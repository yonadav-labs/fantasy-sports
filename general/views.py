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


def player_match_up_board(request):
    games = _get_game_today()
    return render(request, 'player-match-up-board.html', locals())


def team_match_up_board(request):
    games = _get_game_today()
    return render(request, 'team-match-up-board.html', locals())


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


def get_team_games(team):
    # get all games for the team last season
    season = current_season()
    q = Q(team=team) & \
        Q(date__range=[datetime.date(season, 10, 1), datetime.date(season+1, 6, 30)])

    return PlayerGame.objects.filter(q)


def get_team_stat(team, loc='@'):
    loc_ = '@' if loc == '' else ''
    # pdb.set_trace()
    season = current_season()
    q = Q(opp=team) & Q(location=loc) & \
        Q(date__range=[datetime.date(season, 10, 1), datetime.date(season+1, 6, 30)])
    a_teams = PlayerGame.objects.filter(q)
    a_teams_ = a_teams.values('date').annotate(trb=Sum('trb'), 
                                               ast=Sum('ast'),
                                               stl=Sum('stl'),
                                               blk=Sum('blk'),
                                               tov=Sum('tov'),
                                               pts=Sum('pts'))

    rpg = a_teams_.aggregate(Avg('trb'))['trb__avg'] or 0
    apg = a_teams_.aggregate(Avg('ast'))['ast__avg'] or 0
    spg = a_teams_.aggregate(Avg('stl'))['stl__avg'] or 0
    bpg = a_teams_.aggregate(Avg('blk'))['blk__avg'] or 0
    tov = a_teams_.aggregate(Avg('tov'))['tov__avg'] or 0
    ppg = a_teams_.aggregate(Avg('pts'))['pts__avg'] or 0

    q = Q(team=team) & Q(location=loc_) & \
        Q(date__range=[datetime.date(season, 10, 1), datetime.date(season+1, 6, 30)])
    s_teams = PlayerGame.objects.filter(q)
    s_teams_ = s_teams.values('date').annotate(trb=Sum('trb'), 
                                               ast=Sum('ast'),
                                               stl=Sum('stl'),
                                               blk=Sum('blk'),
                                               tov=Sum('tov'),
                                               pts=Sum('pts'))

    s_rpg = s_teams_.aggregate(Avg('trb'))['trb__avg'] or 0 
    s_apg = s_teams_.aggregate(Avg('ast'))['ast__avg'] or 0
    s_spg = s_teams_.aggregate(Avg('stl'))['stl__avg'] or 0
    s_bpg = s_teams_.aggregate(Avg('blk'))['blk__avg'] or 0
    s_tov = s_teams_.aggregate(Avg('tov'))['tov__avg'] or 0
    s_ppg = s_teams_.aggregate(Avg('pts'))['pts__avg'] or 0

    res = {
        'team': team,
        'rpg': rpg,
        'apg': apg,
        'spg': spg,
        'bpg': bpg,
        'tov': tov,
        'ppg': ppg,
        'total': rpg+apg+spg+bpg+tov+ppg,
        's_rpg': s_rpg,
        's_apg': s_apg,
        's_spg': s_spg,
        's_bpg': s_bpg,
        's_tov': s_tov,
        's_ppg': s_ppg,
        's_total': s_rpg+s_apg+s_spg+s_bpg+s_tov+s_ppg
    }

    # FPA TM POS
    tm_pos = []
    # for each distinct match
    for ii in a_teams_:
        # players (games) in a match
        players = a_teams.filter(date=ii['date'])

        tm_pos_ = {}
        # for each position
        for pos in POSITION:
            # players in the position of the team
            q = Q(position=pos) & Q(data_source='FanDuel')
            players_ = Player.objects.filter(Q(team=players[0].team) & q)
            players_ = ['{} {}'.format(ip.first_name, ip.last_name) for ip in players_]
            tm_pos_[pos] = players.filter(name__in=players_).aggregate(Sum('fpts'))['fpts__sum'] or 0
        if tm_pos_['PG'] > 0 and tm_pos_['SG'] > 0:
            tm_pos.append(tm_pos_)
        print ii['date'], players[0].team, players[0].opp, players[0].location, tm_pos_
        
    for pos in POSITION:
        res[pos] = sum(ii[pos] for ii in tm_pos) / len(tm_pos) if len(tm_pos) else -1

    print '----------------------------'
    # for FPS TM POS
    tm_pos = []
    # for each distinct match
    for ii in s_teams_:
        # players (games) in a match
        players = s_teams.filter(date=ii['date'])

        tm_pos_ = {}
        # for each position
        for pos in POSITION:
            # players in the position of the team
            q = Q(position=pos) & Q(data_source='FanDuel')
            players_ = Player.objects.filter(Q(team=players[0].team) & q)
            players_ = ['{} {}'.format(ip.first_name, ip.last_name) for ip in players_]
            tm_pos_[pos] = players.filter(name__in=players_).aggregate(Sum('fpts'))['fpts__sum'] or 0
        if tm_pos_['PG'] > 0 and tm_pos_['SG'] > 0:
            tm_pos.append(tm_pos_)
        print ii['date'], players[0].team, players[0].opp, players[0].location, tm_pos_
    print '----------------------------'
    for pos in POSITION:
        res['s_'+pos] = sum(ii[pos] for ii in tm_pos) / len(tm_pos) if len(tm_pos) else -1

    return res


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


def get_team_info(team, loc):
    team_games = get_team_games(team)
    # at most one game a day
    game_results = team_games.values('date', 'game_result').distinct()
    wins = game_results.filter(game_result='W').count()
    losses = game_results.filter(game_result='L').count()

    # get distinct players
    players_ = team_games.values('name', 'team').distinct()

    players = []

    for ii in players_:
        player = get_player(ii['name'], ii['team'])
        if player:
            games = team_games.filter(name=ii['name'], location=loc)
            ampg = games.aggregate(Avg('mp'))['mp__avg']
            afp = games.aggregate(Avg('fpts'))['fpts__avg']

            sfp = [ig.fpts for ig in games.order_by('-date')[:3]]
            sfp = sum(sfp)

            players.append({
                'avatar': player.avatar,
                'id': player.id,
                'uid': player.uid,
                'name': ii['name'],
                'pos': player.position,
                'inj': player.injury,
                'salary': player.salary,
                'gp': games.count(),
                'rpg': games.aggregate(Avg('trb'))['trb__avg'],
                'apg': games.aggregate(Avg('ast'))['ast__avg'],
                'spg': games.aggregate(Avg('stl'))['stl__avg'],
                'bpg': games.aggregate(Avg('blk'))['blk__avg'],
                'ppg': games.aggregate(Avg('pts'))['pts__avg'],
                'tov': games.aggregate(Avg('tov'))['tov__avg'],
                'ampg': ampg,
                'afp': afp,
                'sfp': sfp / 3,
                'val': player.salary / 250 + 10
            })

    return { 
        'players': sorted(players, key=Roster().dict_position_order), 
        'wins': wins,
        'losses': losses,
        'win_percent': wins * 100.0 / (wins + losses) if wins + losses > 0 else 0
    }


def filter_players_fpa(team, min_afp, max_afp):
    try:
        info = json.loads(TMSCache.objects.filter(team=team, type=1).first().body)
        players = []

        for ii in range(len(info['players'])):
            afp = info['players'][ii]['afp']
            if min_afp <= afp <= max_afp:
                players.append(info['players'][ii])
        info['players'] = players
        return info
    except Exception as e:
        return {}

@csrf_exempt
def team_match_up(request):
    min_afp = float(request.POST.get('min_afp'))
    max_afp = float(request.POST.get('max_afp'))

    game = request.POST.get('game')
    game = Game.objects.get(id=game)

    home_stat = TMSCache.objects.filter(team=game.home_team, type=2).first()
    away_stat = TMSCache.objects.filter(team=game.visit_team, type=2).first()

    teams = {
        'home': filter_players_fpa(game.home_team, min_afp, max_afp),
        'home_stat': json.loads(home_stat.body) if home_stat else {},
        'away': filter_players_fpa(game.visit_team, min_afp, max_afp),
        'away_stat': json.loads(away_stat.body) if away_stat else {}
    }

    return HttpResponse(render_to_string('team-board_.html', locals()))


def build_OPR_cache():
    season = current_season()
    opr_info = { '': {}, '@': {} }
    all_teams = [ii['team'] for ii in Player.objects.values('team').distinct()]

    colors = linear_gradient('#90EE90', '#137B13', len(all_teams))['hex']

    for loc in ['', '@']:
        for pos in POSITION:
            pos_opr = []
            for team in all_teams:
                # opponent's games
                q = Q(opp=team) & Q(location=loc) & \
                    Q(date__range=[datetime.date(season, 10, 1), datetime.date(season+1, 6, 30)])
                games = PlayerGame.objects.filter(q)
                opp_teams = [jj['team'] for jj in games.values('team').distinct()]
                # filter with pos
                q = Q(position=pos) & Q(data_source='FanDuel')
                players_ = Player.objects.filter(Q(team__in=opp_teams) & q)
                players_ = ['{} {}'.format(ip.first_name, ip.last_name) for ip in players_]
                games = games.filter(name__in=players_).values('date').annotate(fpts=Sum('fpts'))
                opp = games.aggregate(Avg('fpts'))['fpts__avg'] or 0

                pos_opr.append({ 
                    'team': team, 
                    'opp': opp 
                })
            pos_opr, _ = get_ranking(pos_opr, 'opp', 'opr')
            opr_info[loc][pos] = { 
                                    ii['team']: { 'opp': ii['opp'], 'opr': ii['opr'], 'color': colors[ii['opr']-1] } 
                                    for ii in pos_opr 
                                 }
    TMSCache.objects.create(team='TM_OPR', type=3, body=json.dumps(opr_info))


@csrf_exempt
def player_match_up(request):
    loc = request.POST.get('loc')
    pos = request.POST.get('pos')
    pos = '' if pos == 'All' else pos
    ds = request.POST.get('ds')
    min_afp = float(request.POST.get('min_afp'))
    min_sfp = float(request.POST.get('min_sfp'))
    max_afp = float(request.POST.get('max_afp'))
    max_sfp = float(request.POST.get('max_sfp'))
    games = request.POST.get('games').strip(';').split(';')

    game_info = {}
    teams_ = []
    for game in games:
        teams = game.split('-') # home-away
        game_info[teams[0]] = [teams[1], '', '@']   # vs, loc, loc_
        game_info[teams[1]] = [teams[0], '@', '']

        if loc == '' or loc == 'all':
            teams_.append(teams[0])

        if loc == '@' or loc == 'all':
            teams_.append(teams[1])

    opr_info = json.loads(TMSCache.objects.filter(team='TM_OPR').first().body)

    players = Player.objects.filter(data_source=ds,
                                    play_today=True, 
                                    team__in=teams_) \
                            .order_by('-proj_points')
    players_ = []
    for player in players:
        if pos in player.position:
            games = get_games_(player.id, 'all', '', current_season())
            ampg = games.aggregate(Avg('mp'))['mp__avg']
            smpg = games.filter(location=game_info[player.team][1]).aggregate(Avg('mp'))['mp__avg']
            afp = games.aggregate(Avg('fpts'))['fpts__avg']
            sfp = games.filter(location=game_info[player.team][1]).aggregate(Avg('fpts'))['fpts__avg']

            if min_afp <= afp <= max_afp:
                if min_sfp <= sfp <= max_sfp:
                    vs = game_info[player.team][0]
                    loc = game_info[player.team][1]
                    loc_ = game_info[player.team][2]
                    opr_info_ = opr_info[loc_][player.position][vs]

                    players_.append({
                        'avatar': player.avatar,
                        'id': player.id,
                        'uid': player.uid,
                        'name': '{} {}'.format(player.first_name, player.last_name),
                        'team': player.team,
                        'loc': loc,
                        'vs': vs,
                        'pos': player.position,
                        'inj': player.injury,
                        'salary': player.salary,
                        'ampg': ampg,
                        'smpg': smpg,
                        'mdiff': formated_diff(smpg-ampg),
                        'afp': afp,
                        'sfp': sfp,
                        'pdiff': formated_diff(sfp-afp),
                        'val': player.salary / 250 + 10,
                        'opp': opr_info_['opp'],
                        'opr': opr_info_['opr'],
                        'color': opr_info_['color']
                    })

    groups = { ii: [] for ii in POSITION }
    for ii in players_:
        groups[ii['pos']].append(ii)

    num_oprs = []
    for ii in POSITION:
        if groups[ii]:
            groups[ii], _ = get_ranking(groups[ii], 'sfp', 'ppr', -1)
            groups[ii] = sorted(groups[ii], key=lambda k: -k['opr'])

    players = []
    for ii in POSITION:
        if groups[ii]:
            players += groups[ii] + [{}]

    return HttpResponse(render_to_string('player-board_.html', locals()))


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


def gen_lineups(request):
    lineups, players = _get_lineups(request)
    avg_points = mean([ii.projected() for ii in lineups])

    players_ = [{ 'name': '{} {}'.format(ii.first_name, ii.last_name), 
                  'team': ii.team, 
                  'id': ii.id, 
                  'avatar': ii.avatar, 
                  'lineups': get_num_lineups(ii, lineups)} 
                for ii in players if get_num_lineups(ii, lineups)]
    players_ = sorted(players_, key=lambda k: k['lineups'], reverse=True)
    return HttpResponse(render_to_string('player-lineup.html', locals()))


def export_lineups(request):
    lineups, _ = _get_lineups(request)
    ds = request.POST.get('ds')
    CSV_FIELDS = {
        'FanDuel': ['PG', 'PG', 'SG', 'SG', 'SF', 'SF', 'PF', 'PF', 'C'],
        'DraftKings': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
        'Yahoo': ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL'],
        'Fanball': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F/C', 'UTIL']
    }

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


def build_TMS_cache():
    all_teams = [ii['team'] for ii in PlayerGame.objects.values('team').distinct()]
    stat_home = [get_team_stat(ii, '') for ii in all_teams]
    stat_away = [get_team_stat(ii, '@') for ii in all_teams]

    attrs = stat_home[0].keys()
    for attr in attrs:
        if attr != 'team':
            order = -1 if attr.startswith('s_') else 1
            stat_home, _ = get_ranking(stat_home, attr, attr+'_rank', order)
            stat_away, _ = get_ranking(stat_away, attr, attr+'_rank', order)

    stat_home = { ii['team']: ii for ii in stat_home }
    stat_away = { ii['team']: ii for ii in stat_away }

    team_info = {}
    for game in Game.objects.all():
        team_info[game.home_team] = get_team_info(game.home_team, '')
        team_info[game.visit_team] = get_team_info(game.visit_team, '@')

    TMSCache.objects.all().delete()

    TMSCache.objects.create(team='STAT_HOME', type=3, body=json.dumps(stat_home))
    TMSCache.objects.create(team='STAT_AWAY', type=3, body=json.dumps(stat_away))

    for game in Game.objects.all():
        TMSCache.objects.create(team=game.home_team, type=1, body=json.dumps(team_info[game.home_team]))
        TMSCache.objects.create(team=game.visit_team, type=1, body=json.dumps(team_info[game.visit_team]))
        TMSCache.objects.create(team=game.home_team, type=2, body=json.dumps(stat_home[game.home_team]))
        TMSCache.objects.create(team=game.visit_team, type=2, body=json.dumps(stat_away[game.visit_team]))
