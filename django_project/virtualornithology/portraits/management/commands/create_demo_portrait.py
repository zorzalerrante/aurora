# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option
import tweepy
from virtualornithology.portraits.tasks import create_portrait_model

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--screen_name',
            action='store',
            dest='screen_name',
            default=None,
            type='str',
            help='User screen name.'),
    )

    def handle(self, *args, **options):
        path = '{0}/users'.format(settings.PORTRAIT_FOLDER)

        screen_name = options.get('screen_name', None)

        if not screen_name:
            print('no user')
            return

        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])
        api = tweepy.API(auth)

        user_response = api.get_user(screen_name)._json
        print(user_response)
        create_portrait_model(user_response, has_auth=False)
