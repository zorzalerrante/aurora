import gensim
from cytoolz import merge_with, partition_all
from .auxiliary import queryset_iterator
from itertools import groupby


def dictionary_from_tweets(tweets, characterizer, dictionary=None, stopwords=None, no_below=5, no_above=1.0, chunksize=50000):
    if dictionary is None:
        dictionary = gensim.corpora.Dictionary()

    if not tweets.exists():
        return dictionary

    for tweet in queryset_iterator(tweets.only('text'), chunksize=chunksize):
        keywords = characterizer.tokenize(tweet.text)
        dictionary.doc2bow(keywords, allow_update=True)

    if stopwords:
        stopword_ids = [dictionary.token2id[word] for word in stopwords if word in dictionary.token2id]
        dictionary.filter_tokens(bad_ids=stopword_ids)

    dictionary.filter_extremes(no_below=no_below, no_above=no_above, keep_n=None)

    return dictionary


class TweetCorpus(object):
    def __init__(self, tweets, dictionary, characterizer, chunksize=None):
        self.characterizer = characterizer
        self.dictionary = dictionary
        self.tweets = tweets
        self.chunksize = chunksize if chunksize is not None else 50000

    def __len__(self):
        return self.tweets.count()

    def __iter__(self):
        for tweet in queryset_iterator(self.tweets.only('text'), chunksize=self.chunksize):
            keywords = self.characterizer.tokenize(tweet.text)
            yield list(self.dictionary.doc2bow(keywords, allow_update=False))


def concatenate_tweets(tweets, dictionary, characterizer, step=10000):
    if not tweets.count():
        return []

    all_bows = []

    for tweets in partition_all(step, queryset_iterator(tweets.only('text'), chunksize=step)):
        bows = []

        for tweet in tweets:
            keywords = characterizer.tokenize(tweet.text)
            bow = dictionary.doc2bow(set(keywords), allow_update=False)
            bows.append(dict(bow))

        all_bows.append(merge_with(sum, *bows))

    return list(merge_with(sum, all_bows).items())


class AggregatedCorpus(object):
    def __init__(self, querysets, dictionary, characterizer, chunksize=50000):
        self.characterizer = characterizer
        self.dictionary = dictionary
        self.querysets = querysets
        self.chunksize = chunksize

    def __len__(self):
        return len(self.querysets)

    def __iter__(self):
        for queryset in self.querysets:
            yield concatenate_tweets(queryset, self.dictionary, self.characterizer, step=self.chunksize)


class GroupedByCorpus(object):
    def __init__(self, dictionary, characterizer, tweets, key='user_id', step=5000):
        self.tweets = tweets
        self.key = key
        self.characterizer = characterizer
        self.dictionary = dictionary
        self.order = []
        self.key_func = lambda x: getattr(x, self.key)
        self.step = int(step)

    def __len__(self):
        return len(set(self.tweets.values_list(self.key, flat=True)))

    def __iter__(self):
        self.order = []
        user_ids = list(set(self.tweets.values_list(self.key, flat=True)))

        for user_pks in partition_all(self.step, user_ids):
            queryset = self.tweets.filter(user_id__in=user_pks)
            for key_id, tweet_set in groupby(queryset.only('text', self.key).order_by(self.key), key=self.key_func):
                bows = []

                for tweet in tweet_set:
                    keywords = self.characterizer.tokenize(tweet.text)
                    bow = self.dictionary.doc2bow(set(keywords), allow_update=False)
                    bows.append(dict(bow))

                self.order.append(key_id)
                yield list(merge_with(sum, *bows).items())
