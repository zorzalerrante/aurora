from django.conf.urls import patterns, url
from .views import record_event

urlpatterns = patterns('',
    url(r'^record/event$', record_event, name='record-event'),
)

