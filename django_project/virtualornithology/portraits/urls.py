from django.conf.urls import patterns, url
from .views import portraits_home, get_portrait, get_recommendations, view_portrait, follow, share, public_portraits


urlpatterns = patterns('',
    url(r'^perfiles/action/follow/$', follow, name='action-follow'),
    url(r'^perfiles/action/share/$', share, name='action-share'),
    url(r'^perfiles/api/public_portraits/$', public_portraits, name='get-public-portraits'),
    url(r'^perfiles/api/portrait/(?P<screen_name>\w+)/$', get_portrait, name='get-portrait'),
    url(r'^perfiles/api/recommendations/(?P<screen_name>\w+)/$', get_recommendations, name='get-recommendations'),
    url(r'^perfil/(?P<screen_name>\w+)/$', view_portrait, name='view-portrait'),
    url(r'^$', portraits_home, name='portraits-home'),
)