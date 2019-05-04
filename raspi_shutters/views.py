import json

from django.core.exceptions import FieldError
from django.http import HttpResponse

# Create your views here.
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from domotics.models import Room
from raspi_shutters.actions import (
    update_home_forced_shutter_status,
)
from raspi_shutters.models import Shutter
from raspi_shutters.threads import ActuateShutterThread


class HttpResponseConflict(HttpResponse):
    status_code = 409


@csrf_exempt
def api_actuate_all(request, target_position):
    if target_position not in ["opened", "closed"]:
        return HttpResponseBadRequest(
            {
                "error": "Target position must belong to 'opened', 'closed' "
                "on route /api/shutter/all/<target_position>/"
            }
        )

    results = []

    update_home_forced_shutter_status(
        target_position=target_position, all_shutters=True
    )

    moved_shutters_list = Shutter.objects.exclude(
            current_position=target_position
    )
    for shutter in moved_shutters_list:
        if shutter.current_position == target_position:
            continue

        if shutter.running:
            shutter.force_stop()
            shutter.refresh_from_db()

        shutter.target_position = target_position
        time = shutter.get_transit_duration()
        results.append(
            {
                "id": shutter.id,
                "transit_duration": time.total_seconds(),
                "running": True,
            }
        )
    shutters = moved_shutters_list.values_list('id', flat=True)
    ActuateShutterThread(args=(shutters, target_position)).start()

    return HttpResponse(json.dumps(results))


@csrf_exempt
def api_actuate(request, shutter_id, target_position):
    try:
        shutter = Shutter.objects.get(id=shutter_id)
    except Shutter.DoesNotExist:
        return HttpResponseNotFound({"shutter_id": "Id not found."})
    if shutter.running:
        return HttpResponseConflict({"error": "shutter currently moving"})

    if target_position not in ["opened", "middle", "closed"]:
        return HttpResponseBadRequest(
            {
                "error":
                    "Target position must belong to 'opened', 'middle', "
                    "'closed' on route "
                    "/api/shutter/{}/<target_position>/".format(
                        shutter_id
                    )
            }
        )

    update_home_forced_shutter_status(target_position=target_position)

    shutter.target_position = target_position
    time = shutter.get_transit_duration()
    ActuateShutterThread(args=([shutter_id], target_position)).start()
    return HttpResponse(
        json.dumps(
            {
                "id": shutter.id,
                "transit_duration": time.total_seconds(),
                "running": True,
            }
        )
    )


@csrf_exempt
def api_actuate_in_room(request, room_id, target_position):
    if target_position not in ["opened", "closed"]:
        return HttpResponseBadRequest(
            {
                "error":
                    "Target position must belong to 'opened', 'closed' on "
                    "route /api/room/{}/shutters/<target_position>/".format(
                        room_id
                    )
            }
        )
    try:
        room = Room.objects.get(pk=room_id)
    except Shutter.DoesNotExist:
        return HttpResponseNotFound({"room_id": "Id not found."})
    target_states = set(
        Shutter.objects.exclude(room=room).values_list(
            "current_position", flat=True
        )
    )
    update_home_forced_shutter_status(
        target_position=target_position,
        all_shutters=(
            target_states == {"closed"} and target_position == "closed"
        ),
    )
    results = []
    for shutter in room.shutters.all():
        if shutter.current_position == target_position:
            continue

        if shutter.running:
            shutter.force_stop()
            shutter.refresh_from_db()

        shutter.target_position = target_position
        time = shutter.get_transit_duration()
        results.append(
            {
                "id": shutter.id,
                "transit_duration": time.total_seconds(),
                "running": True,
            }
        )
    shutters = room.shutters.values_list('id', flat=True)
    ActuateShutterThread(args=(shutters, target_position)).start()

    return HttpResponse(json.dumps(results))


def api_get(request, shutter_id):
    try:
        shutter = Shutter.objects.get(id=shutter_id)
    except Shutter.DoesNotExist:
        return HttpResponseNotFound({"shutter_id": "Id not found."})
    return HttpResponse(json.dumps(shutter.to_dict()))


def api_search(request):
    try:
        shutters = Shutter.objects.filter(**request.GET.dict())
        print(shutters)
    except FieldError as e:
        return HttpResponseBadRequest(json.dumps({"request.GET": str(e)}))
    result_d = {'meta': {'total_count': len(shutters)}, 'objects': []}
    for shutter in shutters:
        result_d['objects'].append(shutter.to_dict())
    return HttpResponse(json.dumps(result_d))


class ShutterViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()