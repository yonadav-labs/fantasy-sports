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

def get_games(data_source):
    slate = 'Main' if data_source == 'FanDuel' else 'all'
    url = 'https://www.rotowire.com/daily/tables/schedule.php?sport=NBA&' + \
          'site={}&type=main&slate={}'.format(data_source, slate)

    games = requests.get(url).json()
    if games:
        Game.objects.filter(data_source=data_source).delete()

        exclude_fields = ['exclude', 'home_score', 'visit_score', 'home_team_abbr', 
                          'visit_team_abbr', 'weather_icon', 'home_logo', 'visit_logo']
        for ii in games:
            for jj in exclude_fields:
                ii.pop(jj)
            ii['data_source'] = data_source
            ii['date'] = datetime.datetime.strptime(ii['date'].split(' ')[1], '%I:%M%p')
            # date is not used
            ii['date'] = datetime.datetime.combine(datetime.date.today(), ii['date'].time())
            ii['ou'] = float(ii['ou']) if ii['ou'] else 0
            Game.objects.create(**ii)

if __name__ == "__main__":
    for ds in DATA_SOURCE:
        get_games(ds[0])
