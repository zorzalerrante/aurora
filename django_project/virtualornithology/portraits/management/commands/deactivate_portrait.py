# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from optparse import make_option
from virtualornithology.portraits.models import Portrait


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--screen_name',
            action='store',
            dest='screen_name',
            default=None,
            type='str',
            help='User screen name.'),
    )

    def handle(self, *args, **options):
        screen_name = options.get('screen_name', None)

        if not screen_name:
            print('no user')
            return

        portrait = Portrait.objects.get(auth_screen_name=screen_name)
        portrait.active = False
        portrait.last_update_date = None
        portrait.save()
