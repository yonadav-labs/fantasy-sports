# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import math
import mimetypes
from wsgiref.util import FileWrapper

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.forms.models import model_to_dict

from general.models import *
from general.lineup import *



def players(request):
    players = Player.objects.filter(data_source='FanDuel').order_by('first_name')
    return render(request, 'players.html', locals())

@xframe_options_exempt
def lineup_builder(request):
    data_sources = DATA_SOURCE
    num_lineups = request.session.get('DraftKings_num_lineups', 1)
    return render(request, 'lineup-builder.html', locals())

@xframe_options_exempt
def lineup_optimizer(request):
    data_sources = DATA_SOURCE
    return render(request, 'lineup-optimizer.html', locals())

def _is_full_lineup(lineup, ds):
    if not lineup:
        return False

    num_players = sum([1 for ii in lineup if ii['player']])
    return num_players == ROSTER_SIZE[ds]

@csrf_exempt
def check_mlineups(request):
    ds = request.POST.get('ds')
    num_lineups = request.session.get(ds+'_num_lineups', 1)
    res = []
    for ii in range(1, num_lineups+1):
        key = '{}_lineup_{}'.format(ds, ii)
        lineup = request.session.get(key)
        res.append([ii, 'checked' if _is_full_lineup(lineup, ds) else 'disabled'])
    return JsonResponse(res, safe=False)

@csrf_exempt
def build_lineup(request):
    ds = request.POST.get('ds')
    pid = request.POST.get('pid')
    idx = int(request.POST.get('idx'))

    cus_proj = request.session.get('cus_proj', {})
    request.session['ds'] = ds
    key = '{}_lineup_{}'.format(ds, idx)
    num_lineups = request.session.get(ds+'_num_lineups', 1)
    lineup = request.session.get(key, [{ 'pos':ii, 'player': '' } for ii in CSV_FIELDS[ds]])

    if idx > num_lineups:           # add lineup
        num_lineups = idx
        request.session[ds+'_num_lineups'] = idx
        request.session[key] = lineup

    msg = ''

    if pid == "123456789":          # remove all lineups
        request.session[ds+'_num_lineups'] = 1
        lineup = [{ 'pos':ii, 'player': '' } for ii in CSV_FIELDS[ds]]
        request.session['{}_lineup_{}'.format(ds, 1)] = lineup

        for ii in range(2, num_lineups+1):
            request.session.pop('{}_lineup_{}'.format(ds, ii))
    elif '-' in pid:                # remove a player
        pid = pid.strip('-')
        for ii in lineup:
            if ii['player'] == pid:
                ii['player'] = ''
    elif pid == 'optimize':         # manual optimize
        ids = request.POST.get('ids').split('&')
        ids = [ii[4:] for ii in ids if 'ids=' in ii]

        players = Player.objects.filter(id__in=ids)
        num_lineups = 1
        locked = [int(ii['player']) for ii in lineup if ii['player']]

        _exposure = [{ 'min': 0, 'max': 1, 'id': ii.id } for ii in players]
        lineups = calc_lineups(players, num_lineups, locked, ds, _exposure, cus_proj)

        if lineups:
            roster = lineups[0].get_roster_players()
            lineup = [{ 'pos':ii, 'player': str(roster[idx].id) } for idx, ii in enumerate(CSV_FIELDS[ds])]
            request.session[key] = lineup
        else:
            msg = 'Sorry, something is wrong.'
    elif pid:                       # add a player
        # check whether he is available
        sum_salary = 0
        available = False
        for ii in lineup:
            if ii['player']:
                player = Player.objects.get(id=ii['player'])
                sum_salary += player.salary

        player = Player.objects.get(id=pid)
        if SALARY_CAP[ds] >= sum_salary + player.salary:
            for ii in lineup:
                if not ii['player']:
                    if ii['pos'] == 'UTIL' or ii['pos'] in player.actual_position:
                        available = True
                        ii['player'] = pid
                        break
            if available:
                # save lineup
                request.session[key] = lineup
            else:
                msg = 'He is not applicable to any position.'
        else:
            msg = 'Lineup salary exceeds the salary cap.'

    players = []
    sum_proj = 0
    sum_salary = 0
    num_players = 0
    pids = []

    for ii in lineup:
        player = {}
        if ii['player']:
            # need to take care of old player info
            player = Player.objects.filter(id=ii['player']).first() or {}

        if player:
            pids.append(ii['player'])
            num_players += 1
            sum_salary += player.salary
            sum_proj += float(cus_proj.get(str(player.id), player.proj_points))

        players.append({ 'pos':ii['pos'], 'player': player })

    sum_proj = f'{sum_proj:.2f}'
    rem = (SALARY_CAP[ds] - sum_salary) / (ROSTER_SIZE[ds] - num_players) if ROSTER_SIZE[ds] != num_players else 0
    full = num_players == ROSTER_SIZE[ds]

    result = { 
        'html': render_to_string('lineup-body.html', locals()),
        'pids': pids,
        'msg': msg
    }

    return JsonResponse(result, safe=False)


@csrf_exempt
def get_players(request):
    slate_id = request.POST.get('slate_id')
    slate = Slate.objects.get(pk=slate_id)
    ds = slate.data_source
    order = request.POST.get('order', 'proj_points')
    if order == '-':
        order = 'proj_points'

    teams = request.POST.get('games').strip(';').replace(';', '-').split('-')

    factor = 1 if ds == 'Yahoo' else 1000
    players = []

    cus_proj = request.session.get('cus_proj', {})
    for ii in Player.objects.filter(slate=slate, team__in=teams):
        player = model_to_dict(ii, fields=['id', 'injury', 'avatar', 'salary', 'team',
                                           'actual_position', 'first_name', 'last_name',
                                           'handedness', 'order', 'confirmed', 'opponent'])

        if player['opponent'].startswith('@'):
            player['opponent'] = '@ '+player['opponent'][1:]
        else:
            player['opponent'] = 'vs '+player['opponent']

        player['proj_points'] = float(cus_proj.get(str(ii.id), ii.proj_points))
        player['pt_sal'] = player['proj_points'] * factor / ii.salary if ii.salary else 0
        players.append(player)

    players = sorted(players, key=lambda k: k[order], reverse=True)
    result = { 
        'html': render_to_string('player-list_.html', locals()),
        'num_lineups': request.session.get(ds+'_num_lineups', 1),
    }

    return JsonResponse(result, safe=False)



def _get_lineups(request):
    params = request.POST

    ids = params.getlist('ids')
    locked = params.getlist('locked')
    num_lineups = min(int(params.get('num-lineups', 1)), 150)
    ds = params.get('ds', 'DraftKings')
    exposure = params.get('exposure')

    ids = [int(ii) for ii in ids]
    locked = [int(ii) for ii in locked]

    cus_proj = request.session.get('cus_proj', {})
    players = Player.objects.filter(id__in=ids)

    # get exposure for each valid player
    _exposure = []

    for ii in players:
        if ii.id in locked:
            _exposure.append({ 'min': num_lineups, 'max': num_lineups, 'id': ii.id })
        else:
            _exposure.append({
                'min': int(math.ceil(float(params.get('min_xp_{}'.format(ii.id), 0)) * num_lineups / 100)),
                'max': int(math.floor(float(params.get('max_xp_{}'.format(ii.id), 0)) * num_lineups / 100)),
                'id': ii.id
            })

    # check validity of exposure for minimal
    while True:
        possible_players = 0
        for ii in _exposure:
            possible_players += ii['max']
        if possible_players < ROSTER_SIZE[ds] * num_lineups:
            for ii in _exposure:
                ii['max'] = ii['max'] + 1
        else:
            break

    lineups = calc_lineups(players, num_lineups, locked, ds, _exposure, cus_proj)
    return lineups, players


def get_num_lineups(player, lineups):
    num = 0
    for ii in lineups:
        if ii.is_member(player):
            num = num + 1
    return num


@csrf_exempt
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
    
    rows = [[[str(jj) for jj in ii.get_roster_players()]+[int(ii.spent()), ii.projected()], 'ii.drop']
            for ii in lineups]

    result = {
        'player_stat': render_to_string('player-lineup.html', locals()),
        'preview_lineups': render_to_string('preview-lineups.html', locals())
    }

    return JsonResponse(result, safe=False)


@csrf_exempt
def update_point(request):
    pid = request.POST.get('pid')
    points = request.POST.get('val')

    player = Player.objects.get(id=pid.strip('-'))
    factor = 1 if player.slate.data_source == 'Yahoo' else 1000

    cus_proj = request.session.get('cus_proj', {})
    if '-' in pid:
        del cus_proj[pid[1:]]
        points = player.proj_points
    else:
        cus_proj[pid] = points

    request.session['cus_proj'] = cus_proj

    result = {
        'points': '{:.1f}'.format(float(points)),
        'pt_sal': '{:.1f}'.format(float(points) * factor / player.salary if player.salary else 0)
    }

    return JsonResponse(result, safe=False)


def _get_export_cell(player, ds):
    if ds == 'Yahoo':
        return str(player)
    else:
        return player.rid or str(player) + ' - No ID'


@csrf_exempt
def export_lineups(request):
    lineups, _ = _get_lineups(request)
    ds = request.POST.get('ds')
    csv_fields = CSV_FIELDS[ds]
    path = "/tmp/.fantasy_nba_{}.csv".format(ds.lower())

    with open(path, 'w') as f:
        f.write(','.join(csv_fields)+'\n')
        for ii in lineups:
            f.write(','.join([_get_export_cell(jj, ds) for jj in ii.get_roster_players()])+'\n')
    
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path )
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) )

    return response


@csrf_exempt
def export_manual_lineup(request):
    ds = request.session.get('ds')
    lidx = request.GET.getlist('lidx')
    path = "/tmp/.fantasy_nba_{}.csv".format(ds.lower())
    csv_fields = CSV_FIELDS[ds]

    with open(path, 'w') as f:
        f.write(','.join(csv_fields)+'\n')
        for idx in lidx:
            key = '{}_lineup_{}'.format(ds, idx)
            lineup = request.session.get(key)
            players = [Player.objects.get(id=ii['player']) for ii in lineup]
            f.write(','.join([_get_export_cell(ii, ds) for ii in players])+'\n')
        
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path )
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) )

    return response


@staff_member_required
def load_slate(request, slate_id):
    load_empty_proj = request.GET.get('emtpy')
    slate = Slate.objects.get(pk=slate_id)
    games = Game.objects.filter(slate=slate)

    if load_empty_proj:
        players = Player.objects.filter(slate=slate, proj_points=0)
    else:
        players = Player.objects.filter(slate=slate, proj_points__gt=0)

    last_updated = BaseGame.objects.all().order_by('-updated_at').first().updated_at

    return render(request, 'edit-slate.html', locals())


@staff_member_required
def upload_data(request):
    if request.method == 'GET':
        fd_slates = Slate.objects.filter(data_source="FanDuel").order_by('date')
        dk_slates = Slate.objects.filter(data_source="DraftKings").order_by('date')

        return render(request, 'upload-slate.html', locals())
    else:
        date = request.POST['date']
        slate_name = request.POST['slate']
        data_source = request.POST['data_source']
        slate = get_slate(date, slate_name, data_source)

        err_msg = ''
        try:
            projection_file = request.FILES['projection_file']
            projection_info = parse_projection_csv(projection_file)
            projection_info = [f"{row['name']} @#@{row['fpts'] or 0}" for row in projection_info]
        except Exception:
            err_msg = 'Projection file is invalid'
            return render(request, 'upload-slate.html', locals())

        try:
            players_file = request.FILES['players_file']
            players_info = parse_players_csv(players_file, data_source)
            games = load_games(slate, players_info)
            players = load_players(slate, players_info, projection_info)
        except Exception:
            err_msg = 'Player file is invalid'
            return render(request, 'upload-slate.html', locals())

        last_updated = BaseGame.objects.all().order_by('-updated_at').first().updated_at

        return render(request, 'edit-slate.html', locals())


@staff_member_required
@csrf_exempt
def update_field(request):
    data = request.POST
    model_name = data.get('model')
    id = data.get('id')
    field = data.get('field')
    val = data.get('val') if field != 'confirmed' else data.get('val') == 'true'

    model_cls = apps.get_model('general', model_name)
    model = model_cls.objects.get(pk=id)
    setattr(model, field, val)
    model.save()

    return HttpResponse()


@csrf_exempt
def get_games(request):
    slate_id = request.POST.get('slate_id')
    games = Game.objects.filter(slate_id=slate_id)
    return render(request, 'game-list.html', locals())

@csrf_exempt
def get_slates(request):
    ds = request.POST.get('ds')
    slates = Slate.objects.filter(data_source=ds)
    return render(request, 'slate-list.html', locals())
