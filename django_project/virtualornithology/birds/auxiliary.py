# -*- coding: utf-8 -*-
import unicodedata
import datetime
import time
import pytz
import gc
import sys
import regex as re

# This code is from http://sentiment.christopherpotts.net/
# http://sentiment.christopherpotts.net/code-data/happyfuntokenizing.py
# This particular element is used in a couple ways, so we define it
# with a name:
emoticon_string = r"""
    (?:
      [<>]?
      [:;=8]                     # eyes
      [\-o\*\']?                 # optional nose
      [\)\]\(\[dDpP/\:\}\{@\|\\] # mouth
      |
      [\)\]\(\[dDpP/\:\}\{@\|\\] # mouth
      [\-o\*\']?                 # optional nose
      [:;=8]                     # eyes
      [<>]?
    )"""

# The components of the tokenizer:
regex_strings = (
    # URLS
    r"""(https?://[-A-Za-z0-9+&@#/%?=~_\|!:,.;]*[-A-Za-z0-9+&@#/%=~_()|])""",
    # Phone numbers:
    r"""
    (?:
      (?:            # (international)
        \+?[01]
        [\-\s.]*
      )?
      (?:            # (area code)
        [\(]?
        \d{3}
        [\-\s.\)]*
      )?
      \d{3}          # exchange
      [\-\s.]*
      \d{4}          # base
    )"""
    ,
    # Emoticons:
    emoticon_string
    ,
    # HTML tags:
     r"""<[^>]+>"""
    ,
    # Twitter username:
    r"""(?:[\w_]*@[\w_]+)"""
    ,
    # Twitter hashtags:
    r"""(?:\#+[\w_]+[\w\'_\-]*[\w_]+)"""
    ,
    # Remaining word types:
    r"""
    (?:[\w_][\w'\-_]+[\w_])       # Words with apostrophes or dashes.
    |
    (?:[+\-]?\d+[,/.:-]\d+[+\-]?)  # Numbers, including fractions, decimals.
    |
    (?:[\w_]+)                     # Words without apostrophes or dashes.
    |
    (?:\.(?:\s*\.){1,})            # Ellipsis dots.
    |
    (?:\S)                         # Everything else that isn't whitespace.
    """
    )

######################################################################
# This is the core tokenizing regex:
tokenize_re = re.compile(r"""(%s)""" % "|".join(regex_strings), re.VERBOSE | re.I | re.UNICODE)
emoticon_re = re.compile(regex_strings[1], re.VERBOSE | re.I | re.UNICODE)


def queryset_iterator(queryset, chunksize=50000):
    """
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.

    Source: https://djangosnippets.org/snippets/1949/
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


def parse_twitter_date(str):
    naive_datetime = datetime.datetime(*(time.strptime(str, '%a %b %d %H:%M:%S +0000 %Y')[0:6]))
    return pytz.timezone("UTC").localize(naive_datetime)


# from http://farmdev.com/talks/unicode/
if sys.version_info < (3,):
    def to_unicode_or_bust(obj, encoding='utf-8'):
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj
else:
    def to_unicode_or_bust(obj, encoding='utf-8'):
        return obj


def remove_accents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def normalize_str(s, encoding='utf-8'):
    s = to_unicode_or_bust(s, encoding).lower().strip()
    s = 'ñ'.join(map(remove_accents, s.split(u'ñ')))
    return s


def tokenize(s, preserve_case=False):
    global tokenize_re
    words = [w[0] for w in tokenize_re.findall(s)]
    # Possible alter the case, but avoid changing emoticons like :D into :d:
    if not preserve_case:
        words = map((lambda x : x if emoticon_re.search(x) else x.lower()), words)
    return words


def load_list_from_file(filename, normalize_text=False, container=set, sep='\n'):
    items = []
    with open(filename, 'rt') as f:
        items.extend(f.read().split(sep))

    if normalize_text:
        return container(filter(lambda x: x, map(normalize_str, items)))
    else:
        return container(filter(lambda x: x, map(lambda x: x.strip(), items)))


def save_list_in_file(list, filename):
    members = set(w for w in list if w)
    with open(filename, 'wt') as f:
        f.write('\n'.join(members))
