# -*- coding: utf-8 -*-
import time
import datetime
import logging
import tweepy
from optparse import make_option
from django.core.management.base import BaseCommand
from django.conf import settings
from virtualornithology.birds.auxiliary import load_list_from_file, normalize_str, to_unicode_or_bust
from virtualornithology.birds.models import User
from virtualornithology.birds.tasks import crawl_tweets

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--woeid',
            action='store',
            dest='woeid',
            default=None,
            type='int',
            help='Where in the world id.'),
        make_option('--source_account',
            action='store',
            dest='source_account',
            default=None,
            type='string',
            help='Account to crawl timeline.'),
        make_option('--keywords',
            action='store',
            dest='keywords_file',
            default=settings.TWITTER_SEARCH_KEYWORDS_FILE,
            type='string',
            help='A file with a list of keywords to query with.'),
        make_option('--log',
            action='store',
            dest='log_level',
            default=30,
            type='int',
            help='Log level.'),
        make_option('--minutes',
            action='store',
            dest='minutes',
            default=settings.STREAMING_SCRIPT_DURATION,
            type='int',
            help='Time in minutes to keep crawling.'),
    )

    def handle(self, *args, **options):
        logging.basicConfig(level=options['log_level'])

        path = settings.DATA_FOLDER

        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])

        # here the actions begins
        if settings.STREAMING_SOURCE_ACCOUNT:
            api = tweepy.API(auth)
        else:
            api = None

        keywords = set(load_list_from_file(options.get('keywords_file')))
        keywords = list(filter(lambda x: x and x[0] != '%' and 1 < len(x) < 60, keywords))
        keywords = list(map(normalize_str, keywords))
        keywords = keywords[0:125]

        locations = settings.TWITTER_SEARCH_LOCATION_BBOX

        self.time_limit = options.get('minutes', settings.STREAMING_SCRIPT_DURATION) * 60
        print('time limit', self.time_limit)
        self.start_time = time.time()

        now = datetime.datetime.now().strftime("%Y%m%d%H%M")

        self.filename = '{0}/{1}_{2}.data.gz'.format(path, settings.STREAMING_FILE_PREFIX, now)

        print(keywords)

        # people I have manually followed with the account @todocl
        if settings.STREAMING_SOURCE_ACCOUNT:
            people = map(str, api.friends_ids(screen_name=settings.STREAMING_SOURCE_ACCOUNT))
        else:
            people = None

        if settings.STREAMING_FOLLOW_ACCOUNTS:
            values = User.objects.filter(screen_name__in=settings.STREAMING_FOLLOW_ACCOUNTS).values('internal_id')
            ids = [x['internal_id'] for x in values]

            if not people:
                people = ids
            else:
                people.extend(ids)

        tweet_count = crawl_tweets(self.filename, track=keywords, follow=people, locations=locations, api_keys=api_keys, time_limit=self.time_limit)
        print('imported {0} tweets'.format(tweet_count))
