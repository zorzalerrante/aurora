import regex
import gzip
import logging

try:
    import ujson as json
except ImportError:
    import json

from django.conf import settings
from django.db import transaction
from django.db.models import F
from cytoolz import pluck, valfilter, groupby, memoize
from itertools import chain
from urllib.parse import urlparse
from collections import defaultdict, Counter
from langid import langid
from virtualornithology.birds.auxiliary import load_list_from_file, normalize_str
from virtualornithology.birds.models import User, Tweet, ReTweet, Url, Keyword, Media
from .models import UserFeatures, TweetFeatures
from .characterizer import Characterizer



class Importer(object):
    def __init__(self):
        self.accepted_languages = settings.TWITTER_ACCEPTED_LANGUAGES

        print(self.accepted_languages)

        self.step = settings.CHARACTERIZATION_STEP
        self.reject_unknown_locations = settings.REJECT_UNKNOWN_LOCATIONS
        self.characterizer = Characterizer()

        discard_locations_file = settings.TWITTER_DISCARD_LOCATIONS

        if discard_locations_file is not None:
            self.discard_locations = set(load_list_from_file(discard_locations_file, normalize_text=True))
            self.discard_locations = [self.characterizer.prepare_location_name(l) for l in self.discard_locations]
            logging.info(u'discard locations: {0}'.format(self.discard_locations))
        else:
            self.discard_locations = None

        discard_keywords_file = settings.TWITTER_DISCARD_KEYWORDS

        if discard_keywords_file is not None:
            self.discard_keywords = set(load_list_from_file(discard_keywords_file, normalize_text=True))
            self.discard_hashtags = set(filter(lambda x: x[0] == '#', self.discard_keywords))
            self.discard_mentions = set(filter(lambda x: x[0] == '@', self.discard_keywords))
            logging.info('discard hashtags: {0}'.format(self.discard_hashtags))
            logging.info('discard mentions: {0}'.format(self.discard_mentions))
            logging.info('discard keywords: {0}'.format(self.discard_keywords))
        else:
            self.discard_hashtags = None
            self.discard_mentions = None
            self.discard_keywords = None

        discard_urls_file = settings.TWITTER_DISCARD_URLS

        if discard_urls_file is not None:
            self.discard_urls = set(load_list_from_file(discard_urls_file, normalize_text=True))
            logging.info('discard URLs: {0}'.format(self.discard_urls))
        else:
            self.discard_urls = None

        # mysql doesn't support 4 bytes utf-8 characters
        # source: http://stackoverflow.com/a/3220210
        self.re_pattern = regex.compile(r'[^\u0000-\uD7FF\uE000-\uFFFF]', regex.UNICODE)

        with open('{0}/twitter_time_zones.csv'.format(settings.PROJECT_PATH), 'rt', encoding='utf-8') as f:
            self.zone_dict = {}
            # Santiago => (GMT-04:00)
            for l in f:
                parts = l.strip().split(',', 2)
                self.zone_dict[parts[1]] = parts[0]

        with open('{0}/allowed_time_zones.txt'.format(settings.PROJECT_PATH), 'rt', encoding='utf-8') as f:
            self.allowed_timezones = set(f.read().split('\n'))
            # self.allowed_timezones = {'(GMT-03:00)', '(GMT-04:00)'}

        with open('{0}/discard_time_zones.txt'.format(settings.PROJECT_PATH), 'rt', encoding='utf-8') as f:
            self.discarded_timezones = set(f.read().split('\n'))
            # {'Brazilia', 'Brasilia', 'Georgetown', 'Greenland', 'Atlantic Time (Canada)'}

        with open('{0}/allowed_sources.txt'.format(settings.PROJECT_PATH), 'rt', encoding='utf-8') as f:
            self.allowed_sources = set(f.read().split('\n'))

        self.discarded_sources = Counter()
        self.reject_reasons = Counter()

        # we remember.
        self.total_tweet_count = 0
        self.saved_tweets = set()

    def is_present(self, tweet):
        return tweet['id'] in self.saved_tweets

    @memoize
    def is_valid_timezone(self, time_zone_name):
        if time_zone_name in self.allowed_timezones:
            return True

        if time_zone_name not in self.zone_dict:
            logging.info('Rejected! Unknown time zone', time_zone_name)
            return False

        if self.zone_dict[time_zone_name] not in self.allowed_timezones or time_zone_name in self.discarded_timezones:
            logging.info('Rejected! Discarded time zone', time_zone_name)
            return False

        return True

    def accept_tweet(self, tweet, check_repeated=False, check_sources=True, check_time_zone=True):
        if not 'text' in tweet:
            logging.info('Invalid: tweet does not containt text! {0}'.format(tweet))
            return False

        if self.is_present(tweet):
            if check_repeated:
                self.reject_reasons['repeated'] += 1
                return False
            # since we do not check repeats, and it is available, we accept it immediately.
            # and, since it was repeated, we do not increase the tweet count
            return True

        if check_sources and tweet['source'] not in self.allowed_sources:
            logging.info('rejected! source: {0}'.format(tweet['source']))
            self.reject_reasons['blacklisted_source'] += 1
            self.discarded_sources[tweet['source']] += 1
            return False

        time_zone = tweet['user'].get('time_zone', None)
        if check_time_zone and not self.is_valid_timezone(time_zone):
            self.reject_reasons['time_zone'] += 1
            return False

        if 'retweeted_status' in tweet and tweet['retweeted_status']:
            # we don't check sources for retweets, nor if it was added
            accepted = self.accept_tweet(tweet['retweeted_status'], check_repeated=False, check_sources=False, check_time_zone=False)
            if not accepted:
                self.reject_reasons['rejected_rt'] += 1
                logging.info(u'Rejected RT!')
                return False

        if 'quoted_status' in tweet and tweet['quoted_status']:
            # we don't check sources for quotes, nor if it was added
            accepted = self.accept_tweet(tweet['quoted_status'], check_repeated=False, check_sources=False, check_time_zone=False)
            if not accepted:
                self.reject_reasons['rejected_quote'] += 1
                logging.info(u'Rejected Quote!')
                return False

        if self.accepted_languages:
            lang = tweet.get('lang', 'UNK')

            if not lang in self.accepted_languages:
                logging.info('Rejected: not in the language expected! {0}, {1}'.format(lang, tweet['text']))
                self.reject_reasons['language'] += 1
                return False

        if self.discard_locations:
            if tweet['user']['location']:
                loc_name = self.characterizer.prepare_location_name(tweet['user']['location'])
                if loc_name in self.discard_locations:
                    logging.info('Rejected location: {0}'.format(loc_name))
                    self.reject_reasons['location'] += 1
                    return False

        if self.reject_unknown_locations:
            if not tweet['user']['__geolocation__']:
                logging.info('Rejected user - not geolocated: {0}'.format(tweet['user']['location']))
                self.reject_reasons['location'] += 1
                return False

        if self.discard_mentions:
            screen_name = u'@{0}'.format(tweet['user']['screen_name'].lower())
            if screen_name in self.discard_mentions:
                logging.info('Rejected! Blacklisted user: {0}'.format(screen_name))
                self.reject_reasons['blacklisted_user'] += 1
                return False

        if 'entities' in tweet:
            if self.discard_hashtags:
                if 'hashtags' in tweet['entities'] and tweet['entities']['hashtags']:
                    hashtags = set(['#{0}'.format(normalize_str(h['text'])) for h in tweet['entities']['hashtags']])
                    if hashtags & self.discard_hashtags:
                        logging.info(u'Rejected! Hashtags: {0}'.format(hashtags))
                        self.reject_reasons['blacklisted_hashtag'] += 1
                        return False

                if 'user_mentions' in tweet['entities'] and tweet['entities']['user_mentions']:
                    mentions = set(['@{0}'.format(normalize_str(h['screen_name'])) for h in tweet['entities']['user_mentions']])
                    if mentions & self.discard_mentions:
                        logging.info('Rejected! Mentions: {0}'.format(mentions))
                        self.reject_reasons['blacklisted_mention'] += 1
                        return False

            if self.discard_urls:
                if tweet['__domains__']:
                    if tweet['__domains__'] & self.discard_urls:
                        logging.info('Rejected! URLs: {0}'.format(tweet['__domains__']))
                        self.reject_reasons['blacklisted_domain'] += 1
                        return False

        if 'keywords' in tweet:
            kws = set(tweet['keywords'])
            if self.discard_keywords:
                if kws & self.discard_keywords:
                    logging.info('Rejected! Keywords: {0}'.format(kws))
                    return False

        self.total_tweet_count += 1
        self.saved_tweets.add(tweet['id'])

        return True

    def pre_func(self, tweet):
        if 'text' in tweet:
            tweet['text'] = self.re_pattern.sub('', tweet['text'])

            tweet['user']['profile_image_url'] = tweet['user']['profile_image_url'][:255]
            tweet['user']['__geolocation__'] = self.characterizer.get_geolocation(tweet['user']['location'])

            if not 'lang' in tweet:
                tweet['lang'] = detect_language(tweet['text'])

            tweet['keywords'] = self.characterizer.characterize_text(tweet['text'])['keywords']

            if 'entities' in tweet:
                tweet['__domains__'] = set()

                if 'urls' in tweet['entities']:
                    for url in tweet['entities']['urls']:
                        expanded = url['expanded_url']
                        if not expanded:
                            expanded = url['url']
                            url['expanded_url'] = expanded
                        url['expanded_url'] = url['expanded_url'][:255]
                        domain = urlparse(expanded).netloc
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        url['domain'] = domain
                        tweet['__domains__'].add(domain)
            else:
                tweet['__domains__'] = None

            if 'retweeted_status' in tweet:
                self.pre_func(tweet['retweeted_status'])

            if 'quoted_status' in tweet:
                self.pre_func(tweet['quoted_status'])
        return tweet


    def post_func(self, users, tweets):
        #self.characterizer.batch_characterize(x)
        ucs = [self.characterizer.characterize_user(u, extend_with_user_info=False) for u in users]
        tcs = [self.characterizer.characterize_tweet(t, extend_with_tweet_info=False) for t in tweets]

        logging.debug('User Characterizations: {0}'.format(len(ucs)))
        logging.debug('Tweet Characterizations: {0}'.format(len(tcs)))

        save_user_characterizations(self.characterizer, ucs)
        save_tweet_characterizations(self.characterizer, tcs)


    def __call__(self, filename):
        """
        filter_func is applied to single tweet jsons
        post_func is applied to the whole list of imported pairs (user, tweet)
        """

        pending = []
        self.total_tweet_count = 0

        with gzip.open(filename, 'rt') as f:
            logging.info('Filename: {0} (step={1})'.format(filename, self.step))

            for l in f:
                l = l.strip()

                if not l:
                    continue

                try:
                    json_data = json.loads(l)
                except ValueError as e:
                    logging.debug('Value Error: {0}'.format(e))
                    continue

                pending.append(json_data)

                if len(pending) >= self.step:
                    self.batch_import(pending)
                    pending = []

        if pending:
            self.batch_import(pending)

        logging.info('Filename {0} processed! {1} tweets accepted.'.format(filename, self.total_tweet_count))

    @classmethod
    def _batch_import(base_class, cls, elements, fn):
        logging.debug('Trying to import {1} from {0} elements'.format(len(elements), cls))
        internal_ids = set(pluck('id_str', fn(elements)))

        existing_users = cls.objects.filter(internal_id__in=internal_ids)
        existing_ids = set([u.internal_id for u in existing_users])
        user_pks = dict([(u.internal_id, u.pk) for u in existing_users])
        new_ids = internal_ids - existing_ids

        logging.debug('Existing IDs: {0}'.format(len(existing_ids)))
        logging.debug('New IDs: {0}'.format(len(new_ids)))

        added_keys = set()
        new_elements = []
        for element in fn(elements):
            if element['id_str'] in user_pks:
                element['__pk__'] = user_pks[element['id_str']]
                element['__created__'] = False
            else:
                if not element['id_str'] in added_keys:
                    user_model = cls()
                    user_model.copy_json(valfilter(lambda x: x, element))
                    new_elements.append(user_model)
                element['__created__'] = True
                element['__pk__'] = None
                added_keys.add(element['id_str'])

        cls.objects.bulk_create(new_elements)

        new_models = list(cls.objects.filter(internal_id__in=new_ids))
        logging.debug('New IDs created successfully: {0}'.format(len(new_models)))
        new_pks = dict([(u.internal_id, u.pk) for u in new_models])
        for element in fn(elements):
            if element['id_str'] in new_pks:
                element['__pk__'] = new_pks[element['id_str']]

        return new_models

    @classmethod
    def _batch_import_retweets(cls, tweets, retweet_key='retweeted_status'):
        rts = []

        user_map = User.objects.in_bulk(pluck('__pk__', pluck('user', tweets)))

        tweet_ids = list(pluck('__pk__', tweets))
        tweet_ids.extend(pluck('__pk__', pluck(retweet_key, tweets)))
        tweet_map = Tweet.objects.in_bulk(tweet_ids)

        rt_counts = defaultdict(int)

        for current in tweets:
            rts.append(ReTweet(user=user_map[current['user']['__pk__']],
                                      tweet_instance=tweet_map[current['__pk__']],
                                      source_tweet=tweet_map[current[retweet_key]['__pk__']],
                                      datetime=tweet_map[current['__pk__']].datetime))

            rt_counts[current['__pk__']] += 1

        ReTweet.objects.bulk_create(rts)
        logging.debug('RT Increments: {0}'.format(rt_counts))
        increment_rt_counts(rt_counts)

    @classmethod
    def _batch_import_keywords(cls, tweets):
        kws = set()
        for kw in pluck('keywords', tweets):
            kws.update(kw)

        keyword_map = dict(map(lambda x: (x.name, x), Keyword.retrieve(kws)))
        tweet_map = Tweet.objects.in_bulk(pluck('__pk__', tweets))
        logging.debug('Keywords: {0} in {1} tweets'.format(len(keyword_map), len(tweet_map)))

        for tweet in tweets:
            tweet_kws = [keyword_map[k] for k in tweet['keywords']]
            tweet_map[tweet['__pk__']].keywords = tweet_kws

    @classmethod
    @transaction.atomic
    def _save_urls(cls, urls):
        for u in urls:
            expanded = u['expanded_url']
            short = u['url']
            display = u.get('display_url', u['domain'])
            defaults = {'short': short, 'domain': u['domain'], 'display_url': display}
            Url.objects.get_or_create(url=expanded, defaults=defaults)

    @classmethod
    @transaction.atomic
    def _save_media_urls(cls, media_urls):
        for u in media_urls:
            Media.objects.get_or_create(internal_id=u['id_str'], defaults={
                 'type': u['type'],
                 'media_url': u['media_url'][:255],
                 'display_url': u['display_url'][:255],
                 'expanded_url': u['expanded_url'][:255],
                 'url': u['url'][:255],
                 'sizes': json.dumps(u['sizes'])
            })

    @classmethod
    def _batch_import_urls(cls, tweets):
        with_urls = [t for t in tweets if 'entities' in t and 'urls' in t['entities']]
        urls = list(chain(*[t['entities']['urls'] for t in with_urls]))
        logging.debug('URLs: {0} in {1} tweets'.format(len(urls), len(with_urls)))
        cls._save_urls(urls)
        url_map = dict(map(lambda x: (x.url, x), Url.objects.filter(url__in=pluck('expanded_url', urls))))

        with_media_urls = [t for t in tweets if 'entities' in t and 'media' in t['entities'] and t['entities']['media']]
        media_urls = list(chain(*[t['entities']['media'] for t in with_media_urls]))
        logging.debug('Media URLs: {0} in {1} tweets'.format(len(media_urls), len(with_media_urls)))
        cls._save_media_urls(media_urls)
        media_url_map = dict(map(lambda x: (x.internal_id, x), Media.objects.filter(internal_id__in=pluck('id_str', media_urls))))

        tweet_map = Tweet.objects.in_bulk(pluck('__pk__', tweets))

        logging.debug('URLs saved: {0}'.format(len(url_map)))
        logging.debug('Media URLs saved: {0}'.format(len(media_url_map)))

        for tweet in tweets:
            tweet_urls = [url_map[url['expanded_url']] for url in tweet['entities']['urls'] if url['expanded_url'] in url_map]

            if tweet_urls:
                tweet_map[tweet['__pk__']].links = tweet_urls

            if 'media' in tweet['entities'] and tweet['entities']['media']:
                print(tweet['entities']['media'])
                tweet_media_urls = [media_url_map[media_url['id_str']] for media_url in tweet['entities']['media'] if media_url['id_str'] in media_url_map]

                if tweet_media_urls:
                    tweet_map[tweet['__pk__']].media = tweet_media_urls

    def batch_import(self, tweets, parse_json=False):
        logging.info('Received {0} tweets'.format(len(tweets)))
        tweets = list(filter(self.accept_tweet, map(self.pre_func, tweets)))
        logging.info('After Filtering: {0} tweets'.format(len(tweets)))

        user_fn = lambda x: pluck('user', x)
        tweet_fn = lambda x: x

        retweet_sources = [t['retweeted_status'] for t in tweets if 'retweeted_status' in t]
        quote_sources = [t['quoted_status'] for t in tweets if 'quoted_status' in t]
        imported_users = Importer._batch_import(User, tweets, user_fn)
        imported_users.extend(Importer._batch_import(User, retweet_sources, user_fn))
        imported_users.extend(Importer._batch_import(User, quote_sources, user_fn))

        imported = Importer._batch_import(Tweet, tweets, tweet_fn)
        imported.extend(Importer._batch_import(Tweet, [t['retweeted_status'] for t in tweets if 'retweeted_status' in t], tweet_fn))
        imported.extend(Importer._batch_import(Tweet, [t['quoted_status'] for t in tweets if 'quoted_status' in t], tweet_fn))

        Importer._batch_import_retweets(list(filter(lambda x: 'retweeted_status' in x, tweets)))
        Importer._batch_import_retweets(list(filter(lambda x: 'quoted_status' in x, tweets)), retweet_key='quoted_status')

        Importer._batch_import_keywords(list(filter(lambda x: x['__created__'], tweets)))
        Importer._batch_import_keywords(list(filter(lambda x: x['__created__'], retweet_sources)))
        Importer._batch_import_keywords(list(filter(lambda x: x['__created__'], quote_sources)))

        Importer._batch_import_urls(list(filter(lambda x: x['__created__'], tweets)))
        Importer._batch_import_urls(list(filter(lambda x: x['__created__'], retweet_sources)))
        Importer._batch_import_urls(list(filter(lambda x: x['__created__'], quote_sources)))

        self.post_func(imported_users, imported)

        logging.debug('Imported Tweets: {0}'.format(len(imported)))

        return imported_users, imported


def detect_language(text):
    classif = langid.classify(text)
    if not classif:
        return 'UNK'

    if classif[1] > 0.9:
        return classif[0]

    return 'UNK'


def increment_rt_counts(tweet_pks):
    """
    :param tweet_pks: dictionary {tweet_pk: rt_count}
    :return:
    """
    items = sorted(tweet_pks.items(), key=lambda x: x[1], reverse=True)
    grouped = groupby(lambda x: x[1], items)

    for incr, pairs in grouped.items():
        if incr > 0:
            pks = pluck(0, pairs)
            TweetFeatures.objects.filter(tweet_id__in=pks).update(count_rts=F('count_rts') + incr)


_location_parents_cache = {}


def get_location_parent(location):
    global _location_parents_cache

    if not location.pk in _location_parents_cache:
        _location_parents_cache[location.pk] = location.parent

    return _location_parents_cache[location.pk]


def save_user_characterizations(characterizer, chars):
    new_features = []
    for i, char in enumerate(chars, start=1):
        user = char['model']

        try:
            UserFeatures.objects.get(user=user)
            char['saved'] = False
            continue
        except UserFeatures.DoesNotExist:
            pass

        char['saved'] = True

        # first: add the basic stuff.
        defaults = {
            'user_id': user.pk,
            'first_name': char['first_name'],
            'last_name': char['last_name'],
            'domain': char['domain'],
            'friends_followers_ratio': char['friends_followers_ratio'],
            'datetime': user.created_at,
        }

        if user.location and characterizer._do_geo_location:
            location = characterizer.get_geolocation(user.location)

            if location:
                for i in range(location.depth, -1, -1):
                    defaults['location_depth_{0}'.format(location.depth)] = location
                    location = get_location_parent(location)

        new_features.append(UserFeatures(**defaults))

    UserFeatures.objects.bulk_create(new_features)


def save_tweet_characterizations(characterizer, chars):
    new_features = []
    for i, char in enumerate(chars, start=1):
        try:
            uc = UserFeatures.objects.get(user_id=char['user_id'])
        except UserFeatures.DoesNotExist:
            char['saved'] = False
            continue

        try:
            sc = TweetFeatures.objects.get(tweet_id=char['tweet_id'])
            char['saved'] = False
            continue
        except TweetFeatures.DoesNotExist:
            pass

        char['saved'] = True

        # first: add the basic stuff.
        defaults = {
            'tweet_id': char['tweet_id'],
            'count_mentions': len(char['mentions']),
            'count_hashtags': len(char['hashtags']),
            'count_keywords': len(char['keywords']),
            'datetime': char['datetime'],
            'length': len(char['text']),
            'source_user_id': uc.pk,
            'count_links': len(char['links']),
            'count_media': char['count_media'],
            'manual_rt': char['manual_rt'],
            'count_rts': 0
        }

        # second: the interaction stuff.
        defaults['is_reply'] = char['is_reply']

        # for now we consider only direct messages, not broadcasts to multiple users :(
        if defaults['count_mentions'] == 1:
            try:

                screen_name = char['mentions'].pop()
                mentioned = User.objects.get(screen_name=screen_name)

                try:
                    mentioned_uc = UserFeatures.objects.get(user=mentioned)
                    defaults['target_user'] = mentioned_uc
                except UserFeatures.DoesNotExist:
                    pass

            except User.MultipleObjectsReturned:
                pass

            except User.DoesNotExist:
                pass

        new_features.append(TweetFeatures(**defaults))
        char['saved'] = True

    TweetFeatures.objects.bulk_create(new_features)
