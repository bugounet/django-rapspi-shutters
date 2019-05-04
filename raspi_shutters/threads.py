# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from collections import OrderedDict
from logging import getLogger

from time import sleep
import threading
from django.conf import settings
from django.db import connection
from django.db import transaction
from django.utils.timezone import now

from raspi_shutters.models import Shutter

logger = getLogger(__name__)
if not hasattr(settings, 'DISABLE_SHUTTERS') or settings.DISABLE_SHUTTERS:
    from mock import Mock
    LED = Mock()
    logger.warning(
        "Shutters are disabled. Set DISABLE_SHUTTERS to False in "
        "your django settings file to enable GPIO actions."
    )
else:
    from gpiozero import LED

sleep_event = threading.Event()


class ActuateShutterThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(ActuateShutterThread, self).__init__(*args, **kwargs)

    def run(self):
        self.actuate_shutter(*self._args)
        connection.close()

    def actuate_shutter(self, shutter_ids_list, target_position):
        logger.info(
            "Actuating shutter {shutter_id} to target_position".format(
                shutter_id=",".join([str(_id) for _id in shutter_ids_list]),
                target_position=target_position,
            )
        )

        shutters = list(Shutter.objects.filter(id__in=shutter_ids_list))
        with transaction.atomic():
            (
                gpio_ports_mapping,
                timing_mapping
            ) = self.phase_1_init_gpio_states(shutters, target_position)

        self.phase_2_start_motors(gpio_ports_mapping)
        self.phase_3_stop_motors_on_time(timing_mapping, gpio_ports_mapping)

        with transaction.atomic():
            self.phse_4_save_new_status_in_DB(
                shutters, target_position, gpio_ports_mapping
            )
        logger.info("DB updated & locks released")

    def phase_1_init_gpio_states(self, shutters, target_position):
        gpio_ports_mapping = {}
        timing_mapping = {}

        for shutter in shutters:
            if shutter.running:
                self.log_busy_shutter_warning(shutter, target_position)
                continue
            try:
                ports = gpio_ports_mapping[shutter.id] = (
                    LED(shutter.power_output_adress),
                    LED(shutter.direction_selector_adress),
                )
            except Exception as e:
                self.log_gpio_error(shutter, target_position, e)
                continue

            self.lock_shutter_in_db(shutter, target_position)
            self.setup_shutter_motion(shutter, ports)

            # update-transit time & dates
            seconds_of_pause = self.save_arrival_time_estimation(shutter)
            shutters_at_time = timing_mapping.get(seconds_of_pause, [])
            shutters_at_time.append(shutter.id)
            timing_mapping[seconds_of_pause] = shutters_at_time

        timing_mapping = OrderedDict(sorted(timing_mapping.items()))
        return gpio_ports_mapping, timing_mapping

    @staticmethod
    def phase_2_start_motors(gpio_ports_mapping):
        # turn them on
        for shutter_id, ports in gpio_ports_mapping.items():
            logger.info("Start shutter %s", shutter_id)
            ports[0].off()

    @staticmethod
    def phase_3_stop_motors_on_time(timing_mapping, gpio_ports_mapping):
        previous_step = 0
        for time_step in timing_mapping.keys():
            delta = time_step - previous_step
            previous_step = time_step
            logger.info(
                "stop shutters %s after %s seconds",
                timing_mapping[time_step], delta
            )
            sleep_event.wait(timeout=delta)
            # stop them all
            for shutter_id in timing_mapping[time_step]:
                gpio_ports_mapping[shutter_id][0].on()
                logger.info("shutter {} stopped.".format(shutter_id))

    @staticmethod
    def phase_4_save_new_status_in_DB(
        shutters, target_position, gpio_ports_mapping
    ):
        for shutter in shutters:
            # update model to it's terminal status
            shutter.running = False
            shutter.target_position_arrival_time = None
            if shutter.id in gpio_ports_mapping:
                shutter.current_position = target_position
            shutter.save()

    def log_gpio_error(self, shutter, target_position, e):
        logger.error("Shutter {} broken: {}".format(shutter.id, str(e)))

    def log_busy_shutter_warning(self, shutter, target_position):
        logger.warning(
            "Shutter {} currently moving. Action skipped".format(shutter.id)
        )

    def setup_shutter_motion(self, shutter, ports):
        # No matter what we'll stop what the shutter was doing
        # then pause to let relays take their position. When
        # everything's done, we'll set-direction, pause for the relay
        # and turn the shutter on.
        ports[0].on()
        sleep(0.05)

        # setup direction then wait for relay
        if shutter.get_direction() == shutter.DIRECTION_UP:
            if shutter.upside_down is False:
                ports[1].off()
            else:
                ports[1].on()
        else:
            if shutter.upside_down is False:
                ports[1].on()
            else:
                ports[1].off()

    @staticmethod
    def lock_shutter_in_db(shutter, target_position):
        shutter.running = True
        shutter.target_position = target_position
        shutter.save()
        shutter.refresh_from_db()

    @staticmethod
    def save_arrival_time_estimation(shutter):
        expected_transit_duration = shutter.get_transit_duration()
        shutter.target_position_arrival_time = (
            now() + expected_transit_duration
        )
        shutter.save()
        return expected_transit_duration.total_seconds()


def force_stop_shutter(shutter):
    logger.info("Forcing shutter {} stop.".format(shutter.id))
    LED(shutter.power_output_adress).on()
    shutter.running = False
    shutter.save(update_fields=["running"])
    logger.info("Shutter force stopped.")
