import threading

from django.contrib import admin

# Register your models here.
from raspi_shutters.models import ShutterConfig
from raspi_shutters.tasks import actuate_shutter


@admin.register(ShutterConfig)
class ShutterConfigAdmin(admin.ModelAdmin):
    model = ShutterConfig

    list_display = ('shutter_name', 'running', 'current_position', 'target_position')

    actions = (
        'actuate_shutter_to_opened',
        'actuate_shutter_to_middle',
        'actuate_shutter_to_closed',
    )

    @staticmethod
    def actuate_shutter_to_opened(request, queryset):
        for shutter in queryset.all():
            def open_shutter():
                actuate_shutter(shutter, ShutterConfig.POSITION_OPENED)
            action = threading.Thread(target=open_shutter)
            action.start()

    @staticmethod
    def actuate_shutter_to_middle(request, queryset):
        for shutter in queryset.all():
            def midway_shutter():
                actuate_shutter(shutter, ShutterConfig.POSITION_MIDDLE)
            action = threading.Thread(target=midway_shutter)
            action.start()

    @staticmethod
    def actuate_shutter_to_closed(request, queryset):
        for shutter in queryset.all():
            def close_shutter():
                try:
                    actuate_shutter(shutter, ShutterConfig.POSITION_CLOSED)
                except
                    request

            action = threading.Thread(target=close_shutter)
            action.start()
