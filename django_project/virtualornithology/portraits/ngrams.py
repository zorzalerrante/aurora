import gensim
from virtualornithology.analysis.characterizer import Characterizer


class Tokenizer(object):
    def __init__(self, characterizer=None, ngram_threshold=3.0):
        self.characterizer = characterizer if characterizer is not None else Characterizer()
        self.ngram_threshold = ngram_threshold
        self.stopwords = self.characterizer.stopwords()

    def _filter_(self, tokens):
        to_pop = set()

        for w in tokens:
            if self.characterizer.is_stopword(w) or len(w) == 1:
                to_pop.add(w)
                continue

            if 'http://t.co' in w:
                to_pop.add(w)
                continue

            parts = w.split('_')
            if self.characterizer.is_stopword(parts[-1]):
                to_pop.add(w)
                continue

            if parts[0] in ('rt', 'mt', 'via'):
                to_pop.add(w)
                continue

            if all(self.characterizer.is_stopword(p) for p in parts):
                to_pop.add(w)
                continue

            parts = set(parts)

            if 'http' in parts:
                to_pop.add(w)
                continue

            if len(parts) == len(parts & self.stopwords):
                to_pop.add(w)
                continue

        return list(filter(lambda x: x not in to_pop, tokens))

    def train(self, corpus):
        self.bigrams = gensim.models.Phrases((self.characterizer.tokenize(t) for t in corpus), threshold=self.ngram_threshold)
        self.trigrams = gensim.models.Phrases((self.bigrams[self.characterizer.tokenize(t)] for t in corpus), threshold=self.ngram_threshold * 0.5)

    def tokenize(self, text):
        tokens = self.trigrams[self.bigrams[self.characterizer.tokenize(text)]]
        return self._filter_(tokens)
