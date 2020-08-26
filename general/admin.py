# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from general.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'uid', 'position', 'team', 'opponent', 'salary', 'play_today', 
                    'proj_points', 'data_source', 'updated_at', 'created_at', 'avatar']
    search_fields = ['first_name', 'last_name', 'team']
    list_filter = ['team', 'data_source', 'position', 'play_today']
    save_as = True


class PlayerGameAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'location', 'opp', 'game_result', 'mp', 'fg', 'fga', 'fg_pct',
                    'fg3', 'fg3a', 'fg3_pct', 'ft', 'fta', 'ft_pct', 'trb', 'ast', 'stl', 'blk',
                    'tov', 'pf', 'pts', 'fpts', 'date']
    search_fields = ['name', 'team']
    list_filter = ['team', 'opp', 'location', 'game_result']


class GameAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'visit_team', 'ou', 'ml', 'updated_at', 'game_status', 'date', 'data_source']
    search_fields = ['home_team', 'visit_team']
    list_filter = ['game_status', 'data_source']


admin.site.register(Player, PlayerAdmin)
admin.site.register(Game, GameAdmin)
# admin.site.register(PlayerGame, PlayerGameAdmin)
