import gensim
import sklearn.preprocessing
import numpy as np
from sklearn import svm
from virtualornithology.birds.gensimwrapper import AggregatedCorpus


class TweetClassifier(object):

    def build_X(self, querysets):
        x = []
        for qs in querysets:
            for tweet in qs:
                words = self.characterizer.characterize_text(tweet.text)
                tweet_bow = self.dictionary.doc2bow(words['keywords'], allow_update=False)
                f1 = self.similarity[self.tfidf[tweet_bow]]
                #print f1
                x.append(f1)
        return sklearn.preprocessing.normalize(x, norm='l1', axis=1, copy=False)

    def __init__(self, characterizer, dictionary, querysets, prefix='/tmp/location_tmp_idx'):
        self.characterizer = characterizer
        self.dictionary = dictionary
        self.querysets = querysets
        self.corpus = AggregatedCorpus(self.querysets, self.dictionary, self.characterizer)
        self.Y = np.concatenate([np.ones((len(qs), 1)) * i for i, qs in enumerate(self.querysets)]).ravel()
        self.tfidf = gensim.models.TfidfModel(corpus=self.corpus, id2word=self.dictionary)
        self.similarity = gensim.similarities.Similarity(prefix, self.tfidf[self.corpus], num_features=len(self.dictionary), num_best=None)

        self.X = self.build_X(self.querysets)
        self.svm = svm.LinearSVC().fit(self.X, self.Y)