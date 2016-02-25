from django.db import models
from virtualornithology.birds.auxiliary import normalize_str
import regex as re

_non_word = re.compile('[\W\s]+')


class Location(models.Model):
    parent = models.ForeignKey('self', db_index=True, null=True)
    depth = models.IntegerField(db_index=True, default=0)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    name = models.CharField(db_index=True, max_length=255)
    code = models.CharField(db_index=True, max_length=10, default='')
    iso_code = models.CharField(db_index=True, max_length=3, default='')
    population = models.IntegerField(default=0)
    area_in_km2 = models.FloatField(default=0.0)
    time_zone = models.CharField(max_length=50, default='')

    def __unicode__(self):
        return u'{0} [depth={1}]'.format(self.name, self.depth)

    def add_child(self, name):
        child = Location(parent=self, depth=self.depth+1, name=name)
        child.save()
        child.add_name(name)
        return child

    def add_name(self, other_name):
        normalized_name = KnownName.prepare_name(other_name)

        try:
            known_name = KnownName.objects.get(normalized_name=normalized_name, location=self)
        except KnownName.DoesNotExist:
            known_name = KnownName(name=other_name, normalized_name=normalized_name, location=self)
            known_name.save()

        return known_name

    def normalize(self, desired_depth):
        if desired_depth < 0 or self.depth < desired_depth:
            return None

        current = self.parent
        while current is not None:
            if current.depth == desired_depth:
                return current
            current = current.parent


class KnownName(models.Model):
    location = models.ForeignKey(Location, related_name='known_name', db_index=True)
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, db_index=True)

    @classmethod
    def prepare_name(cls, name):
        normalized_name = normalize_str(name)
        return _non_word.sub(u' ', normalized_name)


class BoundingBox(models.Model):
    location = models.ForeignKey(Location, related_name='source_location')
    latitude_sw = models.FloatField()
    latitude_se = models.FloatField()
    latitude_nw = models.FloatField()
    latitude_ne = models.FloatField()
    longitude_sw = models.FloatField()
    longitude_se = models.FloatField()
    longitude_nw = models.FloatField()
    longitude_ne = models.FloatField()
