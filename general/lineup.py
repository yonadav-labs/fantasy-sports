from ortools.linear_solver import pywraplp

from .models import *
from .constants import POSITION_LIMITS, ROSTER_SIZE, TEAM_LIMIT, TEAM_MEMEBER_LIMIT, SALARY_CAP


class Roster:
    POSITION_ORDER = {
        "PG": 0,
        "SG": 1,
        "SF": 2,
        "PF": 3,
        "C": 4
    }

    def __init__(self, ds):
        self.players = []
        self.ds = ds
        self.drop = None

    def add_player(self, player):
        self.players.append(player)

    def is_member(self, player):
        return player in self.players

    def get_num_teams(self):
        teams = set([ii.team for ii in self.players])
        return len(teams)

    def spent(self):
        return sum(map(lambda x: x.salary, self.players))

    def projected(self, gross=True):
        lst = map(lambda x: x.proj_points, self.players)
        res = sum(lst)
        if self.ds == 'FanDuel' and not gross:
            drop = min(lst)
            for ii in self.players:
                if ii.proj_points == drop:
                    self.drop = str(ii)
                    break
            res = res - drop
        return res

    def position_order(self, player):
        return self.POSITION_ORDER[player.position]

    def sorted_players(self):
        return sorted(self.players, key=self.position_order)

    def get_roster_players(self):
        if self.ds == 'FanDuel': 
            return self.sorted_players()
        else:
            pos = {
                'DraftKings': ['PG', 'SG', 'SF', 'PF', 'C', 'PG,SG', 'SF,PF'],
                'Yahoo': ['PG', 'SG', 'PG,SG', 'SF', 'PF', 'SF,PF', 'C'],
            }
            pos = pos[self.ds]
            players = list(self.players)
            players_ = []

            for ii in pos:
                for jj in players:
                    if jj.position in ii:
                        players_.append(jj)
                        players.remove(jj)
                        break
            players_.append(players[0])
            return players_

    def __repr__(self):
        s = '\n'.join(str(x) for x in self.sorted_players())
        s += "\n\nProjected Score: %s" % self.projected()
        s += "\tCost: $%s" % self.spent()
        return s


def get_lineup(ds, players, teams, locked, ban, max_point, con_mul):
    solver = pywraplp.Solver('nba-lineup', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    variables = []

    for i, player in enumerate(players):
        if player.id in locked and ds == 'impossible':  # != 'DraftKings':
            variables.append(solver.IntVar(1, 1, str(player)+str(i)))
        elif player.id in ban:
            variables.append(solver.IntVar(0, 0, str(player)+str(i)))
        else:
            variables.append(solver.IntVar(0, 1, str(player)+str(i)))

    objective = solver.Objective()
    objective.SetMaximization()

    for i, player in enumerate(players):
        objective.SetCoefficient(variables[i], player.proj_points)

    salary_cap = solver.Constraint(0, SALARY_CAP[ds])
    for i, player in enumerate(players):
        salary_cap.SetCoefficient(variables[i], player.salary)

    point_cap = solver.Constraint(0, max_point)
    for i, player in enumerate(players):
        point_cap.SetCoefficient(variables[i], player.proj_points)

    position_limits = POSITION_LIMITS[ds]
    for position, min_limit, max_limit in position_limits:
        position_cap = solver.Constraint(min_limit, max_limit)

        for i, player in enumerate(players):
            if player.position in position:
                position_cap.SetCoefficient(variables[i], 1)

    # no more than n players from one team (yahoo, fanduel)
    if TEAM_MEMEBER_LIMIT[ds] != ROSTER_SIZE[ds]:
        for team in teams:
            team_cap = solver.Constraint(0, TEAM_MEMEBER_LIMIT[ds])
            for i, player in enumerate(players):
                if team == player.team:
                    team_cap.SetCoefficient(variables[i], 1)

    if ds:  # == 'DraftKings':    # multi positional constraints
        for ii in con_mul:
            if players[ii[0]].id in locked:
                mul_pos_cap = solver.Constraint(1, 1)
            else:
                mul_pos_cap = solver.Constraint(0, 1)

            for jj in ii:
                mul_pos_cap.SetCoefficient(variables[jj], 1)

    size_cap = solver.Constraint(ROSTER_SIZE[ds], ROSTER_SIZE[ds])
    for variable in variables:
        size_cap.SetCoefficient(variable, 1)

    solution = solver.Solve()

    if solution == solver.OPTIMAL:
        roster = Roster(ds)

        for i, player in enumerate(players):
            if variables[i].solution_value() == 1:
                roster.add_player(player)

        return roster


def post_process(result, ds):
    if ds == 'FanDuel': # due to min drop rule
        _result = [{ "roster": ii, "proj": ii.projected() } for ii in result]
        _result = sorted(_result, key=lambda k: k["proj"], reverse=True)
        result = [ii["roster"] for ii in _result]
    return result


def get_num_lineups(player, lineups):
    num = 0
    for ii in lineups:
        if ii.is_member(player):
            num = num + 1
    return num


def get_exposure(players, lineups):
    return { ii.id: get_num_lineups(ii, lineups) for ii in players }


def calc_lineups(players, num_lineups, locked, ds, exposure, cus_proj):
    result = []

    max_point = 10000
    exposure_d = { ii['id']: ii for ii in exposure }
    teams = set([ii.team for ii in players])
    con_mul = []
    players_ = []
    idx = 0

    for ii in players:
        p = vars(ii)
        p.pop('_state')
        p['proj_points'] = float(cus_proj.get(str(ii.id), ii.proj_points))

        ci_ = []
        for jj in ii.actual_position.split('/'):
            ci_.append(idx)
            p['position'] = jj
            players_.append(Player(**p))
            idx += 1
        con_mul.append(ci_)
    players = players_

    ban = []
    _ban = []   # temp ban

    # for min exposure
    for ii in exposure:
        if ii['min']:
            _locked = [ii['id']]
            while True:
                # check and update all users' status
                cur_exps = get_exposure(players, result)
                for pid, exp in cur_exps.items():
                    if exp >= exposure_d[pid]['max'] and pid not in ban:
                        ban.append(pid)
                    elif exp >= exposure_d[pid]['min'] > 0 and pid not in _ban:
                        _ban.append(pid)

                if cur_exps[ii['id']] >= ii['min']:
                    break
                    
                roster = get_lineup(ds, players, teams, locked+_locked, ban+_ban, max_point, con_mul)

                if not roster:
                    return post_process(result, ds)

                max_point = roster.projected(gross=True) - 0.001
                if roster.get_num_teams() >= TEAM_LIMIT[ds]:
                    result.append(roster)
                    if len(result) == num_lineups:
                        return post_process(result, ds)

    # for max exposure -> focus on getting optimized lineups
    while True:
        cur_exps = get_exposure(players, result)
        for pid, exp in cur_exps.items():
            if exp >= exposure_d[pid]['max'] and pid not in ban:
                ban.append(pid)

        roster = get_lineup(ds, players, teams, locked, ban, max_point, con_mul)

        if not roster:
            return post_process(result, ds)

        max_point = roster.projected(gross=True) - 0.001
        if roster.get_num_teams() >= TEAM_LIMIT[ds]:
            result.append(roster)
            if len(result) == num_lineups:
                return post_process(result, ds)
