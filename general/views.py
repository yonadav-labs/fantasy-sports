# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json
import mimetypes
import datetime
from wsgiref.util import FileWrapper
import pdb

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Q, Sum

from general.models import *
from general.lineup import *
from general.color import *

POSITION = ['PG', 'SG', 'SF', 'PF', 'C']


def _get_game_today():
    return Game.objects.all()


def players(request):
    players = Player.objects.filter(data_source='FanDuel').order_by('first_name')
    return render(request, 'players.html', locals())


def lineup_builder(request):
    data_sources = DATA_SOURCE
    games = _get_game_today()
    return render(request, 'lineup-builder.html', locals())


def lineup(request):
    data_sources = DATA_SOURCE
    games = _get_game_today()
    return render(request, 'lineup.html', locals())


@csrf_exempt
def fav_player(request):
    uid = request.POST.get('uid')
    if uid:
        if uid == "-1":
            FavPlayer.objects.all().delete()
        else:
            player = Player.objects.filter(uid=uid).first()
            if FavPlayer.objects.filter(player=player).exists():
                FavPlayer.objects.filter(player=player).delete()
            else:
                FavPlayer.objects.create(player=player)

    players = [ii for ii in FavPlayer.objects.all()]
    players = sorted(players, key=Roster().fav_position_order)

    return HttpResponse(render_to_string('fav-body.html', locals()))


@csrf_exempt
def get_players(request):
    ds = request.POST.get('ds')
    teams = request.POST.get('games').strip(';').replace(';', '-').split('-')
    players = Player.objects.filter(data_source=ds, 
                                    team__in=teams,
                                    play_today=True) \
                            .order_by('-proj_points')
    return HttpResponse(render_to_string('player-list_.html', locals()))


def get_games_(pid, loc, opp, season):
    player = Player.objects.get(id=pid)
    q = Q(name='{} {}'.format(player.first_name, player.last_name)) \
      & Q(team=player.team) \
      & Q(date__range=[datetime.date(season, 10, 1), datetime.date(season+1, 6, 30)])

    if opp:
        q &= Q(opp=opp)
    if loc != 'all':
        q &= Q(location=loc)

    return PlayerGame.objects.filter(q).order_by('-date')


def current_season():
    today = datetime.date.today()
    return today.year if today > datetime.date(today.year, 10, 17) else today.year - 1


def player_detail(request, pid):
    player = Player.objects.get(id=pid)
    year = current_season()
    games = get_games_(pid, 'all', '', year)
    avg_min = games.aggregate(Avg('mp'))
    avg_fpts = games.aggregate(Avg('fpts'))

    return render(request, 'player_detail.html', locals())


def formated_diff(val):
    fm = '{:.1f}' if val > 0 else '({:.1f})'
    return fm.format(abs(val))


def get_ranking(players, sattr, dattr, order=1):
    # order = 1: ascending, -1: descending
    players = sorted(players, key=lambda k: k[sattr]*order)
    ranking = 0
    prev_val = None
    for ii in players:
        if ii[sattr] != prev_val:
            prev_val = ii[sattr]
            ranking += 1
        ii[dattr] = ranking
    return players, ranking


def get_player(full_name, team):
    '''
    FanDuel has top priority
    '''
    names = full_name.split(' ')
    players = Player.objects.filter(first_name=names[0], last_name=names[1], team=team) \
                            .order_by('data_source')
    player = players.filter(data_source='FanDuel').first()
    if not player:
        player = players.first()
    return player


@csrf_exempt
def player_games(request):
    pid = request.POST.get('pid')
    loc = request.POST.get('loc')
    opp = request.POST.get('opp')
    season = int(request.POST.get('season'))

    games = get_games_(pid, loc, opp, season)

    opps = '<option value="">All</option>'
    for ii in sorted(set(games.values_list('opp', flat=True).distinct())):
        opps += '<option>{}</option>'.format(ii)

    result = {
        'game_table': render_to_string('game-list_.html', locals()),
        'chart': [[ii.date.strftime('%Y/%m/%d'), ii.fpts] for ii in games],
        'opps': opps
    }

    return JsonResponse(result, safe=False)


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def _get_lineups(request):
    ids = request.POST.getlist('ids')
    locked = request.POST.getlist('locked')
    num_lineups = int(request.POST.get('num-lineups'))
    ds = request.POST.get('ds')

    ids = [int(ii) for ii in ids]
    locked = [int(ii) for ii in locked]

    players = Player.objects.filter(id__in=ids)
    lineups = calc_lineups(players, num_lineups, locked, ds)
    return lineups, players


def get_num_lineups(player, lineups):
    num = 0
    for ii in lineups:
        if ii.is_member(player):
            num = num + 1
    return num


CSV_FIELDS = {
    'FanDuel': ['PG', 'PG', 'SG', 'SG', 'SF', 'SF', 'PF', 'PF', 'C'],
    'DraftKings': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
    'Yahoo': ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL'],
    'Fanball': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F/C', 'UTIL']
}


def gen_lineups(request):
    lineups, players = _get_lineups(request)
    avg_points = mean([ii.projected() for ii in lineups])

    players_ = [{ 'name': '{} {}'.format(ii.first_name, ii.last_name), 
                  'team': ii.team, 
                  'position': ii.actual_position,
                  'id': ii.id, 
                  'avatar': ii.avatar, 
                  'lineups': get_num_lineups(ii, lineups)} 
                for ii in players if get_num_lineups(ii, lineups)]
    players_ = sorted(players_, key=lambda k: k['lineups'], reverse=True)

    ds = request.POST.get('ds')
    header = CSV_FIELDS[ds] + ['Spent', 'Projected']
    
    rows = [ii.get_csv(ds).strip().split(',')+[ii.spent(), ii.projected()]
            for ii in lineups]

    result = {
        'player_stat': render_to_string('player-lineup.html', locals()),
        'preview_lineups': render_to_string('preview-lineups.html', locals())
    }

    return JsonResponse(result, safe=False)


def export_lineups(request):
    lineups, _ = _get_lineups(request)
    ds = request.POST.get('ds')
    csv_fields = CSV_FIELDS[ds]
    path = "/tmp/.fantasy_nba_{}.csv".format(ds.lower())

    with open(path, 'w') as f:
        f.write(','.join(csv_fields)+'\n')
        for ii in lineups:
            f.write(ii.get_csv(ds))
    
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path ) # not FileField instance
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) ) # same here        
    return response


@csrf_exempt
def update_point(request):
    pid = int(request.POST.get('pid'))
    points = request.POST.get('val')
    Player.objects.filter(id=pid).update(proj_points=points)
    return HttpResponse('')
