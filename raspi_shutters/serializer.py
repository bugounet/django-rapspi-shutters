from raspi_shutters.models import Shutter
from rest_framework import serializers


class ShutterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shutter
        exclude = [
            'upside_down',
            'power_output_adress',
            'direction_selector_adress',
        ]

class ActuationSerializer(serializers.Serializer):
    target_position = serializers.ChoiceField(Shutter.POSITION_CHOICES)
    shutters = serializers.ListField(blank=True)
