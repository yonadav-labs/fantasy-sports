import os
import datetime

from os import sys, path

import requests
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_mlb.settings")
django.setup()

from general.models import BaseGame
from general.constants import DATA_SOURCE
from general import html2text
from scripts.roto_slate import get_slate


def fetch_games(data_source, data_source_id):
    slate_id = get_slate(data_source)
    url = 'https://www.rotowire.com/daily/tables/mlb/schedule.php' + \
          '?siteID={}&slateID={}'.format(data_source_id, slate_id)
    print (url)

    games = requests.get(url).json()
    if not games:
        return

    BaseGame.objects.filter(data_source=data_source).delete()

    for game in games:
        defaults = {
            'data_source': data_source,
            'home_team': game['home_team'],
            'visit_team': game['visit_team'],
            'home_score': html2text.html2text(game['home_score']).strip(),
            'visit_score': html2text.html2text(game['visit_score']).strip(),
            'time': datetime.datetime.strptime(game['date'][5:], '%I:%M %p'),
            'ou': float(game['ou']) if game['ou'] else 0,
            'ml': str(game['ml']).replace(',', ''),
        }

        # in case there are duplicates
        BaseGame.objects.update_or_create(home_team=game['home_team'],
                                          visit_team=game['visit_team'],
                                          data_source=data_source,
                                          defaults=defaults)


if __name__ == "__main__":
    for id, ds in enumerate(DATA_SOURCE, 1):
        fetch_games(ds[0], id)
