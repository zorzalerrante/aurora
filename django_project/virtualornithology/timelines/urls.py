from django.conf.urls import patterns, url
from .views import last_timeline_json, timeline_home


urlpatterns = patterns('',
    url(r'^api/timeline/latest$', last_timeline_json, name='latest-timeline'),
    url(r'^$', timeline_home, name='timeline-home'),
)

