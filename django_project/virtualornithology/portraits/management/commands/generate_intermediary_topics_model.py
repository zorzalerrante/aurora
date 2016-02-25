from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime, timedelta
import os
from virtualornithology.birds.models import Tweet
from django.db.models import Max
from virtualornithology.portraits.intermediary import build_intermediary_topics_model
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--days',
            action='store',
            dest='days',
            default=1,
            type='int',
            help='Number of days in the past to look for candidate tweets.'),
        make_option('--num_topics',
            action='store',
            dest='num_topics',
            default=200,
            type='int',
            help='Number of latents topics for the LDA model.'),
        make_option('--percentile',
            action='store',
            dest='percentile',
            default=50.0,
            type='float',
            help='Percentile of centrality in the topic graph to determine intermediary topics.'),
        make_option('--min_followers',
            action='store',
            dest='min_followers',
            default=100,
            type='int',
            help='Minimum number of followers of recommended users.'),
        make_option('--min_tweets',
            action='store',
            dest='min_tweets',
            default=1000,
            type='int',
            help='Minimum number of tweets of recommended users.'),
    )

    def handle(self, *args, **options):
            path = settings.PORTRAIT_FOLDER
            now = datetime.now().strftime("%Y%m%d%H%M")
            max_date = Tweet.objects.aggregate(max_date=Max('datetime'))['max_date']
            time_range = [max_date - timedelta(days=options.get('days', 1)), max_date]
            print(time_range)
            tweets = Tweet.objects.filter(datetime__range=time_range).exclude(user__characterization__location_depth_0_id=None)
            tweets = tweets.filter(user__followers_count__gte=options.get('min_followers', 100))
            tweets = tweets.filter(user__statuses_count__gte=options.get('min_tweets', 1000))
            print(path)

            build_intermediary_topics_model(tweets, path=path, prefix=now,
                num_topics=options.get('num_topics', 200),
                percentile=options.get('percentile', 50.0))

            try:
                os.unlink('{0}/it-topics/current_dictionary.gensim'.format(path))
            except:
                pass
            try:
                os.unlink('{0}/it-topics/current_lda_model.gensim'.format(path))
            except:
                pass
            try:
                os.unlink('{0}/it-topics/current_topic_graph.nx'.format(path))
            except:
                pass
            try:
                os.unlink('{0}/it-topics/current_candidates.json.gz'.format(path))
            except:
                pass

            os.symlink('{0}/it-topics/{1}_dictionary.gensim'.format(path, now), '{0}/it-topics/current_dictionary.gensim'.format(path))
            os.symlink('{0}/it-topics/{1}_lda_model.gensim'.format(path, now), '{0}/it-topics/current_lda_model.gensim'.format(path))
            os.symlink('{0}/it-topics/{1}_topic_graph.nx'.format(path, now), '{0}/it-topics/current_topic_graph.nx'.format(path))
            os.symlink('{0}/it-topics/{1}_candidates.json.gz'.format(path, now), '{0}/it-topics/current_candidates.json.gz'.format(path))
