from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from django.core.urlresolvers import reverse

class BirdsMiddleWare(SocialAuthExceptionMiddleware):
    def get_redirect_uri(self, request, exception):
        return reverse('portraits:portraits-home')
