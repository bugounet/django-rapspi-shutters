# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from raspi_shutters.views import ShutterViewSet

from rest_framework.routers import DefaultRouter

shutters_router = DefaultRouter()
shutters_router.register(
    r'shutter', ShutterViewSet, basename='shutter'
)
urlpatterns = shutters_router.urls
