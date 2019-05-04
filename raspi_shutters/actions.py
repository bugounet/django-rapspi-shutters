# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from domotics.models import HomeEvent, HomeStatus


ACTION_NAME_D = {
    "opened": _("Open"),
    "middle": _("Shadow"),
    "closed": _("Close"),
}


def update_home_forced_shutter_status(target_position, all_shutters=False):
    home = HomeStatus.objects.get()
    if target_position == "opened" and home.forced_shut_status:
        home.forced_shut_status = False
    elif all_shutters:
        home.forced_shut_status = target_position == "closed"
    home.save()
