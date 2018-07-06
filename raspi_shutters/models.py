from django.db import models
from django.utils.translation import ugettext_lazy as _


class ShutterConfig(models.Model):
    DIRECTION_UP = True
    DIRECTION_DOWN = False
    DIRECTION_CHOICES = (
        (DIRECTION_UP, _("Down")),
        (DIRECTION_DOWN, _("Down"))
    )

    POSITION_OPENED = 'opened'
    POSITION_MIDDLE = 'middle'
    POSITION_CLOSED = 'closed'
    POSITION_CHOICES = (
        (POSITION_OPENED, _("Opened")),
        (POSITION_MIDDLE, _("Shadow")),
        (POSITION_CLOSED, _("Closed")),
    )
    POSITION_ORDERING = {
        POSITION_OPENED: 1,
        POSITION_MIDDLE: 2,
        POSITION_CLOSED: 3,
    }


    # config
    shutter_name = models.CharField(max_length=100)
    upside_down = models.BooleanField()
    power_output_adress = models.PositiveSmallIntegerField(
        unique=True
    )
    direction_selector_adress = models.PositiveSmallIntegerField(
        unique=True
    )
    opened_from_middle_timer = models.DurationField()
    opened_from_closed_timer = models.DurationField()
    middle_from_opened_timer = models.DurationField()
    middle_from_closed_timer = models.DurationField()
    closed_from_middle_timer = models.DurationField()
    closed_from_opened_timer = models.DurationField()

    # usage
    running = models.BooleanField()
    current_position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        null=True,
        blank=True,
        default=None
    )
    target_position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        default=POSITION_CLOSED
    )
    target_position_arrival_time = models.DateTimeField(
        null=True,
        blank=True
    )


    def get_direction(self):
        if self.current_position is None:
            return self.DIRECTION_DOWN

        current_numeric = self.POSITION_ORDERING[self.target_position]
        target_numeric = self.POSITION_ORDERING[self.current_position]

        if current_numeric > target_numeric:
            return self.DIRECTION_UP
        else:
            return self.DIRECTION_DOWN

    def get_transit_duration(self):
        # technically, opening a shutter is longer than closing it. This is
        # why in case of unknown position, target will always-default to
        # "closed" position while runing for the longer possible time.
        DEFAULT_SUM = self.opened_from_closed_timer
        # else we use this transition table to determine transit time
        # using current-position and target-position.
        TIMETABLE = {
            (self.POSITION_OPENED, self.POSITION_MIDDLE):
                self.middle_from_opened_timer,
            (self.POSITION_OPENED, self.POSITION_CLOSED):
                self.closed_from_opened_timer,
            (self.POSITION_MIDDLE, self.POSITION_OPENED):
                self.opened_from_middle_timer,
            (self.POSITION_MIDDLE, self.POSITION_CLOSED):
                self.closed_from_middle_timer,
            (self.POSITION_CLOSED, self.POSITION_OPENED):
                self.opened_from_closed_timer,
            (self.POSITION_CLOSED, self.POSITION_MIDDLE):
                self.opened_from_middle_timer,
        }
        return TIMETABLE.get(
            (self.current_position, self.target_position),
            DEFAULT_SUM
        )