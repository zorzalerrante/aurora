from urllib.parse import urlparse
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

try:
    import ujson as json
except ImportError:
    import json


def convert_to_dicts(queryset, single=False):
    if not single:
        return json.loads(serializers.serialize("json", queryset))
    else:
        result = json.loads(serializers.serialize("json", queryset))
        if result:
            return result[0]
        return None


# TODO: this should be a decorator?
def render_json(request, data, dumped=False):
    if dumped:
        code = data
    else:
        code = json.dumps(data)
    return render_to_response('json.html', {'json': code}, context_instance=RequestContext(request), content_type='application/json')


# TODO: this should be a decorator?
def check_referer(request):
    referer = request.META.get('HTTP_REFERER', None)
    debug = settings.DEBUG

    if not debug and referer is None:
        raise PermissionDenied()

    if not debug and not urlparse(referer).netloc in settings.ALLOWED_HOSTS and not settings.ALLOWED_HOSTS[0] == '*':
        raise PermissionDenied()
