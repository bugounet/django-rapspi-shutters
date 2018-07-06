# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from time import sleep

from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


from raspi_shutters.exceptions import UnavailableError, BrokenShutterError


if not settings.DEBUG:
    from gpiozero import LED
else:
    from unittest import mock
    LED = mock.Mock()


def actuate_shutter(shutter, target_position):
    if shutter.running:
        raise UnavailableError()

    try:
        power_output = LED(shutter.power_output_adress)
        direction_selector_output = LED(shutter.direction_selector_adress)
    except Exception as e:
        raise BrokenShutterError(
            _("Communication with shutter command hardware lost")
        )
    shutter.running = True
    shutter.save()

    # No matter what we'll stop what the shutter was doing
    # then pause to let relays take their position. When everything's
    # done, we'll set-direction, pause for the relay and turn the shutter
    # on.

    # stop then wait for relay
    try:
        power_output.off()
    except Exception as e:
        raise BrokenShutterError(_("Can't actuate shutter"))
    else:
        sleep(0.1)

    # setup direction then wait for relay
    if shutter.get_direction() == shutter.DIRECTION_UP:
        if shutter.upside_down == False:
            direction_selector_output.on()
        else:
            direction_selector_output.off()
    else:
        if shutter.upside_down == False:
            direction_selector_output.off()
        else:
            direction_selector_output.on()

    # update-transit time & dates
    expected_transit_duration = shutter.get_transit_duration()
    shutter.target_position = target_position
    shutter.target_position_arrival_time = now() + expected_transit_duration
    shutter.save()
    sleep(0.05)

    # Turn shutter on for expected amount of time
    power_output.on()
    seconds_of_pause = expected_transit_duration.total_seconds()
    print("waiting for shutter {} seconds".format(seconds_of_pause))
    sleep(seconds_of_pause)
    power_output.off()

    # update model to it's terminal status
    shutter.running = False
    shutter.current_position = target_position
    shutter.target_position_arrival_time = None
    shutter.save()
