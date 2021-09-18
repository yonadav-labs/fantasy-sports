import requests

from bs4 import BeautifulSoup


def get_slate(ds):
    try:
        url = 'https://www.rotowire.com/daily/nba/optimizer.php?site={}'.format(ds)
        r = requests.get(url).text

        soup = BeautifulSoup(r, "html.parser")
        body = soup.find('body')
        slate_id = body['data-slateid']
    except:
        slate_id = ''

    return slate_id
