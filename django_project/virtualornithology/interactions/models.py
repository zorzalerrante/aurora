# coding=utf-8
from django.db import models
from virtualornithology.portraits.models import Portrait

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


class InteractionEvent(models.Model):
    session = models.CharField(max_length=255)
    portrait = models.ForeignKey(Portrait, null=True)
    source_app = models.CharField(max_length=255, default='')
    experimental_group = models.CharField(max_length=255, default='')
    key = models.CharField(max_length=255, db_index=True)
    data = models.TextField()
    meta = models.TextField(default='{}')
    reported_datetime = models.CharField(max_length=255, null=True)
    datetime = models.DateTimeField(auto_now_add=True)

    def add_request_meta(self, request, ua=None, mobile=False):
        meta = {
            'ip': get_client_ip(request),
            'referer': request.META.get('HTTP_REFERER', ''),
            'user_agent': str(ua) if ua is not None else request.META.get('HTTP_USER_AGENT', ''),
            'mobile': mobile
        }

        self.portrait = Portrait.objects.get(auth_screen_name=request.user.username.lower()) if request.user.is_authenticated() else None
        self.meta = json.dumps(meta)
