# coding=utf-8
from django.db import models
from django.core import serializers

try:
    import ujson as json
except ImportError:
    import json


class Timeline(models.Model):
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    json = models.TextField()

    @classmethod
    def from_tweets(cls, tweets, metadata=None, **kwargs):
        """
        :param tweets: a iterable of tweets
        :param kwargs: extra attributes to be considered for inclusion. should be json serializable.
        :return:
        """

        tl = cls()

        json_tweets = json.loads(serializers.serialize("json", tweets));
        for key, values in kwargs.items():
            if len(values) != len(json_tweets):
                continue

            for tweet, value in zip(json_tweets, values):
                tweet['fields'][key] = value

        tl.save()

        json_repr = {'metadata': metadata, 'tweets': json_tweets, 'pk': tl.pk, 'created_at': tl.datetime.isoformat()}
        tl.json = json.dumps(json_repr)
        tl.save()
        return tl


class Interaction(models.Model):
    session = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    data = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)


# feedback and user information

from django.forms import ModelForm
from django.forms.widgets import Textarea, Select

LIKERT_7_CHOICES = (
    (1, '1 - Sin valor.'),
    (2, '2 - Poco valor.'),
    (3, '3 - Ligero valor.'),
    (4, '4 - Moderado valor.'),
    (5, '5 - Bastante valor.'),
    (6, '6 - Mucho valor.'),
    (7, '7 - Máximo valor.'),
    (8, 'Prefiero no decirlo'),
)

TWITTER_USER_TYPES = (
    ('UNK', 'Prefiero no decirlo.'),
    ('passive', 'Tengo cuenta, pero solamente leo tweets de otras personas.'),
    ('meformer', 'Publico tweets de interés sólo para mí y mis amigos(as).'),
    ('informer', 'Trato de discutir, informar e informarme respecto a los temas que me interesan.'),
    ('mix', 'A veces publico tweets no informativos, y otras intento discutir, informarme e informar.'),
    ('none', 'No uso Twitter.'),
)

class Feedback(models.Model):
    text = models.TextField(verbose_name='¿Qué te gusta, qué no te gusta, y qué mejorarías del sitio?')
    datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    session = models.CharField(max_length=255, db_index=True)
    aesthetics = models.IntegerField(choices=LIKERT_7_CHOICES, default=8,
        verbose_name='De 1 a 7, ¿cómo valorarías la interfaz visual de la aplicación?')
    twitter_user_type = models.CharField(max_length=10, choices=TWITTER_USER_TYPES, default='UNK',
        verbose_name='¿Cuál de los siguientes perfiles se adapta más a tu uso de Twitter?')

class FeedbackForm(ModelForm):
    class Meta:
        model = Feedback
        fields = ('aesthetics', 'text', 'twitter_user_type')
        widgets = {
            'aesthetics': Select(attrs={'class': 'form-control'}),
            'text': Textarea(attrs={'class':'input-xxlarge form-control'}),
            'twitter_user_type': Select(attrs={'class': 'form-control'}),
        }

