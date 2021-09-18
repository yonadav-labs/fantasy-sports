# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from general.constants import DATA_SOURCE


class Slate(models.Model):
    data_source = models.CharField(max_length=30, choices=DATA_SOURCE)
    name = models.CharField(max_length=120)
    date = models.DateField()

    def __str__(self):
        return self.name


class Game(models.Model):
    slate = models.ForeignKey(Slate, on_delete=models.CASCADE, related_name="games")
    home_team = models.CharField(max_length=20)
    visit_team = models.CharField(max_length=20)
    time = models.CharField(max_length=20, null=True, blank=True, default="")
    home_score = models.CharField(max_length=50, null=True, blank=True)
    visit_score = models.CharField(max_length=50, null=True, blank=True)
    ou = models.FloatField(default=0)
    ml = models.CharField(max_length=20, null=True, blank=True, default="")
    display = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.visit_team}@{self.home_team}'


class Player(models.Model):
    slate = models.ForeignKey(Slate, on_delete=models.CASCADE, related_name="players")
    rid = models.CharField(max_length=100)
    uid = models.IntegerField()  # roto id
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.CharField(max_length=250, default="/static/img/nba.ico")
    injury = models.CharField(max_length=250, blank=True)
    opponent = models.CharField(max_length=50)
    position = models.CharField(max_length=50)
    actual_position = models.CharField(max_length=50)
    proj_points = models.DecimalField(max_digits=5, decimal_places=2)
    proj_delta = models.FloatField()
    salary = models.IntegerField()
    team = models.CharField(max_length=50)
    handedness = models.CharField(max_length=5, blank=True)
    order = models.CharField(max_length=5, blank=True)
    confirmed = models.BooleanField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class BaseGame(models.Model):
    data_source = models.CharField(max_length=30, choices=DATA_SOURCE, default='FanDuel')
    time = models.TimeField()
    visit_team = models.CharField(max_length=20)
    home_team = models.CharField(max_length=20)
    visit_score = models.CharField(max_length=50, null=True, blank=True)
    home_score = models.CharField(max_length=50, null=True, blank=True)
    ou = models.FloatField(default=0)
    ml = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.home_team, self.visit_team)


class BasePlayer(models.Model):
    data_source = models.CharField(max_length=30, choices=DATA_SOURCE, default='FanDuel')
    uid = models.IntegerField()  # roto id
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    avatar = models.CharField(max_length=250, default="/static/img/nba.ico")
    team = models.CharField(max_length=50)
    injury = models.CharField(max_length=250, blank=True, default='')  # from FD
    handedness = models.CharField(max_length=5, blank=True)
    order = models.CharField(max_length=5, blank=True)
    confirmed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)
