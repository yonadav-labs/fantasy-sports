import os
import django
import urllib2

from bs4 import BeautifulSoup
from os import sys, path
from datetime import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_sports.settings")
django.setup()

from general.models import *

def teamSync(team):
    # bball -> roto
    team = team.strip().strip('@')
    conv = {
        'GSW': 'GS',
        'CHO': 'CHA',
        'NOP': 'NO',
        'SAS': 'SA',
        'BRK': 'BKN',
        'NYK': 'NY'
    }
    return conv[team] if team in conv else team

def nameSync(name):
    # bball -> roto
    conv = {
        'Juan Hernangomez': 'Juancho Hernangomez',
    }
    return conv[name] if name in conv else name

def main():
    dp = "https://www.basketball-reference.com/friv/dailyleaders.fcgi"

    response = urllib2.urlopen(dp)
    r = response.read()

    is_new = False # True
    soup = BeautifulSoup(r, "html.parser")

    try:
        date = soup.find("span", {"class": "button2 current"}).text
        date = datetime.strptime(date, '%b %d, %Y')
        # last_game = PlayerGame.objects.all().order_by('-date').first()
        # if last_game and last_game.date == date.date():
        #     is_new = False

        table = soup.find("table", {"id":"stats"})
        player_rows = table.find("tbody")
        players = player_rows.find_all("tr")
    except Exception as e:
        print (e)
        return  # no players

    for player in players:
        try:
            if not player.get('class'): # ignore header
                mp = player.find("td", {"data-stat":"mp"}).text.split(':')
                team = player.find("td", {"data-stat":"team_id"}).text.strip()
                team = teamSync(team)
                opp = player.find("td", {"data-stat":"opp_id"}).text
                opp = teamSync(opp)
                uid = player.find("td", {"data-stat":"player"}).get('data-append-csv')

                name = player.find("td", {"data-stat":"player"}).text.strip()
                first_name, last_name = parse_name(nameSync(name))
                player_ = Player.objects.filter(first_name__iexact=first_name,
                                                last_name__iexact=last_name,
                                                team=team)
                # update avatar for possible new players
                avatar = 'https://d2cwpp38twqe55.cloudfront.net/req/201808311/images/players/{}.jpg'.format(uid)
                player_.update(avatar=avatar)
        except (Exception) as e:
            print (e)
    

if __name__ == "__main__":
    main()
