import gzip
import time
import os
from tweepy import StreamListener, Stream, OAuthHandler
from virtualornithology.analysis.importer import Importer


class _Listener(StreamListener):
    def __init__(self, fd, time_limit):
        """

        :param fd:
        :param time_limit: in seconds
        :return:
        """
        self.fd = fd
        self.time_limit = time_limit
        self.start_time = time.time()
        super(StreamListener, self).__init__()

    def on_data(self, data):
        self.fd.write(data)
        delta_time = time.time() - self.start_time

        if delta_time >= self.time_limit:
            return False
        return True


def crawl_tweets(filename, track=None, follow=None, locations=None, auth=None, api_keys=None, time_limit=None, log_level=None):
    with gzip.open(filename + '.part', 'wt') as f:
        listener = _Listener(f, time_limit)

        if not auth:
            auth = OAuthHandler(api_keys['consumer_key'], api_keys['consumer_secret'])
            auth.set_access_token(api_keys['access_token_key'], api_keys['access_token_secret'])

        stream = Stream(auth, listener)
        stream.filter(track=track, follow=follow, locations=locations)

    importer = Importer()
    tweet_count = importer(filename + '.part')
    os.rename(filename + '.part', filename)
    return tweet_count
