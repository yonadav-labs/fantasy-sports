import urllib2

from bs4 import BeautifulSoup

def get_slate(ds):
    slate = 'all'
    try:
        url = 'https://www.rotowire.com/daily/nba/optimizer.php?site={}'.format(ds)
        response = urllib2.urlopen(url)
        r = response.read()

        soup = BeautifulSoup(r, "html.parser")
        body = soup.find('body')
        slate = body['data-slate']
    except:
        pass

    return slate
