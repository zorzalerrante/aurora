from user_agents import parse as agentparse
from .models import InteractionEvent
from virtualornithology.birds.views import render_json, check_referer
from django.core.exceptions import PermissionDenied
from django.http import Http404

try:
    import ujson as json
except ImportError:
    import json


def get_client_ip(request):
    # from http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def prepare_session(request, group, application):
    session = request.session
    if 'experimental_group' not in session:
        session.save()
        session['experimental_group'] = {application: group}
    else:
        if not application in session['experimental_group']:
            session['experimental_group'][application] = group
            session.save()
    print(session['experimental_group'])


def record_event(request):
    check_referer(request)

    ua = agentparse(request.META.get('HTTP_USER_AGENT', ''))
    print(ua)

    if ua.is_bot:
        raise PermissionDenied()

    session = request.session

    if 'experimental_group' not in session:
        raise PermissionDenied()

    if not 'source_app' in request.POST:
        print('no source app in POST', request.POST)
        raise Http404

    source_app = request.POST.get('source_app', None)
    if not source_app or not source_app in ('aurora', 'portraits'):
        print('invalid app', source_app)
        raise Http404

    if not 'user_events' in request.POST:
        print('no user events in POST', request.POST)
        raise Http404

    print('POST', request.POST)

    user_events_str = str(request.POST['user_events'])

    try:
        user_events = json.loads(user_events_str)
    except ValueError:
        raise Http404

    print(session.session_key)
    print(session['experimental_group'])

    for event in user_events:
        print(source_app, 'event', event)
        try:
            interaction = InteractionEvent(session=session.session_key,
                             experimental_group=session['experimental_group'][source_app],
                             source_app=source_app,
                             key=event['name'],
                             data=json.dumps(event),
                             reported_datetime=event['client_datetime'])
            interaction.add_request_meta(request, ua=ua, mobile=(ua.is_mobile or ua.is_tablet or bool(request.GET.get('mobile_version', False))))
            interaction.save()
        except KeyError:
            continue

    return render_json(request, {'json': True})
