from django.core.management.base import BaseCommand
from virtualornithology.timelines.models import Interaction, Timeline, TestUser


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(Timeline.objects.all().delete())
        print(Interaction.objects.all().delete())
        print(TestUser.objects.all().delete())