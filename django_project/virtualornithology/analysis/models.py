from django.db import models
from virtualornithology.birds.models import User, Tweet
from virtualornithology.places.models import Location


class UserFeatures(models.Model):
    user = models.ForeignKey(User, related_name='characterization', unique=True)
    first_name = models.CharField(max_length=255, default='')
    last_name = models.CharField(max_length=255, default='')
    domain = models.CharField(max_length=255)
    friends_followers_ratio = models.FloatField(default=0.0)
    location_depth_0 = models.ForeignKey(Location, null=True, related_name='location_depth_0', db_index=True)
    location_depth_1 = models.ForeignKey(Location, null=True, related_name='location_depth_1', db_index=True)
    location_depth_2 = models.ForeignKey(Location, null=True, related_name='location_depth_2', db_index=True)
    location_depth_3 = models.ForeignKey(Location, null=True, related_name='location_depth_3', db_index=True)
    datetime = models.DateTimeField(null=True, db_index=True)

    def set_location(self, location):
        self.location_depth_0 = None
        self.location_depth_1 = None
        self.location_depth_2 = None
        self.location_depth_3 = None

        if location:
            for i in range(location.depth, -1, -1):
                setattr(self, 'location_depth_{0}'.format(location.depth), location)
                parent = location.parent
                location = parent


class TweetFeatures(models.Model):
    tweet = models.ForeignKey(Tweet, related_name='characterization', unique=True)
    length = models.IntegerField(default=0)
    manual_rt = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    source_user = models.ForeignKey(UserFeatures, related_name='source_user')
    target_user = models.ForeignKey(UserFeatures, related_name='target_user', null=True)
    count_mentions = models.IntegerField(default=0)
    count_hashtags = models.IntegerField(default=0)
    count_keywords = models.IntegerField(default=0)
    count_links = models.IntegerField(default=0, db_index=True)
    count_media = models.IntegerField(default=0, db_index=True)
    count_rts = models.IntegerField(default=0, db_index=True)
    datetime = models.DateTimeField(null=True, db_index=True)
