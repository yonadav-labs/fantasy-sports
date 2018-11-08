import csv

import os
from os import sys, path
import django
import pdb

from datetime import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nba.settings")
django.setup()

from general.models import *

def main():
    with open('NBA 16-17 & 17-18 Season Data.csv', 'r') as f:
        gplayers = csv.DictReader(f)
        for gplayer in gplayers:
            try:
                gplayer['date'] = datetime.strptime(gplayer['date'], '%d/%m/%Y')
                gplayer['fg_pct'] = gplayer['fg_pct'] or None
                gplayer['fg3_pct'] = gplayer['fg3_pct'] or None
                gplayer['ft_pct'] = gplayer['ft_pct'] or None
                PlayerGame.objects.create(**gplayer)
            except Exception as e:
                print e
                pdb.set_trace()


if __name__ == "__main__":
    main()
