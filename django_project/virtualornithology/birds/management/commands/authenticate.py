# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import tweepy

class Command(BaseCommand):

    def handle(self, *args, **options):
        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])

        try:
            redirect_url = auth.get_authorization_url()
        except tweepy.TweepError as e:
            print('Error! Failed to get request token.')
            raise e

        print(redirect_url)
        verifier = input('Verifier:')

        print(auth.get_access_token(verifier=verifier))
