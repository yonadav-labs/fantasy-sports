import random
import requests

import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_sports.settings")
django.setup()

from general.models import *
from general import html2text
import pdb

def get_players(data_source):
    try:
        url = 'https://www.rotowire.com/daily/tables/optimizer-nba.php?sport=NBA&' + \
              'site={}&projections=&type=main&slate=all'.format(data_source)

        players = requests.get(url).json()

        fields = ['minutes', 'money_line', 
                  'over_under', 'point_spread', 'position', 'proj_ceiling', 'opponent',
                  'proj_custom', 'proj_floor', 'proj_original', 'proj_rotowire', 
                  'proj_site', 'proj_third_party_one', 'proj_third_party_two', 'actual_position', 
                  'salary', 'salary_custom', 'salary_original', 'team', 'team_points', 'value'] # 'proj_points'
        print data_source, len(players)
        for ii in players:
            defaults = { key: str(ii[key]).replace(',', '') for key in fields }
            defaults['proj_points'] = float(ii['proj_points']) + random.randrange(-20, 20) / 10.0
            if defaults['proj_points'] <= 0:
                defaults['proj_points'] = float(ii['proj_points'])
            defaults['play_today'] = True
            defaults['injury'] = html2text.html2text(ii['injury']).strip()
            defaults['first_name'] = ii['first_name'].replace('.', '')
            defaults['last_name'] = ii['last_name'].replace('.', '')

            obj = Player.objects.update_or_create(uid=ii['id'], data_source=data_source,
                                                  defaults=defaults)
    except:
        print("*** some thing is wrong ***")

if __name__ == "__main__":
    Player.objects.all().update(play_today=False)
    for ds in DATA_SOURCE:
        get_players(ds[0])
