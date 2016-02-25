# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
import time
from virtualornithology.portraits.models import Portrait
from virtualornithology.portraits.tasks import portrait_api
import tweepy
from tweepy import TweepError


class Command(BaseCommand):
    def handle(self, *args, **options):
        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])

        new_portraits = Portrait.objects.filter(active=True, demo_portrait=False)

        print('scheduled portraits', new_portraits.count())

        for portrait in new_portraits:
            is_new_portrait = portrait.portrait_content is None

            print('user', portrait.auth_screen_name)
            print('new', is_new_portrait)

            try:
                portrait_api(portrait)
                print('OK')
            except TweepError as err:
                print('ERROR', err)
                portrait.active = False
                portrait.save()
                continue
            except Exception as err:
                print('ERROR', err)
                continue

            # to avoid too many connections
            time.sleep(5)
