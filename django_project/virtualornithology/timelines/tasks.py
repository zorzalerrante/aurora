# -*- coding: utf-8 -*-
from .filtering import TimelineFilter
from virtualornithology.places.models import Location
from virtualornithology.birds.models import Tweet, User
from virtualornithology.analysis.characterizer import Characterizer
from .models import Timeline
from django.core import serializers

try:
    import ujson as json
except ImportError:
    import json

from cytoolz import pluck
from scipy.stats import gmean
from cytoolz.dicttoolz import valfilter
from django.db.models import Q
import time
from django.conf import settings
import tweepy
import random
import pytz
from django.core.urlresolvers import reverse


def _timeline_queryset(time_range, location_depth=1, min_length=50, exclude_replies=True, informational_only=False,
                       exclude_retweets=False, skip_sensitive_content=True, retweeted_only=True):

    tweets = Tweet.objects.filter(datetime__range=time_range).exclude(
        **{'user__characterization__location_depth_{0}'.format(location_depth): None})

    if exclude_replies:
        tweets = tweets.exclude(characterization__is_reply=True)

    if exclude_retweets:
        tweets = tweets.exclude(characterization__manual_rt=True)

    if informational_only:
        tweets = tweets.filter(Q(characterization__count_links__gt=0)|Q(characterization__count_media__gt=0))

    if min_length is not None and min_length > 0:
        tweets = tweets.exclude(characterization__length__lt=min_length)

    if skip_sensitive_content:
        tweets = tweets.exclude(possibly_sensitive=True)

    if retweeted_only:
        tweets = tweets.filter(Q(characterization__count_rts__gt=0)|Q(retweet_count__gt=0))

    # no spam please
    tweets = tweets.exclude(characterization__count_mentions__gt=2)
    tweets = tweets.exclude(characterization__count_hashtags__gt=2)

    print(tweets.count())

    return tweets


def generate_timeline(time_range, save_to_db=True, tweets=None, skip_fields=None, size=40, sideline_turns=5,
                      time_bucket_size=30, location_depth=1, time_zone=None, twitter_api=None,
                      min_length=50, exclude_replies=True, informational_only=False, exclude_retweets=False,
                      post_update=True, retweet_tweeps=True, skip_sensitive_content=True,
                      retweeted_only=False, post_to_twitter=False, update_users=True, shout_score=0.5,
                      n_candidates=None, target_entropy=0.99):

    if n_candidates is not None and n_candidates <= 0:
        n_candidates = None

    # generate filtered set
    characterizer = Characterizer()

    if not time_zone:
        time_zone = pytz.timezone(settings.TIME_ZONE)

    locations = list(Location.objects.filter(depth=location_depth))
    location_pks = [loc.pk for loc in locations]
    location_populations = dict([(loc.pk, loc.population) for loc in locations])

    if not time_zone:
        time_zone = pytz.timezone(settings.TIME_ZONE)

    if tweets is None:
        tweets = _timeline_queryset(time_range, location_depth=location_depth, min_length=min_length, exclude_replies=exclude_replies,
                                informational_only=informational_only, exclude_retweets=exclude_retweets,
                                skip_sensitive_content=skip_sensitive_content, retweeted_only=retweeted_only)

    feature_keys = ['pk', 'text', 'favourite_count', 'retweet_count',
                        'user__screen_name', 'datetime', 'user__name', 'user__profile_image_url', 'internal_id',
                        'user__internal_id', 'user__friends_count', 'user__followers_count',
                        'user__statuses_count', 'characterization__count_rts',
                        'characterization__manual_rt', 'characterization__is_reply']

    if location_depth > 0:
        feature_keys.append('user__characterization__location_depth_{0}'.format(location_depth))

    tweet_features = list(tweets.values(*feature_keys))

    if not tweet_features or len(tweet_features) < size:
        print('ERROR, not enough tweets', len(tweet_features))
        return None

    if location_depth > 0:
        pick_strategy, approve_fn = TimelineFilter.select_tweet_and_sideline(TimelineFilter.select_popular_bucketed, location_pks, turns=sideline_turns)
        start_strategy = pick_strategy
    else:
        pick_strategy = TimelineFilter.select_popular_bucketed
        start_strategy = TimelineFilter.starting_tweet
        approve_fn = None

        if skip_fields is None:
            skip_fields = {'geography'}
        else:
            skip_fields.add('geography')

    generator = TimelineFilter(characterizer,
                               skip_fields=skip_fields,
                               min_date=time_range[0],
                               max_entropy_percentile=100.0,
                               time_bucket_size=time_bucket_size,
                               start_strategy=start_strategy,
                               pick_strategy=pick_strategy,
                               approve_tweet_fn=approve_fn,
                               n_candidates=n_candidates,
                               target_entropy=target_entropy)

    for t in tweet_features:
        if location_depth > 0:
            t['geography'] = int(t['user__characterization__location_depth_{0}'.format(location_depth)])
        t['popularity'] = 2.0 * t['characterization__count_rts'] + t['retweet_count'] + 0.5 * t['favourite_count']
        generator.prepare_tweet(t)

    tweet_features = filter(lambda x: x['__shout_score__'] < shout_score, tweet_features)
    tweet_features = sorted(tweet_features, key=lambda x: x['buckets']['popularity'], reverse=True)
    print('N features', len(tweet_features))

    for i in range(0, min([size, len(tweet_features)])):
        generator(tweet_features)

    # estimate data
    tweet_pks = list(pluck('pk', generator))
    tl_tweets = Tweet.objects.in_bulk(tweet_pks)
    to_serialize = [tl_tweets[pk] for pk in tweet_pks]
    popularity = list(pluck('popularity', generator))

    html = []
    media = []
    sources = []

    rted_user_pks = set()

    for t in to_serialize:
        if t.media.exists():
            media.append(json.loads(serializers.serialize("json", t.media.all())))
        else:
            media.append(None)

        if t.rt_instance_tweet.exists():
            rt = t.rt_instance_tweet.all()[0].source_tweet
            rt_serialized = json.loads(serializers.serialize("json", [rt]))[0]
            rted_user_pks.add(rt_serialized['fields']['user'])
            # NOTE: this user is not updated. need to update it at some point.
            #rt_serialized['fields']['user'] = json.loads(serializers.serialize("json", [User.objects.get(pk=pk)]))[0]
            html.append(rt.beautify_html())
            sources.append(rt_serialized)
        else:
            html.append(t.beautify_html())
            sources.append(None)

    if not twitter_api or not update_users:
        print('not updating users')
        users = json.loads(serializers.serialize("json", [t.user for t in to_serialize]))
    else:
        print('updating user profiles')
        user_pks = [t.user_id for t in to_serialize]
        user_pks.extend(rted_user_pks)
        user_ids = User.objects.filter(pk__in=user_pks).values_list('internal_id', flat=True)
        tl_user_data = twitter_api.lookup_users(user_ids=user_ids)

        for tl_user in tl_user_data:
            user, created = User.import_json(valfilter(lambda x: x, tl_user._json))

        user_dict = User.objects.in_bulk([t.user_id for t in to_serialize])
        users = json.loads(serializers.serialize("json", [user_dict[t.user_id] for t in to_serialize]))

    for t, source in zip(to_serialize, sources):
        if source is not None:
            source['fields']['user'] = json.loads(serializers.serialize("json", [User.objects.get(pk=source['fields']['user'])]))[0]

    weight = []

    if location_depth > 0:
        max_population = 1.0 * max([loc.population for loc in locations])
    else:
        max_population = None

    for t in generator:
        if location_depth > 0:
            w = gmean([t['popularity'] + 1.0,
                   max_population / location_populations[t['geography']],
                   t['user__followers_count'] + 1.0,
                   t['user__friends_count'] + 1.0])
        else:
            w = gmean([t['popularity'] + 1.0,
                   t['user__followers_count'] + 1.0,
                   t['user__friends_count'] + 1.0])
        weight.append(w)

    hour_norm = 1.0 / (60.0 * 60.0)
    kwargs = {
        'user': users,
        'html': html,
        'popularity': popularity,
        'weight': weight,
        'recency': [(time_range[1] - t.datetime).total_seconds() * hour_norm for t in to_serialize],
        'media': media,
        'source_user': sources
    }

    if location_depth > 0:
        kwargs['geolocation'] = list(pluck('geography', generator))

    if time_zone:
        kwargs['datetime'] = [t.datetime.astimezone(time_zone).isoformat() for t in to_serialize]

    # metadata
    metadata = {
        'locations': json.loads(serializers.serialize("json", locations)),
    }

    if not save_to_db:
        return {'tweets': to_serialize, 'metadata': kwargs}

    # save filtered set
    tl = Timeline.from_tweets(to_serialize, metadata, **kwargs)

    if twitter_api and to_serialize:
        tl_url = u'http://auroratwittera.cl{0}'.format(reverse('timelines:timeline-home'))

        if len(users) > 3:
            top_users = random.sample([u'@{0}'.format(t['fields']['screen_name']) for t in users], 3)
        else:
            top_users = ['@{0}'.format(t['fields']['screen_name']) for t in users]

        status_1 = 'Nvo. resumen informativo en {0} con tweets de {1}'.format(tl_url, u' '.join(top_users))
        print(repr(status_1))
        if post_update and post_to_twitter:
            try:
                twitter_api.update_status(status_1)
                time.sleep(30)
            except tweepy.error.TweepError:
                pass

        if rted_user_pks:
            try:
                top_rted = random.sample([u'@{0}'.format(t['fields']['user']['fields']['screen_name']) for t in sources if t], min([3, len(rted_user_pks)]))
                status_2 = 'Nvo. resumen informativo en {0} con RTs de {1}'.format(tl_url, u' '.join(top_rted))
                print(repr(status_2))
                if post_update and post_to_twitter:
                    try:
                        twitter_api.update_status(status_2)
                        time.sleep(30)
                    except tweepy.error.TweepError:
                        pass
            except ValueError:
                pass

        if retweet_tweeps:
            for w, t in sorted(zip(kwargs['weight'], to_serialize), reverse=True)[0:size - 1]:
                if not post_to_twitter:
                    print('retweet', t.internal_id)
                else:
                    try:
                        print('retweet', t.internal_id)
                        twitter_api.retweet(t.internal_id)
                        time.sleep(60)
                    except tweepy.error.TweepError as e:
                        print([e])

    return tl
