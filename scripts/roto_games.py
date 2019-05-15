import requests
import datetime

import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_sports.settings")
django.setup()

from general.models import *
from general.views import *
from general import html2text
from scripts.get_slate import get_slate


def get_games(data_source):
    slate = get_slate(data_source)
    url = 'https://www.rotowire.com/daily/tables/schedule.php?sport=NBA&' + \
          'site={}&type=main&slate={}'.format(data_source, slate)
    print (url)
    games = requests.get(url).json()

    if games:
        Game.objects.filter(data_source=data_source).delete()

        fields = ['game_status', 'ml', 'home_team', 'visit_team']
        for ii in games:
            defaults = { key: str(ii[key]).replace(',', '') for key in fields }
            defaults['date'] = datetime.datetime.strptime(ii['date'].split(' ')[1], '%I:%M%p')
            # date is not used
            defaults['date'] = datetime.datetime.combine(datetime.date.today(), defaults['date'].time())
            defaults['ou'] = float(ii['ou']) if ii['ou'] else 0
            defaults['data_source'] = data_source
            defaults['home_score'] = html2text.html2text(ii['home_score']).strip()
            defaults['visit_score'] = html2text.html2text(ii['visit_score']).strip()
            Game.objects.create(**defaults)


if __name__ == "__main__":
    for ds in DATA_SOURCE:
        get_games(ds[0])
