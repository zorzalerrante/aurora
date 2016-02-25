from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.gzip import gzip_page
from .models import Portrait
from .tasks import portrait_follow, portrait_share
from virtualornithology.interactions.views import prepare_session
from virtualornithology.birds.views import render_json

try:
    import ujson as json
except ImportError:
    import json


@gzip_page
def get_portrait(request, screen_name):
    portrait = get_object_or_404(Portrait, auth_screen_name=screen_name.lower(), active=True)

    if not portrait.public_access_enabled:
        if request.user.username.lower() != screen_name.lower():
            raise PermissionDenied()

    return render_json(request, portrait.portrait_content, dumped=True)


@gzip_page
@login_required
def get_recommendations(request, screen_name):
    if request.user.username.lower() == screen_name.lower():
        portrait = get_object_or_404(Portrait, auth_screen_name=screen_name.lower(), active=True)
        return render_json(request, portrait.portrait_recommendations, dumped=True)

    raise PermissionDenied()


# @login_required
def view_portrait(request, screen_name):
    print(screen_name)
    portrait = get_object_or_404(Portrait, auth_screen_name=screen_name.lower(), active=True)

    if not portrait.public_access_enabled:
        if not request.user.is_authenticated() or request.user.username.lower() != screen_name.lower():
            return render_to_response('portraits/protected.html', {
                'portrait_screen_name': screen_name,
                'portrait_pk': portrait.pk,
                'profile_data': json.dumps(portrait.user_data)
            }, context_instance=RequestContext(request))

    if not portrait.portrait_content:
        return render_to_response('portraits/wait.html', {
            'portrait_screen_name': screen_name,
            'portrait_pk': portrait.pk,
            'profile_data': json.dumps(portrait.user_data),
            'demo_portrait': portrait.demo_portrait
        }, context_instance=RequestContext(request))

    record_interactions = False
    show_recommendations = False

    if request.user.is_authenticated():
        record_interactions = True
        auth_portrait = Portrait.objects.get(auth_screen_name=request.user.username.lower(), active=True)

        if auth_portrait == portrait:
            show_recommendations = True
            portrait.last_access = timezone.now()
            portrait.save()

        if not 'experimental_group' in request.session or not 'portraits' in request.session['experimental_group']:
            print('preparing session')
            prepare_session(request, '{0}_{1}'.format(auth_portrait.condition_ui, auth_portrait.condition_rec), 'portraits')
            print(request.session)

    return render_to_response('portraits/portrait.html', {
        'portrait_screen_name': screen_name,
        'portrait_current_pk': portrait.pk,
        'condition_ui': portrait.condition_ui,
        'condition_rec': portrait.condition_rec,
        'last_update': portrait.last_update_date.isoformat(),
        'demo_portrait': portrait.demo_portrait,
        'show_recommendations': show_recommendations,
        'record_interactions': record_interactions,
        'current_app': 'portraits',
        'client_datetime_var': 'client_datetime'
    }, context_instance=RequestContext(request))


@gzip_page
def public_portraits(request):
    portraits = Portrait.objects.exclude(Q(portrait_content=None)|Q(active=False)|Q(public_access_enabled=False)).filter(featured_on_home=True).order_by('-created_on')
    # we need to concat json
    user_data = portraits.values_list('user_data', flat=True)
    users = '[{0}]'.format(u','.join(user_data[0:50]))
    return render_json(request, users, dumped=True)


def portraits_home(request):
    return render_to_response('portraits/index.html', {'n_portraits': 50}, context_instance=RequestContext(request))


# actions
@login_required
def follow(request):
    #print 'follow'
    #print request.POST
    auth_user = request.user

    source_user = request.POST.get('source', '')
    if not source_user or auth_user.username != source_user:
        print(auth_user.username, len(auth_user.username), source_user, len(source_user))
        raise PermissionDenied

    portrait = get_object_or_404(Portrait, auth_screen_name=auth_user.username.lower())

    target_user_id = request.POST.get('target', '')[:100]
    if not target_user_id:
        raise Http404

    try:
        followed = portrait_follow(portrait, target_user_id)
    except:
        followed = False

    return render_json(request, followed)


@login_required
def share(request):
    auth_user = request.user

    source_user = request.POST.get('source', '')
    if not source_user or auth_user.username.lower() != source_user.lower():
        print(auth_user.username, len(auth_user.username), source_user, len(source_user))
        raise PermissionDenied

    portrait = get_object_or_404(Portrait, auth_screen_name=auth_user.username.lower())

    try:
        followed = portrait_share(portrait)
    except Exception as err:
        print(err)
        followed = False

    print('share result', followed)

    return render_json(request, followed)
