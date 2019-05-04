from django.utils.translation import ugettext_lazy as _

from rest_framework import status, viewsets
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

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def all(self, request):
        """ Execute a given action on all connected shutters

        :param target_position: Requested position to reach
        """
        serializer = ActuationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        target_position = serializer.data['target_position']

        results = []
        moved_shutters_list = Shutter.objects.exclude(
              current_position=target_position
        )
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

    @all.mapping.get
    def list_all_running_shutters(self):
        """ List running shutters
        """
        moving_shutters = Shutter.objects.filter(running=True)

        serializer = self.get_serializer(moving_shutters, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def actuate(self, request, pk=None):
        """ Execute a given  action on a shutter

        :param target_position: Requested position to reach
        """
        shutter = self.get_object()
        serializer = ActuationSerializer(data=request.data)
        
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

    @actuate.mapping.get
    def list_running_shutters(self, request, pk=None):
        """ Ask the API if given shutter is running
        """
        shutter = self.get_object()

        return Response({
            "id": shutter.id,
            "running": shutter.running,
            "target_position_arrival_time":
                shutter.target_position_arrival_time,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def force_stop(self, request, pk=None):
        shutter = self.get_object()

        force_stop_shutter(shutter)

        return self.get_serializer(shutter)
