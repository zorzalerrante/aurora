from django.db import models


class Portrait(models.Model):
    auth_screen_name = models.CharField(max_length=100, db_index=True, default='')
    auth_id_str = models.CharField(max_length=100, default='')
    public_access_enabled = models.BooleanField(default=True)
    access_token = models.CharField(max_length=255)
    access_token_secret = models.CharField(max_length=255)
    demo_portrait = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    last_update_date = models.DateTimeField(null=True, default=None)
    last_tweet_date = models.DateTimeField(null=True, default=None)
    last_tweet_id = models.CharField(max_length=255, null=True, default=None)
    last_access = models.DateTimeField(null=True, default=None)
    portrait_content = models.TextField(null=True, default=None)
    portrait_preferences = models.TextField(null=True, default=None)
    portrait_recommendations = models.TextField(null=True, default=None)
    user_data = models.TextField(null=True)
    has_political_content = models.NullBooleanField(null=True, default=None)
    condition_ui = models.CharField(max_length=25, null=True, default=None, choices=(('baseline', 'Baseline'), ('bubbles', 'Circle Packing')))
    condition_rec = models.CharField(max_length=25, null=True, default=None, choices=(('kls', 'Kullback-Leibler Similarity'), ('it_score', 'Intermediary Topics Score')))
    # some users remove permissions. we delete them.
    active = models.BooleanField(default=True)
    # feature on the home page
    featured_on_home = models.BooleanField(default=False)
    # last time user was mentioned
    last_notification_date = models.DateTimeField(null=True, default=None)
