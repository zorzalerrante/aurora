# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Max
from virtualornithology.birds.models import Tweet
from virtualornithology.timelines.tasks import generate_timeline
import tweepy
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--post_timeline',
            action='store_true',
            dest='post_timeline',
            default=False,
            help='True if timeline should be posted to Twitter using credentials.'),
        make_option('--popular',
            action='store_true',
            dest='popular',
            default=False,
            help='True if only tweets with retweets should be considered.'),
        make_option('--hours',
            dest='hours',
            type='int',
            default=2,
            help='Number of hours to consider.'),
        make_option('--turns',
            dest='turns',
            type='int',
            default=5,
            help='Number of turns to sideline locations.'),
        make_option('--n_candidates',
            dest='n_candidates',
            type='int',
            default=None,
            help='Number of candidate tweets to consider when building the timeline.'),
        make_option('--update_users',
            action='store_true',
            dest='update_users',
            default=False,
            help='Whether to update user info when publishing their tweets (i.e., avatars).'),
        make_option('--size',
            action='store',
            type='int',
            dest='size',
            default=60,
            help='Whether to update user info when publishing their tweets (i.e., avatars).'),
        )

    def handle(self, *args, **options):
        SKIP_FIELDS = None #set(['n_tweets', 'diffusion', 'reply'])
        TIME_BUCKET_SIZE = options.get('time_bucket', 60)
        S = options.get('size', 100)
        HOURS = options.get('hours', 2)
        print(Tweet.objects.aggregate(maxdate=Max('datetime')))
        TIME_RANGE = [Tweet.objects.aggregate(maxdate=Max('datetime'))['maxdate'] - timedelta(hours=HOURS),
                      Tweet.objects.aggregate(maxdate=Max('datetime'))['maxdate']]
        TURNS = options.get('turns', 5)
        TIME_ZONE = pytz.timezone(options.get('time_zone', settings.TIME_ZONE))
        EXCLUDE_REPLIES = bool(options.get('exclude_replies', True))
        EXCLUDE_RETWEETS = bool(options.get('exclude_retweets', False))
        INFORMATIONAL_ONLY = bool(options.get('informational_only', True))
        POST_TO_TWITTER = bool(options.get('post_timeline', False))
        UPDATE_USERS = bool(options.get('update_users', False))
        POPULAR_ONLY = bool(options.get('popular', False))

        print(SKIP_FIELDS)
        print(TIME_BUCKET_SIZE)
        print(S)
        print(TIME_RANGE)
        print(TIME_ZONE)
        print(EXCLUDE_REPLIES, EXCLUDE_RETWEETS)
        print(INFORMATIONAL_ONLY)
        print(HOURS)
        print(POST_TO_TWITTER)
        print(UPDATE_USERS)

        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])
        api = tweepy.API(auth)

        generate_timeline(TIME_RANGE, skip_fields=SKIP_FIELDS, size=S,
                          sideline_turns=TURNS, time_bucket_size=TIME_BUCKET_SIZE,
                          time_zone=TIME_ZONE, twitter_api=api, exclude_replies=EXCLUDE_REPLIES,
                          exclude_retweets=EXCLUDE_RETWEETS, informational_only=INFORMATIONAL_ONLY,
                          update_users=UPDATE_USERS, post_to_twitter=POST_TO_TWITTER, retweeted_only=POPULAR_ONLY,
                          n_candidates=options.get('n_candidates', None))
