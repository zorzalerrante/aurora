# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
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
        # TODO: delete files
        #path = '{0}/users'.format(settings.PORTRAIT_FOLDER)

        screen_name = options.get('screen_name', None)

        if not screen_name:
            print('no user')
            return

        portraits = Portrait.objects.filter(auth_screen_name=screen_name)
        portraits.delete()
