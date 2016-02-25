from urllib.parse import urlparse

import regex as re
from django.conf import settings
from cytoolz import memoize

from virtualornithology.birds.auxiliary import normalize_str, tokenize
from virtualornithology.places.geolocator import geolocate
from virtualornithology.places.models import Location
from virtualornithology.birds.auxiliary import load_list_from_file

class Characterizer(object):
    # variables
    # http://stackoverflow.com/questions/863297/regular-expression-to-retrieve-domain-tld

    def __init__(self):
        self._url_pattern = r'(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|])'

        self._re = {
            'hashtag': re.compile(r'#([\w]+)'),
            'mention': re.compile(r'@([\w]+)'),
            'phrase': re.compile('[^\s\d\w]'),
            'split': re.compile(r'[\W\s]+'),
            'non_word': re.compile('[\W]+'),
            'spaces': re.compile('\s+'),
            'url': re.compile(self._url_pattern)
        }

        self._stopwords = {
            lang: load_list_from_file(settings.PROJECT_PATH + '/stopwords/{0}.txt'.format(lang), normalize_text=True)
            for lang in settings.TWITTER_ACCEPTED_LANGUAGES
        }

        self._universal_stopwords = load_list_from_file(settings.PROJECT_PATH + '/stopwords/other.txt', normalize_text=True)

        self._source_locations = {}

        for location in Location.objects.filter(depth=0):
            self._source_locations[normalize_str(location.name)] = location

        self._do_geo_location = bool(self._source_locations)

        # we do this so it works with cytoolz :(
        # it doesn't work if we memoize directly the class function
        @memoize
        def _get_geolocation(text):
            location = None

            if text:
                found_locations = geolocate(text)

                if found_locations:
                    location = max(found_locations, key=lambda x: x.depth)
                else:
                    for loc_name, source_location in self._source_locations.items():
                        if loc_name in text:
                            location = source_location
                            break

            return location

        self._geolocation_fn = _get_geolocation
        self.rt_starters = ['RT @', 'MT @', 'RT@']

    def characterize_tweet(self, status, extend_with_tweet_info=False):
        features = self.characterize_text(status.text)
        features['tweet_id'] = status.pk
        features['datetime'] = status.datetime
        features['text'] = status.text
        features['count_media'] = status.media.count()
        features['user_id'] = status.user_id
        features['manual_rt'] = False

        for starter in self.rt_starters:
            if status.text.startswith(starter):
                features['manual_rt'] = True
                break

        features['is_reply'] = bool(status.in_reply_to_status_id)
        features['length'] = len(status.text)

        if extend_with_tweet_info:
            features.update(status.displayable_dict())

        return features

    def characterize_user(self, user, extend_with_user_info=False):
        features = self.characterize_text(user.bio)
        features['model'] = user
        features['domain'] = urlparse(user.url).netloc
        if features['domain'].startswith('www.'):
            features['domain'] = features['domain'][4:]

        if user.followers_count:
            features['friends_followers_ratio'] = float(user.friends_count) / user.followers_count
        else:
            features['friends_followers_ratio'] = 0.0

        names = list(self.get_names(user.name))
        features['first_name'] = names[0]
        features['last_name'] = names[1]

        if extend_with_user_info:
            features.update(user.displayable_dict())

        return features

    def characterize_text(self, text, calc_stopwords=False, return_set=False, min_length=2, max_length=25):
        features = {}

        if not text:
            features['mentions'] = set()
            features['hashtags'] = set()
            features['links'] = set()
            features['keywords'] = set()
            return features

        features['links'] = self.get_links(text)

        for l in features['links']:
            text = text.replace(l, '')

        normalized = normalize_str(text)

        keywords = [x for x in self._re['split'].split(normalized)
                   if x not in self._universal_stopwords
                   and (min_length <= len(x) <= max_length)]

        features['mentions'] = set(self.get_mentions(normalized))
        features['hashtags'] = set(self.get_hashtags(normalized))
        features['keywords'] = set(keywords) - features['mentions'] - features['hashtags']
        features['keywords'] |= set(map(lambda x: '#' + x, features['hashtags']))
        features['keywords'] |= set(map(lambda x: '@' + x, features['mentions']))

        if not return_set:
            features['mentions'] = list(features['mentions'])
            features['hashtags'] = list(features['hashtags'])
            features['keywords'] = list(features['keywords'])

        return features

    def get_used_stopwords(self, keywords, lang):
        if lang == 'UNK' or not self._stopwords or not lang in self._stopwords:
            return set()

        return set(keywords).intersection(self._stopwords[lang])

    def prepare_location_name(self, text):
        if text is None:
            return ''

        text = normalize_str(text)
        # Mexico D.F. => Mexico DF
        text = text.replace('.', '')
        text = text.replace(',', ' ')
        # Remove hashes, hearts, etc
        text = self._re['non_word'].sub(' ', text)
        text = self._re['spaces'].sub(' ', text)
        return text.strip()

    def get_geolocation(self, text):
        text = self.prepare_location_name(text)
        return self._geolocation_fn(text)

    def get_mentions(self, text):
        return self._re['mention'].findall(text)

    def get_hashtags(self, text):
        return self._re['hashtag'].findall(text)

    def get_links(self, text):
        return set(self._re['url'].findall(text))

    def is_stopword(self, word, languages=settings.TWITTER_ACCEPTED_LANGUAGES, min_length=2, max_length=40):
        for lang in languages:
            if word in self._stopwords[lang]:
                return True

        if len(word) < min_length or len(word) > max_length:
            return True

        return True if word in self._universal_stopwords else False

    def stopwords(self, languages=settings.TWITTER_ACCEPTED_LANGUAGES):
        stopwords = set()
        for l in languages:
            stopwords.update(self._stopwords[l])
        stopwords.update(self._universal_stopwords)
        return stopwords

    def get_names(self, text):
        names = ['', '']

        #logging.info(user.name
        parts = self._re['non_word'].split(normalize_str(text))
        parts = list(filter(lambda x: x and x not in self._stopwords, parts))
        #logging.info(parts

        if len(parts) == 1:
            names[0] = parts[0]
        elif len(parts) == 2:
            names = parts
        elif len(parts) == 3:
            if len(parts[1]) == 2:
                names = [parts[0], parts[1] + ' ' + parts[2]]
            else:
                names = parts[0:2]
        elif len(parts) == 4:
            names[0] = parts[0]
            names[1] = parts[2]

        return map(normalize_str, names)

    def get_phrases(self, text):
        phrases = self._re['phrase'].split(normalize_str(text))
        phrases = list(filter(lambda x: x, phrases))
        return phrases

    def __keep_token__(self, t):
        if self._re['hashtag'].match(t):
            return True
        if self._re['mention'].match(t):
            return True
        if self._re['url'].match(t):
            return True
        if not t.isalnum() or t.isnumeric():
            return False
        return True

    def tokenize(self, text):
        text = normalize_str(text)
        tokens = tokenize(text)
        return [tok for tok in tokens if self.__keep_token__(tok)]
