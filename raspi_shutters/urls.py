# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import shutters.views
from django.urls import path

from rest_framework.routers import DefaultRouter


shutters_router = DefaultRouter()
router.register(r'shutters', ShuttersViewSet, basename='shutter')
urlpatterns = router.urls
# urlpatterns = [
#     path("/", shutters_viwset.as_view()),
#     path("all/<slug:target_position>/", shutters.views.api_actuate_all),
#     path("<int:shutter_id>/", shutters.views.api_get),
#     path(
#         "<int:shutter_id>/<slug:target_position>/",
#         shutters.views.api_actuate
#     ),
#     path("", shutters.views.api_search),
# ]
