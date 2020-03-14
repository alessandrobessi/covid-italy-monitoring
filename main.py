import requests

if __name__ == '__main__':
    raw_data = requests.get('https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json'
                            '/dpc-covid19-ita-andamento-nazionale.json')
    if raw_data.status_code != 200:
        raise FileNotFoundError('File not found. Check data URL.')

    data = raw_data.json()
