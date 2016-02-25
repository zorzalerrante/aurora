# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from optparse import make_option
import json
from django.db.models import Q
import time
import gensim
import networkx as nx
import gzip
import os
from datetime import datetime, timedelta
# our packages
from virtualornithology.portraits.models import Portrait
from virtualornithology.portraits.tasks import update_portrait, crawl_user_data
import tweepy
from tweepy import TweepError
from virtualornithology.birds.auxiliary import queryset_iterator


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--update_every',
            action='store',
            dest='update_every',
            default=1,
            type='int',
            help='Time in days to wait between updates.'),
        make_option('--wait_time',
            action='store',
            dest='wait_time',
            default=60,
            type='int',
            help='Time in seconds to wait between passes.'),
        make_option('--n_recommendations',
            action='store',
            dest='n_recommendations',
            default=50,
            type='int',
            help='Number of recommendations included in each portrait.'),
        make_option('--notify_after',
            action='store',
            dest='notify_after',
            default=3,
            type='int',
            help='Number of days to wait between updates.'),
        make_option('--update_only',
            action='store_true',
            dest='update_only',
            default=False,
            help='If used, do not crawl tweets, only recalculate them.'),
        make_option('--renew_user_data',
            action='store_true',
            dest='renew_user_data',
            default=False,
            help='Whether to update user profile meta-data.'),
        make_option('--notify',
            action='store_true',
            dest='notify',
            default=False,
            help='If used, when a portrait is updated the system sends a tweet to the target user with a link to the portrait.'),
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help='If used, process all portraits, not only those that need crawling.'),
        make_option('--skip_update_date',
            action='store_true',
            dest='skip_update_date',
            default=False,
            help='If used, the timestamp of the portrait is not updated.'),
        make_option('--n_times',
            action='store',
            type='int',
            dest='n_times',
            default=5,
            help='Times to run the crawler before exiting.'),
    )

    def load_models(self):
        now = datetime.now()
        self.rec_candidates = []

        if self.last_model_update is None or (now - self.last_model_update).days >= 1:
            print('loading model', now)
            model_path = '{0}/it-topics'.format(settings.PORTRAIT_FOLDER)
            lda_filename = os.readlink('{0}/current_lda_model.gensim'.format(model_path))

            self.lda_model = gensim.models.ldamulticore.LdaMulticore.load(lda_filename)
            self.topic_graph = nx.read_gpickle('{0}/current_topic_graph.nx'.format(model_path))

            with gzip.open('{0}/current_candidates.json.gz'.format(model_path), 'rt') as f:
                self.rec_candidates = json.load(f)
                print('loaded', len(self.rec_candidates), 'candidates')

            self.last_model_update = datetime.now()

    def handle(self, *args, **options):
        path = '{0}/users'.format(settings.PORTRAIT_FOLDER)
        self.last_model_update = None
        update_only = options.get('update_only', False)
        n_recommendations = options.get('n_recommendations', 15)
        renew_user_data = options.get('renew_user_data', False)
        write_update_date = not options.get('skip_update_date', False)
        update_every = int(options.get('update_every', 7))

        try:
            self.load_models()
        except FileNotFoundError:
            self.lda_model = None
            self.topic_graph = None
            self.rec_candidates = []
            print('LDA models and Topic Graph were not loaded because they did not exist.')

        api_keys = settings.TWITTER_USER_KEYS
        auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])
        api = tweepy.API(auth, wait_on_rate_limit=True)

        for i in range(0, options.get('n_times', 5)):

            yesterday = timezone.now() - timedelta(days=update_every)
            # TODO: we should update only active portraits, and do not bother about those without user activity
            #active_date = timezone.now() - timedelta(days=14)

            if not options.get('all', False):
                new_portraits = Portrait.objects.filter(active=True).filter(
                    Q(portrait_content=None)|
                    Q(last_update_date__lte=yesterday)
                )
            else:
                new_portraits = Portrait.objects.filter(active=True)

            portrait_count = new_portraits.count()
            print('scheduled portraits', portrait_count)

            if not portrait_count:
                time.sleep(options.get('wait_time', 60))
                continue

            for portrait in queryset_iterator(new_portraits, chunksize=100):
                is_new_portrait = portrait.portrait_content is None

                print('user', portrait.auth_screen_name)
                print('new', is_new_portrait)
                print('date', portrait.last_tweet_date)
                print('valid content', portrait.portrait_content is not None)
                print('write update date', write_update_date)

                if not update_only:
                    print('crawling data')
                    try:
                        crawl_user_data(portrait, path)
                    except TweepError as err:
                        print('ERROR', err)
                        portrait.active = False
                        portrait.save()
                        continue
                    except Exception as err:
                        print('ERROR', err)
                        continue

                try:
                    update_portrait(portrait, path, self.lda_model, self.topic_graph, self.rec_candidates,
                                    n_recommendations=n_recommendations, update_users=renew_user_data,
                                    write_update_date=write_update_date, update_api=api,
                                    notify_users=options.get('notify', False),
                                    update_days=options.get('notify_after', 7))
                except ValueError as err:
                    print('ERROR', err)
                    continue
            #print 'sleeping...'
            time.sleep(options.get('wait_time', 60))
