# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _


class UnavailableError(RuntimeError):
    def __init__(self):
        super(UnavailableError, self).__init__(
            _("this shutter is currently unavailable")
        )


class BrokenShutterError(RuntimeError):
    pass
