from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from user_agents import parse as agentparse
from virtualornithology.birds.views import check_referer
from virtualornithology.interactions.views import prepare_session
from .models import Timeline


def last_timeline_json(request):
    check_referer(request)
    latest = Timeline.objects.all().order_by('-datetime')[0]
    return render_to_response('json.html', {'json': latest.json}, context_instance=RequestContext(request), content_type='application/json')


def timeline_home(request, timeline_id=None):
    ua = agentparse(request.META.get('HTTP_USER_AGENT', ''))
    print(ua)
    print(request.GET)

    if ua.is_bot:
        return render_to_response('timelines/bots.html', context_instance=RequestContext(request))

    session = request.session
    print(session, session.session_key, session.items())
    prepare_session(request, 'all', 'aurora')

    return render_to_response('timelines/timeline-baseline.html', {
        'timeline_home_tweets': 10,
        'record_interactions': True,
        'current_app': 'aurora',
        'client_datetime_var': 'client_datetime'
    }, context_instance=RequestContext(request))
