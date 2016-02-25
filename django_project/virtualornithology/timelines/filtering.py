from collections import Counter
import numpy as np
import random
import math
import difflib


class TimelineFilter(object):
    def __init__(self, characterizer, skip_fields=None, max_entropy_percentile=100.0, time_bucket_size=10,
                 start_strategy=None, pick_strategy=None, approve_tweet_fn=None,
                 min_date=None, allow_repeated_users=False, allow_repeated_urls=False, similarity_threshold=0.85,
                 n_candidates=None, target_entropy=0.99):
        self.characterizer = characterizer
        self.skip_fields = skip_fields
        self.time_bucket_size = time_bucket_size
        self.max_entropy_percentile = max_entropy_percentile
        self.min_date = min_date
        self.allow_repeated_users = allow_repeated_users
        self.allow_repeated_urls = allow_repeated_urls
        self.similarity_threshold = similarity_threshold

        if start_strategy is None:
            self.start_strategy = TimelineFilter.starting_tweet
        else:
            self.start_strategy = start_strategy

        if pick_strategy is None:
            self.pick_strategy = TimelineFilter.select_tweet
        else:
            self.pick_strategy = pick_strategy

        if approve_tweet_fn is None:
            self.approve_tweet_fn = lambda x: True
        else:
            self.approve_tweet_fn = approve_tweet_fn


        if skip_fields is not None:
            self.feature_keys = [p for p in ['popularity', 'followers', 'friends', 'n_tweets', 'hub', 'diffusion', 'reply', 'geography', 'time', 'url', 'topics']
                                if p not in skip_fields]
        else:
            self.feature_keys = ['popularity', 'followers', 'friends', 'n_tweets', 'hub', 'diffusion', 'reply', 'geography', 'time', 'url', 'topics']

        self.timeline = []
        self.timeline_ids = set()
        self.user_ids = set()
        self.timeline_urls = set()
        self.timeline_feature_vectors = []
        self.feature_vector_counts = Counter()
        self.discarded_ids = set()
        self.sequence_matcher = difflib.SequenceMatcher()
        self.n_candidates = n_candidates
        self.target_entropy = target_entropy

    def reset(self):
        del self.timeline[:]
        del self.timeline_feature_vectors[:]
        self.feature_vector_counts = Counter()
        self.timeline_ids.clear()
        self.user_ids.clear()
        self.timeline_urls.clear()
        self.discarded_ids.clear()

    def __iter__(self):
        return self.timeline.__iter__()

    def __add_tweet__(self, tweet):
        self.timeline.append(tweet)
        self.timeline_ids.add(tweet['pk'])
        self.user_ids.add(tweet['user__internal_id'])
        self.timeline_feature_vectors.append(tweet['__feature_vector__'])
        self.feature_vector_counts.update([tweet['__feature_vector__']])
        self.timeline_urls.update(tweet['char']['links'])
        
        print(['tweet', len(self), tweet['text']])

    def __call__(self, tweets):
        if not self.timeline:
            first = self.start_strategy(tweets)
            if first:
                self.__add_tweet__(first)
            return first

        pairs = []

        for tweet in tweets:
            if tweet['pk'] in self.timeline_ids or tweet['pk'] in self.discarded_ids:
                continue

            if self.allow_repeated_users == False and tweet['user__internal_id'] in self.user_ids:
                self.discarded_ids.add(tweet['pk'])
                continue

            if self.allow_repeated_urls == False and tweet['char']['links'] & self.timeline_urls:
                self.discarded_ids.add(tweet['pk'])
                continue

            if not self.approve_tweet_fn(tweet):
                continue

            too_similar = False
            for added_tweet in self.timeline:
                self.sequence_matcher.set_seqs(added_tweet['text'], tweet['text'])
                similarity = self.sequence_matcher.quick_ratio()
                if similarity > self.similarity_threshold:
                    print('tweet too similar to a previously added one')
                    print(similarity, [added_tweet['text'], tweet['text']])
                    print('ALREADY ADDED', [added_tweet['text']])
                    print('CANDIDATE', [tweet['text']])
                    self.discarded_ids.add(tweet['pk'])
                    too_similar = True
                    break

            if too_similar:
                continue

            self.feature_vector_counts.update([tweet['__feature_vector__']])
            tweet_entropy = self.__estimate_entropy__()
            self.feature_vector_counts.subtract([tweet['__feature_vector__']])
            
            if self.feature_vector_counts[tweet['__feature_vector__']] <= 0:
                del self.feature_vector_counts[tweet['__feature_vector__']]

            if tweet_entropy >= self.target_entropy:
                pairs.append((tweet_entropy, tweet))

            if self.n_candidates and len(pairs) >= self.n_candidates:
                break

        candidates = [p[1] for p in pairs]
        print('entropies', [p[0] for p in pairs])
        selected = self.pick_strategy(candidates)

        if selected:
            self.__add_tweet__(selected)

        return selected

    def __len__(self):
        return len(self.timeline)

    def shout_score(self, text):
        uppercase_count = float(sum([1 for c in text if c.isupper()]))
        upper_fraction = uppercase_count / len(text)
        return upper_fraction

    def prepare_tweet(self, tweet):
        if 'char' not in tweet:
            tweet['char'] = self.characterizer.characterize_text(tweet['text'])

        tweet['buckets'] = {
            'followers': int(math.log(tweet['user__followers_count'] + 1)),
            'friends': int(math.log(tweet['user__friends_count'] + 1)),
            'n_tweets': int(math.log(tweet['user__statuses_count'] + 1)),
            'url': bool(tweet['char']['links']),
            'reply': bool(tweet['characterization__is_reply']),
            'diffusion': bool(tweet['characterization__manual_rt']),
            'popularity': int(math.log(tweet['popularity'] + 1))
        }

        if not self.skip_field('geography'):
            tweet['buckets']['geography'] = tweet['geography'],

        if tweet['buckets']['friends'] == 0 or tweet['buckets']['followers'] == 0:
            tweet['buckets']['hub'] = 0
        else:
            hub_relation = float(tweet['buckets']['followers']) / tweet['buckets']['friends']
            tweet['buckets']['hub'] = int(math.log(hub_relation))

        delta = tweet['datetime'] - self.min_date
        total_minutes = int(delta.total_seconds() / 60.0)
        time_bucket = total_minutes / self.time_bucket_size
        tweet['buckets']['time'] = time_bucket

        if not self.skip_field('topics'):
            if tweet['char']['hashtags']:
                ht = tweet['char']['hashtags'][0]
            else:
                ht = None

            tweet['buckets']['topics'] = ht

        tweet['__feature_vector__'] = self.__feature_vector__(tweet)
        tweet['__shout_score__'] = self.shout_score(tweet['text'])

    def feature_vector_keys(self):
        keys = []
        for field in self.feature_keys:
            if self.skip_field(field):
                continue

            keys.append(field)

        return keys

    def __feature_vector__(self, tweet):
        vec = []
        for field in self.feature_keys:
            if self.skip_field(field):
                continue

            vec.append(tweet['buckets'][field])

        return tuple(vec)

    def __estimate_entropy__(self):
        counts = self.feature_vector_counts #Counter(self.timeline_feature_vectors)
        #print counts
        #N = float(sum(counts.values()))
        N = float(len(self.timeline) + 1)
        max_H = np.log(float(len(list(filter(lambda x: x, counts)))))

        if np.equal(max_H, 0.0):
            return 0.0

        entropy = 0.0

        for key in counts.keys():
            if counts[key] > 0:
                key_probability = counts[key] / N
                entropy += -(key_probability * np.log(key_probability))

        entropy /= max_H

        #print u'N={0}, |counts|={3}, max_H={1}, entropy={2}, counter={4}'.format(N, max_H, entropy, len(counts), counts)
        return entropy

    def skip_field(self, x):
        return bool(self.skip_fields and x in self.skip_fields)

    @classmethod
    def select_tweet(cls, tweets):
        return max(tweets, key=lambda x: x['popularity'])

    @classmethod
    def select_popular_bucketed(cls, tweets):
        max_popularity = max([t['buckets']['popularity'] for t in tweets])
        popular = [t for t in tweets if t['buckets']['popularity'] == max_popularity]
        return random.choice(popular)

    @classmethod
    def select_tweet_and_sideline(cls, pick, categories, turns=5):
        sidelined = dict([(c, 0) for c in categories])
        state = {'output': False}

        def decrement_counts(selected=None):
            for key in sidelined.keys():
                if selected and key == selected['geography']:
                    sidelined[key] = turns
                else:
                    sidelined[key] -= 1

            print('sideline counts', sidelined)

        def is_sidelined(tweet):
            return sidelined[tweet['geography']] <= 0

        def sideline(tweets):
            if not state['output']:
                #print [t['text'] for t in tweets[0:3]]
                state['output'] = True

            if not tweets:
                return None

            filtered = list(filter(is_sidelined, tweets))

            if not filtered:
                print('all candidate tweets sidelined')
                decrement_counts()
                selected = sideline(tweets)
            else:
                selected = pick(filtered)
                decrement_counts(selected=selected)
                sidelined[selected['geography']] = turns

            return selected

        return sideline, is_sidelined

    @classmethod
    def starting_tweet(cls, tweets):
        max_rt_count = max(tweets, key=lambda e: e['popularity'])['popularity']
        candidates = [t for t in tweets if t['popularity'] == max_rt_count]
        selected = random.choice(candidates)
        return selected
