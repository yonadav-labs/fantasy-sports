import random
import datetime
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

def _deviation_projection(val):
    result = float(val) + random.randrange(-20, 20) / 10.0
    return result if result >= 0 else float(val)

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
            defaults['play_today'] = True
            defaults['injury'] = html2text.html2text(ii['injury']).strip()

            player = Player.objects.filter(uid=ii['id'], data_source=data_source)
            if not player.exists():
                defaults['uid'] = ii['id']
                defaults['proj_points'] = _deviation_projection(ii['proj_points'])
                defaults['first_name'] = ii['first_name'].replace('.', '')
                defaults['last_name'] = ii['last_name'].replace('.', '')
    
                Player.objects.create(**defaults)
            else:
                criteria = datetime.datetime.combine(datetime.date.today(), datetime.time(15, 0, 0)) # utc time - 10 am EST
                if player.first().updated_at.replace(tzinfo=None) < criteria:
                    defaults['proj_points'] = _deviation_projection(ii['proj_points'])

                player.update(**defaults)
    except:
        print("*** some thing is wrong ***")

if __name__ == "__main__":
    Player.objects.all().update(play_today=False)
    for ds in DATA_SOURCE:
        get_players(ds[0])
