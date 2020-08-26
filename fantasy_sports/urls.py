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

admin.site.site_header = "Green Light Optimizer"

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', lineup_optimizer, name="lineup_optimizer"),
    url(r'^lineup-optimizer$', lineup_optimizer, name="lineup_optimizer"),
    url(r'^lineup-builder$', lineup_builder, name="lineup_builder"),
    url(r'^build-lineup$', build_lineup, name="build_lineup"),
    url(r'^gen-lineups', gen_lineups, name="gen_lineups"),
    url(r'^check-mlineups', check_mlineups, name="check_mlineups"),
    url(r'^export_lineups', export_lineups, name="export_lineups"),
    url(r'^export-mlineup', export_manual_lineup, name="export_manual_lineup"),
    url(r'^get-players', get_players, name="get_players"),
    url(r'^get-slates', get_slates, name="get_slates"),
    url(r'^go-dfs', go_dfs, name="go_dfs"),
    url(r'^tool', put_ids, name="put_ids"),
    url(r'^trigger-scraper', trigger_scraper, name="trigger_scraper"),
    url(r'^update-point', update_point, name="update_point"),
]
