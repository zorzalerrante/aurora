from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^timelines/', include('virtualornithology.timelines.urls', namespace="timelines")),
    url(r'^portraits/', include('virtualornithology.portraits.urls', namespace="portraits")),
    url(r'^events/', include('virtualornithology.interactions.urls', namespace="interactions")),
    # Our site urls
    url('', include('django.contrib.auth.urls', namespace='auth')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^about/$', TemplateView.as_view(template_name='site/about.html'), name='about'),
    url(r'^$', TemplateView.as_view(template_name='site/index.html'), name='home'),
)

