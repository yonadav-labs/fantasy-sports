import os

from os import sys, path

import django
import requests

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_mlb.settings")
django.setup()

from general.models import BasePlayer
from general import html2text
from scripts.roto_slate import get_slate


def fetch_players(data_source, data_source_id):
    try:
        slate_id = get_slate(data_source)
        url = 'https://www.rotowire.com/daily/tables/optimizer-mlb.php' + \
              '?siteID={}&slateID={}&projSource=RotoWire&rst=RotoWire'.format(data_source_id, slate_id)

        print(url)
        players = requests.get(url).json()

        print(data_source, len(players))
        if len(players) < 20:
            return

        for player in players:
            defaults = {
                'data_source': data_source,
                'uid': player['id'],
                'first_name': player['first_name'],
                'last_name': player['last_name'],
                'team': player['team'],
                'opp_pitcher_id': player['opp_pitcher_id'],
                'order': '' if player['lineup_status'] == 'Yes' else player['lineup_status'],
                'handedness': html2text.html2text(player['handedness']).strip().replace('B', 'S'),
                'confirmed': player['team_lineup_status'] == '' and player['lineup_status'] != '',
            }

            BasePlayer.objects.update_or_create(uid=player['id'],
                                                data_source=data_source,
                                                defaults=defaults)
    except:
        print("*** some thing is wrong ***")


if __name__ == "__main__":
    for id, ds in enumerate(['DraftKings', 'FanDuel'], 1):
        fetch_players(ds, id)
