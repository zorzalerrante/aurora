import numpy as np
from functools import reduce

def lda_topic_descriptors(lda, n_words=25, max_words=10000, word_filter=lambda x: x):
    """
    Given a LDA model, return a list of topics with word descriptors.

    :param lda:
    :param n_words:
    :param max_words:
    :param word_filter:
    :return:
    """
    exponent = 1.0 / float(max_words)
    quotient_cache = {}

    dictionary = lda.id2word

    def quotient(word):
        if word in quotient_cache:
            return quotient_cache[word]
        value = reduce(lambda x, y: x * y, [x[1] for x in lda[dictionary.doc2bow([word])]], 1.0)
        quotient_cache[word] = np.power(value, exponent)
        return value

    def re_rank(topic):
        re_ranked = sorted(topic, key=lambda x: x[0] * np.log(x[0] / quotient(x[1])), reverse=True)
        re_ranked = [w for w in re_ranked if word_filter(w[1])]
        return re_ranked

    ranked_topics = []

    for i in range(0, lda.num_topics):
        topic = lda.show_topic(i, topn=max_words)
        words = re_rank(topic)
        ranked_topics.append(words[:n_words])

    return ranked_topics
