import gensim
from virtualornithology.analysis.characterizer import Characterizer
import gzip

try:
    import ujson as json
except ImportError:
    import json

from virtualornithology.birds.models import Tweet, User
from virtualornithology.birds.gensimwrapper import GroupedByCorpus, dictionary_from_tweets
from itertools import combinations
import networkx as nx
import numpy as np
import scipy.stats


def build_intermediary_topics_model(tweets, path, prefix='it', characterizer=None, dictionary=None, lda=None,
                                    num_topics=200, percentile=50.0, min_word_count=10):
    np.random.seed(31051985)

    if characterizer is None:
        characterizer = Characterizer()

    if dictionary is None:
        dictionary = dictionary_from_tweets(tweets, characterizer, stopwords=characterizer.stopwords(), no_below=min_word_count)

    print('dictionary len', len(dictionary))

    corpus = GroupedByCorpus(dictionary, characterizer, tweets, key='user_id')

    if lda is None:
        lda = gensim.models.ldamulticore.LdaModel(corpus=corpus, num_topics=num_topics, id2word=dictionary)

    graph = nx.Graph()

    for bow in corpus:
        topics = lda[bow]
        pairs = list(combinations([x[0] for x in topics], 2))

        for topic, probability in topics:
            if graph.has_node(topic):
                graph.node[topic]['probabilities'].append(probability)
                graph.node[topic]['weight'] += 1
                graph.node[topic]['N'] += 1
            else:
                graph.add_node(topic, probabilities=[probability], weight=1, N=1)

        for s, t in pairs:
            if graph.has_edge(s, t):
                graph[s][t]['weight'] += 1
                graph[s][t]['N'] += 1
            else:
                graph.add_edge(s, t, weight=1, N=1)

    print('topic graph done')

    max_weight = float(max(d['N'] for (u, v, d) in graph.edges(data=True)))
    min_weight = float(min(d['N'] for (u, v, d) in graph.edges(data=True)))
    diff_weight = max_weight - min_weight

    for (u, v, d) in graph.edges(data=True):
        d['weight'] = (d['N'] - min_weight) / diff_weight

    to_remove = []

    for (u, v, d) in graph.edges(data=True):
        if np.equal(d['weight'], 0.0):
            #print u, v, d
            to_remove.append((u, v))

    if to_remove:
        graph.remove_edges_from(to_remove)

    to_remove = []
    for i in range(0, lda.num_topics):
        if graph.has_node(i) and not graph.degree(i):
            to_remove.append(i)

    if to_remove:
        graph.remove_nodes_from(to_remove)

    centrality = nx.algorithms.current_flow_closeness_centrality(graph)
    target_centrality = scipy.stats.scoreatpercentile(list(centrality.values()), percentile)

    for topic_id in graph.nodes_iter():
        graph.node[topic_id]['is_intermediary'] = centrality[topic_id] >= target_centrality
        graph.node[topic_id]['centrality'] = centrality[topic_id]

    # candidates
    candidate_map = User.objects.in_bulk(corpus.order)
    candidates = [{'pk': pk,
                   'internal_id': candidate_map[pk].internal_id,
                   'screen_name': candidate_map[pk].screen_name,
                   'followers_count': candidate_map[pk].followers_count,
                   'topics': c}
                  for c, pk in zip(lda[corpus], corpus.order) if c]

    print('candidates', len(candidates))

    dictionary.save('{0}/it-topics/{1}_dictionary.gensim'.format(path, prefix))
    lda.save('{0}/it-topics/{1}_lda_model.gensim'.format(path, prefix))
    nx.write_gpickle(graph, '{0}/it-topics/{1}_topic_graph.nx'.format(path, prefix))

    with gzip.open('{0}/it-topics/{1}_candidates.json.gz'.format(path, prefix), 'wt') as f:
        json.dump(candidates, f)
