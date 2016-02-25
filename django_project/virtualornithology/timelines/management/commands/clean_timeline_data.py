from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from virtualornithology.timelines.models import Timeline, Interaction


class Command(BaseCommand):
    def handle(self, *args, **options):
        Interaction.objects.all().delete()
        limit_date = datetime.now() - timedelta(days=1)
        Timeline.objects.filter(datetime__lt=limit_date).delete()
