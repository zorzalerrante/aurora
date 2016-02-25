# -*- coding: utf-8 -*-
from django.conf import settings
from .models import Portrait
import json
import gzip
import datetime
import tweepy
from .ngrams import Tokenizer
import glob
from collections import Counter, defaultdict
from math import log10, log
import networkx as nx
from networkx.readwrite import json_graph
from virtualornithology.birds.models import User, Tweet
from virtualornithology.birds.html import beautify_html
from virtualornithology.birds.auxiliary import parse_twitter_date
from virtualornithology.analysis.characterizer import Characterizer
from cytoolz import merge_with, pluck, valfilter
from itertools import combinations
import heapq
from django.utils import timezone
import random
from django.core.urlresolvers import reverse
import difflib

# AUXILIARY FUNCTIONS
def kld(lda, lda_topics):
    """
    Builds a function to estimate Kullback-Leibler distance w.r.t. lda_topics using lda.

    Bigi, B. (2003). Using Kullback-Leibler distance for text categorization (pp. 305-319). Springer Berlin Heidelberg.

    :param lda: LDA model.
    :param lda_topics: LDA topic probabilities for a given target user.
    """
    if lda.num_topics != len(lda_topics):
        Q_eps = (1.0 - sum(x[1] for x in lda_topics)) / (lda.num_topics - len(lda_topics))
    else:
        Q_eps = 0.0

    Q_x = defaultdict(lambda: Q_eps)
    Q_x.update(lda_topics)

    def kullback_leibler_distance(P):
        """
        Estimates the KLD between topic distributions Q (target) and P (candidate).
        :param P: LDA topic probabilities for a given candidate user.
        """
        if lda.num_topics != len(P):
            P_eps = (1.0 - sum(x[1] for x in P)) / (lda.num_topics - len(P))
        else:
            P_eps = 0.0

        P_x = defaultdict(lambda: P_eps)
        P_x.update(P)

        result = 0.0
        for i in range(0, lda.num_topics):
            result += (P_x[i] - Q_x[i]) * log(P_x[i] / Q_x[i])

        return result

    return kullback_leibler_distance


def jaccard(graph, lda_topics):
    """
    Builds a function to estimate Jaccard Similarity w.r.t. intermediary topics (from topic graph) in lda_topics.
    """
    Q_it = set(x[0] for x in lda_topics if graph.has_node(x[0]) and graph.node[x[0]]['is_intermediary'])

    def jaccard_similarity(P):
        if not P or not Q_it:
            return 0.0

        P_it = set(x[0] for x in P if graph.has_node(x[0]) and graph.node[x[0]]['is_intermediary'])
        #print P_it, Q_it, float(len(P_it & Q_it)) / len(P_it | Q_it), P_it & Q_it
        return float(len(P_it & Q_it)) / len(P_it | Q_it)

    return jaccard_similarity


def f_score_fn(beta):
    b2 = beta * beta
    def f_score(x, y):
        return (1.0 + b2) * (x * y) / (b2 * x + y)
    return f_score


# "REAL" FUNCTIONS
def portrait_details(backend, user, response, *args, **kwargs):
    print('backend', backend)
    print('user', user)
    print('response', response)
    print('args', args)
    print('kwargs', kwargs)

    portrait = create_portrait_model(response)
    return {'portrait': portrait}


def create_portrait_model(response, has_auth=True):
    portrait, created_portrait = Portrait.objects.get_or_create(auth_id_str=response['id_str'])
    print('portrait', created_portrait)
    print(response)

    if created_portrait:
        portrait.portrait_content = None
        portrait.portrait_recommendations = None
        portrait.last_tweet_date = None
        portrait.last_tweet_id = None
        portrait.last_access = None
        portrait.last_update_date = None

        portrait.portrait_preferences = json.dumps({
            'profile_text_color': response['profile_text_color'],
            'profile_use_background_image': response['profile_use_background_image'],
            'profile_background_image_url_https': response['profile_background_image_url_https'],
            'profile_image_url_https': response['profile_image_url_https'],
            'profile_sidebar_fill_color': response['profile_sidebar_fill_color'],
            'profile_link_color': response['profile_link_color'],
            'profile_image_url': response['profile_image_url'],
            'font_face': 'Roboto',
            'include_rts': True,
            'exclude_replies': False,
            'condition': 'portrait'
        })

    if has_auth:
        portrait.demo_portrait = False
        portrait.access_token = response['access_token']['oauth_token']
        portrait.access_token_secret = response['access_token']['oauth_token_secret']
        portrait.featured_on_home = False
        response.pop('access_token')
    else:
        portrait.demo_portrait = True
        portrait.featured_on_home = True

    if portrait.condition_ui is None:
        portrait.condition_ui = random.choice(['baseline', 'bubbles'])

    if portrait.condition_rec is None:
        portrait.condition_rec = random.choice(['kls', 'it_score'])

    portrait.active = True
    portrait.auth_screen_name = response['screen_name'].lower()
    response['portrait_url'] = reverse('portraits:view-portrait', args=[portrait.auth_screen_name])
    portrait.user_data = json.dumps(response)
    portrait.public_access_enabled = not response['protected']
    portrait.save()
    return portrait


def portrait_api(portrait, wait_on_rate_limit=True):
    api_keys = settings.TWITTER_USER_KEYS
    auth = tweepy.OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])

    if portrait.demo_portrait:
        auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])
    else:
        auth.set_access_token(portrait.access_token, portrait.access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=wait_on_rate_limit)

    return api


def portrait_follow(portrait, user_id):
    if portrait.demo_portrait:
        return False

    api = portrait_api(portrait)
    followed_user = api.create_friendship(user_id)

    if followed_user:
        return True

    return False


def portrait_share(portrait):
    if portrait.demo_portrait:
        print('demo portrait not shareable')
        return False

    api = portrait_api(portrait)

    url = reverse('portraits:view-portrait', args=[portrait.auth_screen_name])
    status_text = 'Visita mi perfil visual en http://auroratwittera.cl{0} / Crea el tuyo en @todocl, http://auroratwittera.cl'.format(url)
    print(repr(status_text))
    res = api.update_status(status_text)
    print(res)

    return True


def crawl_user_data(portrait, path):
    api = portrait_api(portrait)
    now = datetime.datetime.now().strftime("%Y%m%d%H%M")

    timeline = [t._json for t in tweepy.Cursor(api.user_timeline, user_id=portrait.auth_id_str, count=200, since_id=portrait.last_tweet_id).items()]

    if timeline:
        with gzip.open('{0}/{1}_{2}.data.gz'.format(path, portrait.auth_id_str, now), 'wt') as f:
            f.write(json.dumps(timeline))

        print('loaded tweets', len(timeline))

    if not portrait.demo_portrait:
        print(portrait.auth_screen_name, 'not a demo portrait. downloading connectivity')
        connectivity = [t for t in tweepy.Cursor(api.friends_ids, user_id=portrait.auth_id_str, cursor=-1).items()]

        print('loaded friends', len(connectivity))

        with gzip.open('{0}/{1}_{2}.friends.gz'.format(path, portrait.auth_id_str, now), 'wt') as f:
            f.write(json.dumps(connectivity))

    return True


def load_tweets(user_id, path, max_tweets=None):
    tweets = []

    filenames = sorted(glob.glob('{0}/{1}_*.data.gz'.format(path, user_id)), reverse=True)

    for fname in filenames:
        try:
            with gzip.open(fname, 'rt') as f:
                tweets.extend(json.load(f))
        except:
            pass
        #print fname, len(tweets)
        if max_tweets is not None and len(tweets) > max_tweets:
            break

    return tweets[:max_tweets]


def load_friends(user_id, path, max_friends=100000):
    filenames = sorted(glob.glob('{0}/{1}_*.friends.gz'.format(path, user_id)), reverse=True)[0:1]

    if not filenames:
        return set()

    friends = set()
    for fname in filenames:
        try:
            with gzip.open(fname, 'rt') as f:
                friends.update(map(str, json.load(f)[:max_friends]))
        except:
            pass

    return friends


def get_recommendations(characterizer, texts, portrait, path, lda_model, topic_graph, rec_candidates, n_recommendations=25):
    friends = load_friends(portrait.auth_id_str, path)

    print(len(friends), 'friends loaded')
    # we remove already followed users
    candidates = list(filter(lambda x: x['internal_id'] not in friends, rec_candidates))
    print('# candidates', len(candidates))

    if not candidates:
        return []

    if not texts:
        print('NO TWEETS AVAILABLE')
        return heapq.nlargest(n_recommendations, candidates, lambda x: x['followers_count'])

    doc2bow = lambda x: lda_model.id2word.doc2bow(set(characterizer.tokenize(x)))
    p_bow = merge_with(sum, *map(dict, (doc2bow(t['text']) for t in texts)))
    p_lda = lda_model[list(p_bow.items())]
    print('portrait lda', p_lda)

    if not p_lda:
        return heapq.nlargest(n_recommendations, candidates, lambda x: x['followers_count'])

    fn_kld = kld(lda_model, p_lda)
    fn_jaccard = jaccard(topic_graph, p_lda)

    for c in candidates:
        c['distance'] = fn_kld(c['topics']) + 0.001
        c['jaccard'] = fn_jaccard(c['topics'])

    max_distance = max(candidates, key=lambda x: x['distance'])['distance']
    print('max distance', max_distance)
    max_jaccard = max(candidates, key=lambda x: x['jaccard'])['jaccard']
    min_jaccard = min(candidates, key=lambda x: x['jaccard'])['jaccard']
    print('jaccard', min_jaccard, max_jaccard)

    for c in candidates:
        c['kls'] = 1.0 - (c['distance']) / max_distance

    sort_field = 'kls' if portrait.condition_rec == 'kls' else 'score_1.0'
    print('sort field', sort_field)

    if sort_field != 'kls':
        f_score_05 = f_score_fn(0.5)
        f_score_10 = f_score_fn(1.0)
        f_score_20 = f_score_fn(2.0)

        for c in candidates:
            c['score_0.5'] = f_score_05(c['kls'], c['jaccard'])
            c['score_1.0'] = f_score_10(c['kls'], c['jaccard'])
            c['score_2.0'] = f_score_20(c['kls'], c['jaccard'])

    return heapq.nlargest(n_recommendations, candidates, lambda x: x[sort_field])


def select_tweets(timeline, allow_rts=True, allow_replies=False, popular_only=True):
    texts = []

    for t in timeline:
        if not 'retweeted_status' in t:
            if not allow_replies and t['in_reply_to_status_id_str']:
                continue
            t['tweet_score'] = log(t['retweet_count'] + 1.0) + log(t['favorite_count'] + 1.0)
            t['__is_rt__'] = False
            texts.append(t)
        else:
            if allow_rts:
                t['retweeted_status']['tweet_score'] = log10(t['retweet_count'] + 1.0) + log10(t['favorite_count'] + 1.0)
                t['retweeted_status']['source_created_at'] = t['retweeted_status']['created_at']
                t['retweeted_status']['created_at'] = t['created_at']
                t['retweeted_status']['text'] = t['retweeted_status']['text']
                t['retweeted_status']['__is_rt__'] = True
                texts.append(t['retweeted_status'])

    #texts = sorted(texts, key=lambda x: x['tweet_score'], reverse=True)[0:100]
    if popular_only:
        texts = list(filter(lambda x: x['tweet_score'] > 0, texts))

    return texts


def build_token_counts(characterizer, texts):
    tokenizer = Tokenizer(characterizer=characterizer)
    tokenizer.train([t['text'] for t in texts])

    token_counts = Counter()
    seq_matcher = difflib.SequenceMatcher()

    for t in texts:
        t['tokens'] = tokenizer.tokenize(t['text'])
        if not t['tokens']:
            continue

        if 'urls' in t['entities'] and t['entities']['urls']:
            #TODO: replace those urls instead of adding them
            for url in t['entities']['urls']:
                t['tokens'].append(url['display_url'])

        if t['__is_rt__']:
            t['tokens'].append(u'@{0}'.format(t['user']['screen_name']).lower())

        token_counts.update(t['tokens'])

    return token_counts


def merge_tokens(token_counts, max_concepts=250, threshold=0.9):
    seq_matcher = difflib.SequenceMatcher()

    token_replacement = {}
    most_common_keys = set(w[0] for w in token_counts.most_common(max_concepts))

    for t0, t1 in combinations(token_counts.keys(), 2):
        if not t0 in most_common_keys or not t1 in most_common_keys:
            continue

        if '/' in t0 or '/' in t1:
            # no urls
            continue

        seq_matcher.set_seqs(t0, t1)
        similarity = seq_matcher.ratio()
        if similarity >= threshold:
            # we prefer hashtags
            if t0.startswith('#') or token_counts[t0] > token_counts[t1]:
                keep = t0
                throw = t1
            else:
                keep = t1
                throw = t0

            if not keep in token_replacement:
                token_replacement[throw] = keep
            else:
                token_replacement[throw] = token_replacement[keep]

            token_counts[keep] += token_counts[throw]
            token_counts.pop(throw, None)

    return token_replacement


def update_portrait(portrait, path, lda_model, topic_graph, rec_candidates, characterizer=None,
                    allow_rts=True, allow_replies=False, max_tweets=3200, max_concepts=250, popular_only=True,
                    n_recommendations=15, min_tweets=30, update_users=True, write_update_date=True, update_api=None,
                    notify_users=False, update_days=3):
    """
    Updates the content of the given portrait instance.

    :param portrait: the instance we are goind to update.
    :param path: path to tweet files crawled using tweepy
    :param lda_model: a gensim LDA model.
    :param topic_graph: a networkx graph of relations between topics in the lda model.
    :param rec_candidates: an array of users to consider for making recommendations in this portrait.
    :param characterizer: the characterizer instance.
    :param allow_rts: consider retweets in the portrait.
    :param allow_replies: consider replies in the portrait.
    :param max_tweets: maximum number of tweets to consider when building the portrait.
    :param max_concepts: maximum number of elements in the portrait wordcloud.
    :param popular_only: consider only tweets who have been favorited/retweeted.
    :param update_api: API instance to post updates on regular portraits.
    :return:
    """

    if portrait.condition_ui is None:
        portrait.condition_ui = random.choice(['baseline', 'bubbles'])

    if portrait.condition_rec is None:
        portrait.condition_rec = random.choice(['kls', 'it_score'])

    is_new_portrait = portrait.portrait_content is None

    if characterizer is None:
        characterizer = Characterizer()

    timeline = load_tweets(portrait.auth_id_str, path, max_tweets=max_tweets)
    texts = select_tweets(timeline, allow_replies=allow_replies, allow_rts=allow_rts, popular_only=popular_only)

    print('texts', len(texts))

    token_counts = build_token_counts(characterizer, texts)
    token_counts.pop('@{0}'.format(portrait.auth_screen_name), None)

    replacement_tokens = merge_tokens(token_counts, max_concepts=max_concepts, threshold=0.9)

    most_common_keys = set(w[0] for w in token_counts.most_common(max_concepts))

    tweet_graph = nx.DiGraph(portrayed_user=json.loads(portrait.user_data))

    for w in most_common_keys:
        tweet_graph.add_node(w, weight=token_counts[w], label=w, type='term', color='gray')

    for t in texts:
        tweet_tokens = []

        for token in t['tokens']:
            if token in most_common_keys:
                tweet_tokens.append(token)
            elif token in replacement_tokens and replacement_tokens[token] in most_common_keys:
                tweet_tokens.append(replacement_tokens[token])

        if not tweet_tokens:
            continue

        text = beautify_html(t['text'], sources=t['entities']['urls'])
        #print repr(text)
        tweet_graph.add_node(t['id_str'],
                             avatar=t['user']['profile_image_url_https'],
                             author=t['user']['screen_name'],
                             datetime=t['created_at'],
                             label=text,
                             type='tweet',
                             color='purple',
                             weight=t['tweet_score'],
                             media=t['entities']['media'][0] if 'media' in t['entities'] else None
                             )

        for w in tweet_tokens:
            tweet_graph.add_edge(t['id_str'], w)

    print(tweet_graph.number_of_nodes(), tweet_graph.number_of_edges())

    # now, recommendations!
    print('received', len(rec_candidates), 'candidates for recommendation')

    if lda_model is not None:
        recommendation_graph = nx.DiGraph(root=lda_model.num_topics)

        top_candidates = get_recommendations(characterizer, texts, portrait, path, lda_model, topic_graph, rec_candidates, n_recommendations=n_recommendations)

        if top_candidates:

            valid_candidate_pks = set(pluck('pk', top_candidates))

            if update_users and update_api is not None:
                user_ids = User.objects.filter(pk__in=pluck('pk', top_candidates)).values_list('internal_id', flat=True)
                #api = portrait_api(portrait)

                current_candidate_pks = set()
                try:
                    for u in update_api.lookup_users(user_ids=user_ids):
                        u_json = valfilter(lambda x: x, u._json)
                        user_model, created = User.import_json(u_json)
                        current_candidate_pks.add(user_model.pk)

                    valid_candidate_pks = current_candidate_pks
                except Exception as err:
                    print('ERROR', err)

            candidate_map = User.objects.in_bulk(valid_candidate_pks)

            sort_field = 'kls' if portrait.condition_rec == 'kls' else 'score_1.0'

            recommendation_graph.add_node(lda_model.num_topics, depth=0, content=None, weight=0)

            n_it = 1

            for i, c in enumerate(top_candidates):
                pk = c['pk']

                if not pk in candidate_map:
                    print('deleted user', pk)
                    continue

                topic_id = max(c['topics'], key=lambda x: x[1])[0]

                weight = c[sort_field] * (len(top_candidates) - float(i))

                if not recommendation_graph.has_node(topic_id):
                    recommendation_graph.add_node(topic_id, depth=1, weight=0)
                    recommendation_graph.add_edge(lda_model.num_topics, topic_id)

                candidate_json = candidate_map[pk].displayable_dict()
                candidate_json['rank'] = i

                recommendation_graph.add_node(lda_model.num_topics + n_it, label='', content=candidate_json, depth=2, weight=weight)
                recommendation_graph.add_edge(topic_id, lda_model.num_topics + n_it)

                recommendation_graph.node[topic_id]['weight'] += weight
                recommendation_graph.node[lda_model.num_topics]['weight'] += weight
                n_it += 1

        recommendations = json_graph.tree_data(recommendation_graph, recommendation_graph.graph['root'])
    else:
        recommendations = None

    portrait.portrait_content = json.dumps(json_graph.node_link_data(tweet_graph))
    portrait.portrait_recommendations = json.dumps(recommendations)
    portrait.last_tweet_id = timeline[0]['id_str']
    portrait.last_tweet_date = parse_twitter_date(timeline[0]['created_at'])

    if write_update_date:
        portrait.last_update_date = timezone.now()

    url = reverse('portraits:view-portrait', args=[portrait.auth_screen_name])

    if is_new_portrait:
        status_text = '@{0}, ¡tu perfil visual en http://auroratwittera.cl{1} está listo!'.format(portrait.auth_screen_name, url)
    else:
        status_text = '@{0}, ¡tu perfil visual en http://auroratwittera.cl{1} ha sido actualizado!'.format(portrait.auth_screen_name, url)

    previous_update_date = portrait.last_notification_date

    if portrait.demo_portrait:
        print('demo portrait')
        should_notify = False
    elif is_new_portrait or previous_update_date is None:
        print('new portrait, or it wasnt updated before')
        should_notify = True
    elif previous_update_date is not None:
        delta_time = timezone.now() - previous_update_date
        print('delta time', delta_time.days, update_days)
        should_notify = (delta_time.days >= update_days)
    else:
        should_notify = False

    print('should notify?', should_notify)
    print(repr(status_text))

    if should_notify:
        portrait.last_notification_date = timezone.now()

    portrait.save()

    if should_notify and notify_users and update_api is not None:
        update_api.update_status(status_text)
