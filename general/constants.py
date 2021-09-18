DATA_SOURCE = (
    ('DraftKings', 'DraftKings'),
    ('FanDuel', 'FanDuel'),
    ('Yahoo', 'Yahoo'),
)


POSITION = (
    ('PG', 'PG'), 
    ('SG', 'SG'), 
    ('SF', 'SF'), 
    ('PF', 'PF'), 
    ('C', 'C')
)


POSITION_LIMITS = {
    'FanDuel': [
                   ["PG", 2, 2],
                   ["SG", 2, 2],
                   ["SF", 2, 2],
                   ["PF", 2, 2],
                   ["C", 1, 1]
               ],
    'DraftKings': [
                      ["PG", 1, 3],
                      ["SG", 1, 3],
                      ["SF", 1, 3],
                      ["PF", 1, 3],
                      ["C", 1, 2],
                      ["PG,SG", 3, 4],
                      ["SF,PF", 3, 4]
                  ],
    'Yahoo': [
                ["PG", 1, 3],
                ["SG", 1, 3],
                ["SF", 1, 3],
                ["PF", 1, 3],
                ["C", 1, 2],
                ["PG,SG", 3, 4],
                ["SF,PF", 3, 4]
            ]
}


SALARY_CAP = {
    'FanDuel': 60000,
    'DraftKings': 50000,
    'Yahoo': 200,
}


ROSTER_SIZE = {
    'FanDuel': 9,
    'DraftKings': 8,
    'Yahoo': 8,
}


TEAM_LIMIT = {
    'FanDuel': 3,
    'Yahoo': 3,
    'DraftKings': 2
}


TEAM_MEMEBER_LIMIT = {
    'FanDuel': 4,
    'Yahoo': 6,
    'DraftKings': 8
}


CSV_FIELDS = {
    'FanDuel': ['PG', 'PG', 'SG', 'SG', 'SF', 'SF', 'PF', 'PF', 'C'],
    'DraftKings': ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL'],
    'Yahoo': ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL']
}
