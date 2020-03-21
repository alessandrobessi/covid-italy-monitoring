import json
import math
import pathlib
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import requests
import scipy.optimize


def moving_average(a: np.array, n: int = 3) -> np.array:
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


def logistic(x: np.array, a: float, b: float, c: float) -> np.array:
    return c / (1 + np.exp(-(x - b) / a))


if __name__ == '__main__':
    raw_data = requests.get('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json'
                            '/dpc-covid19-ita-andamento-nazionale.json')
    if raw_data.status_code != 200:
        raise FileNotFoundError('File not found. Check data URL.')
    try:
        data = raw_data.json()
    except json.decoder.JSONDecodeError:
        decoded_data = raw_data.content.decode('utf-8-sig')
        data = json.loads(decoded_data)

    dates = [datetime.strptime(d['data'][:10], '%Y-%m-%d') for d in data]
    infected_list = [d['totale_casi'] for d in data]
    recovered = np.array([d['dimessi_guariti'] for d in data], dtype=np.int32)
    dead = np.array([d['deceduti'] for d in data], dtype=np.int32)
    hospitalized = np.array([d['ricoverati_con_sintomi'] for d in data], dtype=np.int32)
    icus = np.array([d['terapia_intensiva'] for d in data], dtype=np.int32)
    isolated = np.array([d['isolamento_domiciliare'] for d in data], dtype=np.int32)
    currently_infected = np.array([d['totale_attualmente_positivi'] for d in data], dtype=np.int32)
    tested = np.array([d['tamponi'] for d in data], dtype=np.int32)

    infected = np.array(infected_list, dtype=np.int32)
    new_infected = infected[-1] - infected[-2]
    growth_rate = (infected[1:] - infected[:-1]) / infected[:-1]
    avg_growth_rate = moving_average(growth_rate, 5)

    # x = (1 + growth_rate)^t
    # log(x) = t * log(1 + growth_rate)
    # t = log(x) / log(1 + growth_rate)
    time_to_2x = math.log(2) / math.log(1 + growth_rate[-1])
    time_to_10x = math.log(10) / math.log(1 + growth_rate[-1])

    dates_forecast = dates.copy()

    days_ahead = 30

    for i in range(days_ahead):
        dates_forecast.append(dates_forecast[-1] + timedelta(days=1))

    x = np.array(np.linspace(1, len(infected), len(infected), dtype=np.float))
    xx = np.array(np.linspace(x[0], x[-1] + days_ahead, len(x) + days_ahead), dtype=np.float)

    # logistic fit infected
    popt, pcov = scipy.optimize.curve_fit(logistic, x, infected,
                                          p0=[2, 25, 1000],
                                          maxfev=1000)
    logistic_infected_forecast = logistic(xx, *popt)
    errors = np.sqrt(np.diag(pcov))
    fit_up = popt + errors
    fit_dw = popt - errors
    logistic_infected_fit_up_p = logistic(xx, *fit_up)
    logistic_infected_fit_dw_p = logistic(xx, *fit_dw)

    # logistic fit dead
    popt, pcov = scipy.optimize.curve_fit(logistic, x, dead,
                                          p0=[2, 25, 1000],
                                          maxfev=1000)
    logistic_dead_forecast = logistic(xx, *popt)
    errors = np.sqrt(np.diag(pcov))
    fit_up = popt + errors
    fit_dw = popt - errors
    logistic_dead_fit_up_p = logistic(xx, *fit_up)
    logistic_dead_fit_dw_p = logistic(xx, *fit_dw)

    with open(pathlib.Path() / 'report' / 'report.md', 'w') as f:
        f.write("<div align='center'>\n\n")
        f.write(f"# {str(dates[-1])[:10]}\n")
        f.write("CoVid-19 Italy Monitoring\n")
        f.write("</div>\n")
        f.write("\n")
        f.write(f"##### Total number of infected individuals is {infected[-1]} (+{new_infected})\n")
        f.write("Infected | Recovered | Dead\n")
        f.write(":---: | :---: | :---:\n")
        f.write(f"*{currently_infected[-1]}* | *{recovered[-1]}* | *{dead[-1]}*\n")
        f.write(f"*(+{currently_infected[-1] - currently_infected[-2]}*) | *"
                f"(+{recovered[-1] - recovered[-2]}*) | "
                f"(*+{dead[-1] - dead[-2]}*)\n")
        f.write(f"\n*Total number of tested individuals is {tested[-1]} (+"
                f"{tested[-1] - tested[-2]})*\n")
        f.write("***\n")
        f.write(
            f"##### Current number of infected individuals is {currently_infected[-1]} (+{currently_infected[-1] - currently_infected[-2]})\n")
        f.write("hospitalized | in ICU | home isolation\n")
        f.write(":---: | :---: | :---:\n")
        f.write(f"*{hospitalized[-1]}* |")
        f.write(f"*{icus[-1]}* |")
        f.write(f"*{isolated[-1]}*\n")
        f.write(f"*(+{hospitalized[-1] - hospitalized[-2]}*) |")
        f.write(f"*(+{icus[-1] - icus[-2]}*) |")
        f.write(f"*(+{isolated[-1] - isolated[-2]}*)\n")
        f.write("***\n")
        f.write(f"##### Growth rate is {growth_rate[-1]:.2f} (5 days smoothing is"
                f" {avg_growth_rate[-1]:.2f})\n")
        f.write(f"- *time to 2x* is {time_to_2x:.2f} days\n")
        f.write(f"- *time to 10x* is {time_to_10x:.2f} days\n")
        f.write("![stats][stats]\n")
        f.write("\n")
        f.write(f"##### Logistic fit infected forecast\n")
        f.write("after 3 days | after 5 days | after 10 days | after 20 days | after 30 days\n")
        f.write(":---: | :---: | :---: | :---: | :---:\n")
        f.write(f"*{int(logistic_infected_forecast[-28])}* |")
        f.write(f"*{int(logistic_infected_forecast[-26])}* |")
        f.write(f"*{int(logistic_infected_forecast[-21])}* |")
        f.write(f"*{int(logistic_infected_forecast[-11])}* |")
        f.write(f"*{int(logistic_infected_forecast[-1])}*\n")
        f.write("\n")
        f.write("\n![logistic_infected][logistic_infected]\n")
        f.write("\n")
        f.write(f"##### Logistic fit dead forecast\n")
        f.write("after 3 days | after 5 days | after 10 days | after 20 days | after 30 days\n")
        f.write(":---: | :---: | :---: | :---: | :---:\n")
        f.write(f"*{int(logistic_dead_forecast[-28])}* |")
        f.write(f"*{int(logistic_dead_forecast[-26])}* |")
        f.write(f"*{int(logistic_dead_forecast[-21])}* |")
        f.write(f"*{int(logistic_dead_forecast[-11])}* |")
        f.write(f"*{int(logistic_dead_forecast[-1])}*\n")
        f.write("\n")
        f.write("\n![logistic_dead][logistic_dead]\n")
        f.write("\n")
        f.write("[stats]: stats.png\n")
        f.write("[logistic_infected]: logistic_infected.png\n")
        f.write("[logistic_dead]: logistic_dead.png\n")

    plt.rc('lines', linewidth=3, markersize=8)
    plt.rc('font', size=12)

    with plt.xkcd():
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=(15, 15))
        fig.autofmt_xdate()

        ax1.stackplot(dates, dead, recovered, currently_infected,
                      labels=['dead', 'recovered', 'infected'])
        ax1.legend(loc='upper left')

        ax2.plot(dates, infected, 'o-', label='total infected')
        ax2.legend(loc='upper left')

        ax3.plot(dates, infected, 'o-', label='total infected\nin log scale')
        ax3.set_yscale('log')
        ax3.legend(loc='upper left')

        ax4.plot(dates[1:], growth_rate, 'o-', label='growth rate')
        ax4.plot(dates[5:], avg_growth_rate, label='5 days smoothing')
        ax4.legend(loc='upper right')

        ax5.stackplot(dates, icus, hospitalized, isolated,
                      labels=['in ICU', 'hospitalized', 'home isolation'])
        ax5.legend(loc='upper left')

        ax6.plot(dates, tested, 'o-', label='total tested')
        ax6.legend(loc='upper left')

        plt.savefig('report/stats.png')

    with plt.xkcd():
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 15))
        fig.autofmt_xdate()
        ax.plot(dates, infected, 'o-', label='total infected')
        ax.plot(dates_forecast, logistic_infected_forecast, label='logistic forecast')
        ax.legend(loc='upper left')
        ax.fill_between(dates_forecast, logistic_infected_fit_up_p, logistic_infected_fit_dw_p,
                        alpha=.25, color='gray')
        plt.savefig('report/logistic_infected.png')

    with plt.xkcd():
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 15))
        fig.autofmt_xdate()
        ax.plot(dates, dead, 'o-', label='total dead')
        ax.plot(dates_forecast, logistic_dead_forecast, label='logistic forecast')
        ax.legend(loc='upper left')
        ax.fill_between(dates_forecast, logistic_dead_fit_up_p, logistic_dead_fit_dw_p,
                        alpha=.25, color='gray')
        plt.savefig('report/logistic_dead.png')

    # regional analysis
    raw_data = requests.get(
        'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-regioni.json')
    if raw_data.status_code != 200:
        raise FileNotFoundError('File not found. Check data URL.')
    try:
        data = raw_data.json()
    except json.decoder.JSONDecodeError:
        decoded_data = raw_data.content.decode('utf-8-sig')
        data = json.loads(decoded_data)

    regions = list(set([d['denominazione_regione'] for d in data]))
    for region in regions:
        region_data = [d for d in data if d['denominazione_regione'] == region]
        dates = [datetime.strptime(d['data'][:10], '%Y-%m-%d') for d in region_data]
        infected_list = [d['totale_casi'] for d in region_data]
        recovered = np.array([d['dimessi_guariti'] for d in region_data], dtype=np.int32)
        dead = np.array([d['deceduti'] for d in region_data], dtype=np.int32)
        hospitalized = np.array([d['ricoverati_con_sintomi'] for d in region_data], dtype=np.int32)
        icus = np.array([d['terapia_intensiva'] for d in region_data], dtype=np.int32)
        isolated = np.array([d['isolamento_domiciliare'] for d in region_data], dtype=np.int32)
        currently_infected = np.array([d['totale_attualmente_positivi'] for d in region_data],
                                      dtype=np.int32)
        tested = np.array([d['tamponi'] for d in region_data], dtype=np.int32)

        infected = np.array(infected_list, dtype=np.float32)
        new_infected = infected[-1] - infected[-2]

        infected[infected < 1e-3] = 1e-3
        growth_rate = (infected[1:] - infected[:-1]) / infected[:-1]
        growth_rate[growth_rate < 1e-3] = 1e-2

        avg_growth_rate = moving_average(growth_rate, 5)

        time_to_2x = math.log(2) / math.log(1 + growth_rate[-1])
        time_to_10x = math.log(10) / math.log(1 + growth_rate[-1])

        with open(pathlib.Path() / 'report' / 'regions' / f'report_{region.replace(" ", "")}.md',
                  'w') as f:
            f.write("<div align='center'>\n\n")
            f.write(f"# {str(dates[-1])[:10]}\n")
            f.write(f"CoVid-19 {region} Monitoring\n")
            f.write("</div>\n")
            f.write("\n")
            f.write(
                f"##### Total number of infected individuals is {int(infected[-1])} ("
                f"+{int(new_infected)})\n")
            f.write("Infected | Recovered | Dead\n")
            f.write(":---: | :---: | :---:\n")
            f.write(f"*{currently_infected[-1]}* | *{recovered[-1]}* | *{dead[-1]}*\n")
            f.write(f"*(+{currently_infected[-1] - currently_infected[-2]}*) | *"
                    f"(+{recovered[-1] - recovered[-2]}*) | "
                    f"(*+{dead[-1] - dead[-2]}*)\n")
            f.write(f"\n*Total number of tested individuals is {tested[-1]} (+"
                    f"{tested[-1] - tested[-2]})*\n")
            f.write("***\n")
            f.write(
                f"##### Current number of infected individuals is {currently_infected[-1]} (+{currently_infected[-1] - currently_infected[-2]})\n")
            f.write("hospitalized | in ICU | home isolation\n")
            f.write(":---: | :---: | :---:\n")
            f.write(f"*{hospitalized[-1]}* |")
            f.write(f"*{icus[-1]}* |")
            f.write(f"*{isolated[-1]}*\n")
            f.write(f"*(+{hospitalized[-1] - hospitalized[-2]}*) |")
            f.write(f"*(+{icus[-1] - icus[-2]}*) |")
            f.write(f"*(+{isolated[-1] - isolated[-2]}*)\n")
            f.write("***\n")
            f.write(f"##### Growth rate is {growth_rate[-1]:.2f} (5 days smoothing is"
                    f" {avg_growth_rate[-1]:.2f})\n")
            f.write(f"- *time to 2x* is {time_to_2x:.2f} days\n")
            f.write(f"- *time to 10x* is {time_to_10x:.2f} days\n")
            f.write("![stats][stats]\n")
            f.write("\n")
            f.write(f"[stats]: stats_{region.replace(' ', '')}.png\n")

        with plt.xkcd():
            fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3,
                                                                   figsize=(15, 15))
            fig.autofmt_xdate()

            ax1.stackplot(dates, dead, recovered, currently_infected,
                          labels=['dead', 'recovered', 'infected'])
            ax1.legend(loc='upper left')

            ax2.plot(dates, infected, 'o-', label='total infected')
            ax2.legend(loc='upper left')

            ax3.plot(dates, infected, 'o-', label='total infected\nin log scale')
            ax3.set_yscale('log')
            ax3.legend(loc='upper left')

            ax4.plot(dates[1:], growth_rate, 'o-', label='growth rate')
            ax4.plot(dates[5:], avg_growth_rate, label='5 days smoothing')
            ax4.set_ylim(0, 0.5)
            ax4.legend(loc='upper left')

            ax5.stackplot(dates, icus, hospitalized, isolated,
                          labels=['in ICU', 'hospitalized', 'home isolation'])
            ax5.legend(loc='upper left')

            ax6.plot(dates, tested, 'o-', label='total tested')
            ax6.legend(loc='upper left')

            plt.savefig(f'report/regions/stats_{region.replace(" ", "")}.png')
