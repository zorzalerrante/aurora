from django.db import models, transaction
from .auxiliary import parse_twitter_date
import regex

URL_RE = regex.compile(r'(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|])')
HASHTAG_RE = regex.compile(r'(#[\w]+)', regex.UNICODE)
MENTION_RE = regex.compile(r'(@[\w]+)', regex.UNICODE)

class Keyword(models.Model):
    name = models.CharField(max_length=255, db_index=True)

    @classmethod
    @transaction.atomic
    def retrieve(cls, keyword_set):
        return map(lambda x: cls.objects.get_or_create(name=x, defaults={'name': x})[0], keyword_set)

    @classmethod
    def bag_of_words(cls, words, update_dictionary=False, min_tweet_count=None, max_tweet_count=None):
        if not update_dictionary:
            models = cls.objects.filter(name__in=words)
            if min_tweet_count is not None:
                models = models.filter(tweet_count__gte=min_tweet_count)
            if max_tweet_count is not None:
                models = models.filter(tweet_count__lte=max_tweet_count)
        else:
            models = cls.retrieve(words)

        bow = [(m.pk, words.count(m.name)) for m in models]
        return dict(bow)

    @classmethod
    def query_tweets(cls, words, exclude_words=None):
        pks = set(cls.objects.filter(name__in=words).values_list('tweet', flat=True))

        if exclude_words:
            exclude_pks = set(cls.objects.filter(name__in=exclude_words).values_list('tweet', flat=True))
        else:
            exclude_pks = set()

        return Tweet.objects.filter(pk__in=pks.difference(exclude_pks))

    def __unicode__(self):
        return self.name


class Url(models.Model):
    short = models.CharField(max_length=255, default='', db_index=True)
    url = models.CharField(max_length=255, default='', db_index=True)
    domain = models.CharField(max_length=255, db_index=True)
    display_url = models.CharField(max_length=255, default='')

    def __unicode__(self):
        return self.url


class Media(models.Model):
    internal_id = models.CharField(unique=True, max_length=100, db_index=True)
    url = models.CharField(max_length=255, default='', db_index=True)
    type = models.CharField(max_length=50, default='photo')
    media_url = models.CharField(max_length=255, default='')
    display_url = models.CharField(max_length=255, default='')
    expanded_url = models.CharField(max_length=255, default='')
    sizes = models.CharField(max_length=255, default='{}')

    def __str__(self):
        return '<a href="{0}">MEDIA ID {1}</a>'.format(self.media_url, self.internal_id)


class User(models.Model):
    internal_id = models.CharField(unique=True, max_length=100, db_index=True, blank=False)
    screen_name = models.CharField(max_length=100, db_index=True, default='')
    name = models.CharField(max_length=100, default='')
    last_updated = models.DateTimeField(auto_now=True)
    bio = models.CharField(max_length=255, default='')
    url = models.CharField(max_length=255, default='')
    location = models.CharField(max_length=255, default='')
    statuses_count = models.IntegerField(default=0)
    listed_count = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    friends_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(db_index=True, null=True)
    time_zone = models.CharField(max_length=100, default='')
    protected = models.BooleanField(default=False)
    favourites_count = models.IntegerField(default=0)
    profile_image_url = models.CharField(max_length=255, default='')
    verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def copy_user(self, u):
        self.screen_name = u.screen_name.lower().strip()
        self.name = u.name
        self.bio = u.bio
        self.url = u.url
        self.location = u.location
        self.statuses_count = u.statuses_count
        self.listed_count = u.listed_count
        self.followers_count = u.followers_count
        self.friends_count = u.friends_count

        self.time_zone = u.time_zone
        self.protected = u.protected
        self.favourites_count = u.favourites_count
        self.profile_image_url = u.profile_image_url

        self.verified = u.verified

    def copy_json(self, u):
        self.internal_id = u['id_str'][:100]
        self.name = u.get('name', '')[:100]
        self.verified = bool(u.get('verified', False))
        self.screen_name = u['screen_name'].lower().strip()[:100]
        self.created_at = parse_twitter_date(u['created_at'])
        self.location = u.get('location', '')[:255]

        self.listed_count = int(u.get('listed_count', 0))
        self.followers_count = int(u.get('followers_count', 0))
        self.friends_count = int(u.get('friends_count', 0))
        self.favourites_count = int(u.get('favourites_count', 0))
        self.statuses_count = int(u.get('statuses_count', 0))

        self.protected = bool(u.get('protected', 0))
        self.profile_image_url = u['profile_image_url'][:255]

        tz = u.get('time_zone', '')
        self.time_zone = tz[:100] if tz else ''

        self.bio = u.get('description', '')[:255]
        self.url = u.get('url', '')

        if self.url:
            self.url = self.url[:255]
        else:
            self.url = ''

    def displayable_dict(self):
        return {
            'pk': self.pk,
            'id': self.internal_id,
            'id_str': self.internal_id,
            'screen_name': self.screen_name,
            'name': self.name,
            'location': self.location,
            'profile_image_url': self.profile_image_url,
            'created_at': self.created_at.isoformat(),
            'full_name': self.name,
            'description': self.bio,
            'followers_count': self.followers_count,
            'friends_count': self.friends_count,
            'total_tweet_count': self.statuses_count,
            'listed_count': self.listed_count
        }

    @classmethod
    def import_json(cls, user_json, save_existant=True):
        try:
            user = cls.objects.get(internal_id=user_json['id_str'])
            if save_existant:
                user.copy_json(user_json)
                user.save()
            return user, False
        except cls.DoesNotExist:
            user = User()
            user.copy_json(user_json)
            try:
                user.save()
            except Exception as e:
                print(user_json)
                raise e
            return user, True

    def __unicode__(self):
        return self.screen_name


class Tweet(models.Model):
    user  = models.ForeignKey(User, related_name='author', db_index=True)
    datetime = models.DateTimeField(db_index=True)
    retweet_count = models.IntegerField(default=0)
    favourite_count = models.IntegerField(default=0)
    in_reply_to_user_id = models.CharField(max_length=255)
    in_reply_to_status_id = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    internal_id = models.CharField(max_length=255, unique=True)
    text = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    has_geo = models.BooleanField(default=False)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    links = models.ManyToManyField(Url)
    media = models.ManyToManyField(Media)
    language = models.CharField(max_length=4, default=u'UNK')
    keywords = models.ManyToManyField(Keyword, db_index=True)
    possibly_sensitive = models.BooleanField(default=False)

    def update_json(self, s):
        try:
            self.favourite_count = int(s['favourites_count'])
        except KeyError:
            self.favourite_count = 0
        except ValueError:
            self.favourite_count = 101

        try:
            self.retweet_count = int(s['retweet_count'])
        except KeyError:
            self.retweet_count = 0
        except ValueError:
            self.retweet_count = 101


    def copy_json(self, s, user=None):
        #self.datetime = datetime.datetime(*(time.strptime(s['created_at'], '%a %b %d %H:%M:%S +0000 %Y')[0:6]))
        self.datetime = parse_twitter_date(s['created_at'])

        #TODO: update this to the new format in API 1.1
        try:
            geo_data = s['geo']

            if geo_data and geo_data['type'] == 'Point':
                self.latitude, self.longitude = geo_data['coordinates']
                self.has_geo = True
        except KeyError:
            self.has_geo = False
            self.geo_latitude = 0.0
            self.geo_longitude = 0.0

        if user:
            self.user = user
        else:
            self.user_id = s['user']['__pk__']

        try:
            self.favourite_count = int(s['favourites_count'])
        except KeyError:
            self.favourite_count = 0
        except ValueError:
            self.favourite_count = 101

        try:
            self.retweet_count = int(s['retweet_count'])
        except KeyError:
            self.retweet_count = 0
        except ValueError:
            self.retweet_count = 101

        self.internal_id = s['id_str']
        self.source = s['source'][:255]

        self.text = s['text'][:255]

        self.in_reply_to_user_id =  str(s.get('in_reply_to_user_id', ''))
        self.in_reply_to_status_id = str(s.get('in_reply_to_status_id', ''))

        self.language = s.get('lang', 'UNK')[:4]

        self.possibly_sensitive = bool(s.get('possibly_sensitive', False))


    def displayable_dict(self):
        return {
            'user': self.user.displayable_dict(),
            'id': self.pk,
            'id_str': self.pk,
            'text': self.beautify_html(self.text),
            'created_at': self.datetime.isoformat(),
            'internal_id': self.internal_id,
        }

    @classmethod
    def import_json(cls, tweet_json, user=None, save_existant=False, save_existant_user=False):
        try:
            status = Tweet.objects.get(internal_id=tweet_json['id_str'])
            if save_existant:
                status.update_json(tweet_json)
                status.save()

            return status, False
        except Tweet.DoesNotExist:
            status = Tweet()
            if not user:
                user = User.import_json(tweet_json['user'], save_existant=save_existant_user)

            status.copy_json(tweet_json, user)
            try:
                status.save()
            except Exception as e:
                print(tweet_json)
                raise e

            return status, True

    def __str__(self):
        return self.text

    def beautify_html(self, text=None):
        global URL_RE
        if text is None:
            text = self.text
        idx = 0
        match = URL_RE.search(text[idx:])

        if match:
            short_url = match.group()
            try:
                expanded_url = Url.objects.get(short=short_url).url
            except Url.DoesNotExist:
                print(short_url, 'does not exist')
                expanded_url = short_url

            span = match.span()

            domain = expanded_url.split('//')[1].split('/')[0]

            formatted_url = '<a target="_blank" href="{0}">{1}</a>'.format(expanded_url, domain)

            if formatted_url[0:3] == 'www':
                formatted_url = formatted_url[3:]

            text = text[0:span[0]] + formatted_url + text[span[1]:]

        tags = HASHTAG_RE.findall(text)
        for t in tags:
            text = text.replace(t, '<a href="https://twitter.com/hashtag/{0}" target="_blank">{1}</a>'.format(t[1:], t))

        mentions = MENTION_RE.findall(text)
        for m in mentions:
            text = text.replace(m, '<a href="https://twitter.com/intent/user?screen_name={0}" target="_blank">{1}</a>'.format(m[1:], m))

        return text


class FollowRelation(models.Model):
    source = models.ForeignKey(User, related_name='source_user', db_index=True)
    target = models.ForeignKey(User, related_name='target_user', db_index=True)


class ReTweet(models.Model):
    user = models.ForeignKey(User, related_name='retweeting_user', db_index=True)
    tweet_instance = models.ForeignKey(Tweet, related_name='rt_instance_tweet')
    source_tweet = models.ForeignKey(Tweet, related_name='source_tweet', db_index=True)
    datetime = models.DateTimeField(db_index=True)



