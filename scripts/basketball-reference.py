import urllib2

from bs4 import BeautifulSoup

import os
from os import sys, path
import django
import pdb

from datetime import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nba.settings")
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
        'CJ McCollum': 'C.J. McCollum'
    }
    return conv[name] if name in conv else name

def main():
    dp = "https://www.basketball-reference.com/friv/dailyleaders.fcgi"
    response = urllib2.urlopen(dp)
    r = response.read()

    is_new = True
    soup = BeautifulSoup(r, "html.parser")
    # pdb.set_trace()

    try:
        date = soup.find("span", {"class": "button2 current"}).text
        date = datetime.strptime(date, '%b %d, %Y')
        last_game = PlayerGame.objects.all().order_by('-date').first()
        if last_game and last_game.date == date.date():
            is_new = False

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
                name = player.find("td", {"data-stat":"player"}).text.strip()
                name = nameSync(name)
                team = player.find("td", {"data-stat":"team_id"}).text.strip()
                team = teamSync(team)
                opp = player.find("td", {"data-stat":"opp_id"}).text
                opp = teamSync(opp)
                uid = player.find("td", {"data-stat":"player"}).get('data-append-csv')
                player_ = Player.objects.filter(first_name__iexact=name.split(' ')[0],
                                                last_name__iexact=name.split(' ')[1],
                                                team=team)
                # update avatar for possible new players
                avatar = 'https://d2cwpp38twqe55.cloudfront.net/req/201808311/images/players/{}.jpg'.format(uid)
                player_.update(avatar=avatar)

                if is_new:
                    fg3 = int(player.find("td", {"data-stat":"fg3"}).text)
                    fg = int(player.find("td", {"data-stat":"fg"}).text)
                    ft = int(player.find("td", {"data-stat":"ft"}).text)
                    trb = int(player.find("td", {"data-stat":"trb"}).text)
                    ast = int(player.find("td", {"data-stat":"ast"}).text)
                    blk = int(player.find("td", {"data-stat":"blk"}).text)
                    stl = int(player.find("td", {"data-stat":"stl"}).text)
                    tov = int(player.find("td", {"data-stat":"tov"}).text)
                    pts = int(player.find("td", {"data-stat":"pts"}).text)
                    fpts = pts + 1.2 * trb + 1.5 * ast + 3 * blk + 3 *stl - tov

                    obj = PlayerGame.objects.create(
                        name = name,
                        team = team,
                        location = player.find("td", {"data-stat":"game_location"}).text,
                        opp = opp,
                        game_result = player.find("td", {"data-stat":"game_result"}).text,
                        mp = float(mp[0])+float(mp[1])/60,
                        fg = fg,
                        fga = player.find("td", {"data-stat":"fga"}).text,
                        fg_pct = player.find("td", {"data-stat":"fg_pct"}).text or None,
                        fg3 = fg3,
                        fg3a = player.find("td", {"data-stat":"fg3a"}).text,
                        fg3_pct = player.find("td", {"data-stat":"fg3_pct"}).text or None,
                        ft = ft,
                        fta = player.find("td", {"data-stat":"fta"}).text,
                        ft_pct = player.find("td", {"data-stat":"ft_pct"}).text or None,
                        trb = trb,
                        ast = ast,
                        stl = stl,
                        blk = blk,
                        tov = tov,
                        pf = player.find("td", {"data-stat":"pf"}).text,
                        pts = pts,
                        fpts = fpts,
                        date = date
                    )
        except (Exception) as e:
            print (e)
    

if __name__ == "__main__":
    main()
