from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^events/', include('virtualornithology.interactions.urls', namespace="interactions")),
    url('', include('django.contrib.auth.urls', namespace='auth')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^timelines/', include('virtualornithology.timelines.urls', namespace="timelines")),
    url(r'^', include('virtualornithology.portraits.urls', namespace="portraits")),
)
