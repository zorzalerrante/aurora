# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option
import glob
import logging
from virtualornithology.analysis.importer import Importer


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--path',
            action='store',
            dest='path',
            default=None,
            type='string',
            help='Path to source files to be imported.'),
        make_option('--step',
            action='store',
            dest='step',
            default=10000,
            type='int',
            help='Number of tweets per import step.'),
        make_option('--log',
            action='store',
            dest='log_level',
            default=30,
            type='int',
            help='Log level.'),
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=options['log_level'])

        if options['path']:
            files = glob.glob(options['path'])
        else:
            files = glob.glob(settings.DATA_FOLDER + '/' + settings.STREAMING_FILE_PREFIX + '*.gz')

        settings.CHARACTERIZATION_STEP = options['step']

        print('# files:', len(files))

        importer = Importer()

        for filename in files:
            print(filename)

            try:
                importer(filename)
                print('{0}: accepted {1} tweets'.format(filename, importer.total_tweet_count))
            except IOError as e:
                print('[ERROR] {0}: {1}'.format(filename, e))
