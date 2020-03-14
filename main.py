import matplotlib.pyplot as plt
import numpy as np
import requests


def moving_average(a: np.array, n: int = 3) -> np.array:
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


if __name__ == '__main__':
    raw_data = requests.get('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json'
                            '/dpc-covid19-ita-andamento-nazionale.json')
    if raw_data.status_code != 200:
        raise FileNotFoundError('File not found. Check data URL.')

    data = raw_data.json()

    dates = [d['data'][:10] for d in data]
    infected = np.array([d['totale_casi'] for d in data], dtype=np.int32)
    growth_rate = (infected[1:] - infected[:-1]) / infected[:-1]

    avg_growth_rate = moving_average(growth_rate, 5)

    print(f"{dates[-1]} SUMMARY")
    print(f"Total number of infected is {infected[-1]}")
    print(f"Growth rate is {growth_rate[-1]:.2f}")
    print(f"Average growth rate (last 5 days) is {avg_growth_rate[-1]:.2f}")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(15, 15))
    ax1.plot(dates, infected)
    fig.autofmt_xdate()
    ax1.set_xlabel('time')
    ax1.set_ylabel('infected')
    ax1.set_title('infected over time')

    ax2.plot(dates, infected)
    ax2.set_yscale('log')
    ax2.set_xlabel('time')
    ax2.set_ylabel('infected (log scale)')
    ax2.set_title('infected over time\n(log scale)')

    ax3.plot(dates[1:], growth_rate)
    ax3.set_xlabel('time')
    ax3.set_ylabel('growth rate')
    ax3.set_title('growth rate over time')

    ax4.plot(dates[5:], avg_growth_rate)
    ax4.set_xlabel('time')
    ax4.set_ylabel('average growth rate')
    ax4.set_title('average (last 5 days) growth rate over time')
    plt.show()
