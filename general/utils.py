import csv
import random


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def csv_to_list(csv_reader):
    result = []
    for row in csv_reader:
        result.append(row)

    return result


def parse_players_csv(file, data_source):
    """
    :param file: stream
    :return: list(dict)
    """
    decoded_file = file.read().decode('utf-8').splitlines()
    net_data = []

    if data_source == 'DraftKings':
        row_start = 7
    elif data_source == 'FanDuel':
        row_start = 0

    for row in decoded_file[row_start:]:
        net_data.append(row)

    reader = csv.DictReader(net_data)

    return csv_to_list(reader)


def parse_projection_csv(file):
    """
    :return: list(dict)
    """
    decoded_file = file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_file)

    return csv_to_list(reader)


def parse_name(name):
    """
    get first and last name from name string after processing
    """
    name = name.strip().replace('.', '')
    name_ = name.split(' ')
    if len(name_) > 1:
        return name_[0], ' '.join(name_[1:])
    return name, ''


def parse_game_info(data_source, game_info):
    visit_team = home_team = time = ""
    try:
        if data_source == 'DraftKings':
            parts = game_info.split(' ')
            visit_team, home_team = parts[0].split('@')
            time = parts[2]
        elif data_source == 'FanDuel':
            visit_team, home_team = game_info.split('@')
    except Exception:
        pass

    return visit_team, home_team, time


def get_delta(proj):
    if proj == 0:
        return 0

    factor = (-100, 100)
    sign = 1 if random.randrange(0, 2) else -1
    delta = random.randrange(factor[0], factor[1]) / 100.0

    return delta * sign
