from django.utils.translation import ugettext_lazy as _
import django_filters.rest_framework

from rest_framework import status, viewsets
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from raspi_shutters.models import Shutter
from raspi_shutters.serializer import ShutterSerializer, ActuationSerializer
from raspi_shutters.threads import ActuateShutterThread, force_stop_shutter


class ShutterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing and actuating shutters.
    """
    serializer_class = ShutterSerializer
    queryset = Shutter.objects.all()
    permission_classes = (IsAuthenticated, )
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated],
            serializer_class=ActuationSerializer,
            url_path='actuate')
    def actuate_list(self, request):
        """ Execute a given action on given list of connected shutters

        If list not provided, all shutters are actuated.

        :param target_position: Requested position to reach
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        target_position = serializer.data['target_position']
        explicit_shutters_list = serializer.data.get('shutters', [])

        moved_shutters_list = Shutter.objects.exclude(
            current_position=target_position
        )
        if explicit_shutters_list:
            moved_shutters_list = moved_shutters_list.filter(
                id__in=explicit_shutters_list
            )

        results = []
        for shutter in moved_shutters_list:
            if shutter.running:
                return Response(
                    {'error': _("Shutter {} is busy").format(shutter.id)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            shutter.target_position = target_position
            time = shutter.get_transit_duration()
            results.append(
                {
                    "id": shutter.id,
                    "transit_duration": time.total_seconds(),
                    "target_position_arrival_time":
                        shutter.target_position_arrival_time,
                    "running": True,
                }
            )

        shutters = moved_shutters_list.values_list('id', flat=True)
        ActuateShutterThread(args=(shutters, target_position)).start()
        return Response(results, status=status.HTTP_202_ACCEPTED)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='running')
    def list_all_running_shutters(self, request):
        """ List running shutters
        """
        moving_shutters = Shutter.objects.filter(running=True)
        serializer = self.get_serializer(moving_shutters, many=True)
        return Response(serializer.data)

    @action(
        detail=True, methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=ActuationSerializer,
        url_path='actuate')
    def actuate(self, request, pk=None):
        """ Execute a given  action on a shutter

        :param target_position: Requested position to reach
        """
        shutter = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        target_position = serializer.data['target_position']

        if shutter.running:
            return Response(
                {'error': _("Shutter {} is busy").format(shutter.id)},
                status=status.HTTP_409_CONFLICT
            )

        shutter.target_position = target_position
        time = shutter.get_transit_duration()
        ActuateShutterThread(args=([shutter.id], target_position)).start()
        return Response({
            "id": shutter.id,
            "transit_duration": time.total_seconds(),
            "target_position_arrival_time":
                shutter.target_position_arrival_time,
            "running": True,
        })

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated],
        serializer_class=serializers.Serializer,
        url_path='force-stop')
    def force_stop(self, request, pk=None):
        shutter = self.get_object()
        force_stop_shutter(shutter)
        return Response(
            ShutterSerializer(shutter, many=False).data,
            status=status.HTTP_200_OK
        )