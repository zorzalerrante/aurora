# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import datetime
from virtualornithology.birds.models import User, Tweet
from django.db.models import Count
from cytoolz import partition_all
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--days',
            action='store',
            dest='days',
            default=7,
            type='int',
            help='Number of days to preserve.'),
        make_option('--step',
            action='store',
            dest='step',
            default=10000,
            type='int',
            help='Number of tweets to delete per iteration.'),
    )

    def handle(self, *args, **options):
        step = options.get('step', 10000)

        limit_date = datetime.datetime.now() - datetime.timedelta(days=options.get('days', 7))
        print(limit_date)

        queryset = Tweet.objects.filter(datetime__lt=limit_date)
        while queryset.exists():
            tweet_ids = [t.pk for t in queryset[:step]]
            Tweet.objects.filter(pk__in=tweet_ids).delete()
            print('deleted', len(tweet_ids))

        user_ids = User.objects.annotate(Count('author')).filter(author__count=0).values_list('pk', flat=True)
        for pks in partition_all(step, user_ids):
            User.objects.filter(pk__in=pks).delete()
            print('deleted', len(pks), 'users')
