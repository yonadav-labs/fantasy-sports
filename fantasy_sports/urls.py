"""fantasy_sports URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from general.views import *

admin.site.site_header = "Fantasy NBA"

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'^$', players, name="players"),
    url(r'^$', lineup, name="lineup"),
    # url(r'^lineup$', lineup, name="lineup"),
    url(r'^fav-player$', fav_player, name="fav_player"),
    url(r'^players/(?P<pid>\d+)$', player_detail, name="player_detail"),
    url(r'^gen-lineups', gen_lineups, name="gen_lineups"),
    url(r'^get-players', get_players, name="get_players"),
    url(r'^export_lineups', export_lineups, name="export_lineups"),
    url(r'^update-point', update_point, name="update_point"),
    url(r'^player-games', player_games, name="player_games"),
    url(r'^player-match-up-board', player_match_up_board, name="player_match_up_board"),
    url(r'^player-match-up', player_match_up, name="player_match_up"),
    url(r'^team-match-up-board', team_match_up_board, name="team_match_up_board"),
    url(r'^team-match-up', team_match_up, name="team_match_up"),
]
