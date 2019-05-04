from django.contrib import admin

# Register your models here.
from raspi_shutters.models import Shutter
from raspi_shutters.threads import ActuateShutterThread


@admin.register(Shutter)
class ShutterAdmin(admin.ModelAdmin):
    model = Shutter

    list_display = (
        "shutter_name",
        "running",
        "current_position",
        "target_position"
    )

    actions = (
        "actuate_shutter_to_opened",
        "actuate_shutter_to_middle",
        "actuate_shutter_to_closed",
    )

    def actuate_shutter_to_opened(self, request, queryset):
        shutter_ids = queryset.all().values_list("id", flat=True)
        ActuateShutterThread(
            args=(shutter_ids, Shutter.POSITION_OPENED)
        ).start()

    def actuate_shutter_to_middle(self, request, queryset):
        shutter_ids = queryset.all().values_list("id", flat=True)
        ActuateShutterThread(
            args=(shutter_ids, Shutter.POSITION_MIDDLE)
        ).start()

    def actuate_shutter_to_closed(self, request, queryset):
        shutter_ids = queryset.all().values_list("id", flat=True)
        ActuateShutterThread(
            args=(shutter_ids, Shutter.POSITION_CLOSED)
        ).start()
