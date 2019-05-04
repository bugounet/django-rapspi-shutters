from datetime import timedelta

from django.test import TestCase

# Create your tests here.
from raspi_shutters.models import Shutter


class ConfigUtilsTestCase(TestCase):
    def test_get_direction_with_no_current_returns_down(self):
        # assuming
        config = Shutter(
            target_position=Shutter.POSITION_OPENED,
            current_position=None
        )

        # when
        result = config.get_direction()

        # then
        self.assertEqual(result, Shutter.DIRECTION_DOWN)

    def test_get_direction_with_same_current_returns_down(self):
        # assuming
        config = Shutter(
            target_position=Shutter.POSITION_MIDDLE,
            current_position=Shutter.POSITION_MIDDLE,
        )

        # when
        result = config.get_direction()

        # then
        self.assertEqual(result, Shutter.DIRECTION_DOWN)

    def test_get_direction_with_lower_target_returns_down(self):
        # assuming
        config = Shutter(
            target_position=Shutter.POSITION_OPENED,
            current_position=Shutter.POSITION_CLOSED,
        )

        # when
        result = config.get_direction()

        # then
        self.assertEqual(result, Shutter.DIRECTION_DOWN)

    def test_get_direction_with_high_target(self):
        # assuming
        config = Shutter(
            current_position=Shutter.POSITION_CLOSED,
            target_position=Shutter.POSITION_OPENED,
        )

        # when
        result = config.get_direction()

        # then
        self.assertEqual(result, Shutter.DIRECTION_DOWN)

    def test_get_transit_duration_from_known_position(self):
        # assuming
        config = Shutter(
            target_position=Shutter.POSITION_CLOSED,
            current_position=Shutter.POSITION_MIDDLE,
            closed_from_middle_timer=timedelta(seconds=10.5),
        )

        # when
        result = config.get_transit_duration()

        # then
        self.assertIsInstance(result, timedelta)
        self.assertEqual(result.total_seconds(), 10.5)

    def test_get_transit_duration_from_unknown_position(self):
        # assuming
        config = Shutter(
            target_position=Shutter.POSITION_CLOSED,
            current_position=Shutter.POSITION_OPENED,
            # This is hell... we're upsidedown
            opened_from_closed_timer=timedelta(seconds=666),
            # else it's good
            closed_from_opened_timer=timedelta(seconds=10.5)
        )

        # when
        result = config.get_transit_duration()

        # then
        self.assertIsInstance(result, timedelta)
        self.assertEqual(result.total_seconds(), 10.5)
