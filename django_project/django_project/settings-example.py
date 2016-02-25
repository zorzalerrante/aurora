"""
Django settings for django_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'YOUR_SUPER_SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['auroratwittera.cl', '104.236.160.149', '0.0.0.0']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'social.apps.django_app.default',
    'virtualornithology.birds',
    'virtualornithology.analysis',
    'virtualornithology.places',
    'virtualornithology.timelines',
    'virtualornithology.portraits',
    'virtualornithology.interactions'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'virtualornithology.portraits.middleware.BirdsMiddleWare'
)

AUTHENTICATION_BACKENDS = (
    'social.backends.twitter.TwitterOAuth',
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

)

ROOT_URLCONF = 'django_project.urls'

WSGI_APPLICATION = 'django_project.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'virtualornithology.birds.processors.ornithology_context',
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    )

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'YOUR DATABASE NAME',
        'USER': 'USER',
        'PASSWORD': 'PASSWORD',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    # 'social.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social.pipeline.user.user_details',

    # CREATE THE PORTRAIT IF NEEDED
    'virtualornithology.portraits.tasks.portrait_details'
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.dirname(os.path.realpath(__file__)) + '/../virtualornithology/templates',
)

# END OF DJANGO STUFF
# START OF AURORA STUFF

# @carnby with prototype app
TWITTER_USER_KEYS = {
    'consumer_key': 'TWITTER_CONSUMER_KEY',
    'consumer_secret': 'TWITTER_CONSUMER_SECRET',
    'access_token_key': 'YOUR_ACCOUNT_TOKEN_KEY',
    'access_token_secret': 'YOUR_ACCOUNT_TOKEN_SECRET'
}

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username']
SOCIAL_AUTH_TWITTER_KEY = TWITTER_USER_KEYS['consumer_key']
SOCIAL_AUTH_TWITTER_SECRET = TWITTER_USER_KEYS['consumer_secret']

# every X minutes we should restart the stream (minutes). This affects the time-out of the filter_stream command.
# but it's not automatic. check the README
STREAMING_SCRIPT_DURATION = 5

# how many tweets to process at once in the importing process
CHARACTERIZATION_STEP = 1000

# whether to discard users with locations that do not appear in our database
REJECT_UNKNOWN_LOCATIONS = False

# the path to the virtualornithology folder
ORNITHOLOGY_PATH = '/home/egraells/resources/aurora/django_project/virtualornithology'

# path to the project folder, containing all the project inputs
PROJECT_PATH = '/home/egraells/resources/aurora/projects/cl'

# these keywords are used in the filter_stream command to crawl tweets
TWITTER_SEARCH_KEYWORDS_FILE =  PROJECT_PATH + '/keywords.txt'

# bounding box (in this case, continental Chile) to search for geo-located tweets
TWITTER_SEARCH_LOCATION_BBOX = [-73.655740,-37.944243,-72.090433,-34.879482]

# where on earth ID of Chile
TWITTER_SEARCH_WOEID = 23424782

# tweets that contain these keywords (including hashtags and screen names) are discarded
TWITTER_DISCARD_KEYWORDS = PROJECT_PATH + '/discard_keywords.txt'

# tweets by users from these locations are discarded
TWITTER_DISCARD_LOCATIONS = PROJECT_PATH + '/discard_locations.txt'

# tweets with links to these URLs are discarded (e.g., check-ins)
TWITTER_DISCARD_URLS = PROJECT_PATH + '/discard_urls.txt'

# accepted languages. Nowadays tweets usually include language. When they do not, we estimate it using langid
TWITTER_ACCEPTED_LANGUAGES = set(['es'])

# some settings for the front-end site.
AURORA_SETTINGS = {
    'ORNITHOLOGY_THEME': 'bootstrap',
    'ORNITHOLOGY_TITLE': 'La Aurora Twittera de Chile',
    'sidebar_width': 160,
    'sidebar_color': 'linen',
    'sidebar_text': 'snow',
    'sidebar_head_text': 'antiquewhite',
    'sidebar_background': 'darkslategray'
}

# a prefix for the crawled files by the filter_stream command
STREAMING_FILE_PREFIX = 'general_2014'

# the screen name of the main account that does the crawling (e.g., todocl in our study)
# note that we crawl tweets that satisfy the filters AND those by accounts followed by YOUR_ACCOUNT
STREAMING_SOURCE_ACCOUNT = 'YOUR_ACCOUNT'

# a list of additional accounts to consider when crawling tweets
STREAMING_FOLLOW_ACCOUNTS = None

# where to store the data in each application.
# tweets crawled by filter_stream
DATA_FOLDER = '/media/egraells/752c8c13-336e-435f-8afb-e69408bdcdb4/aurora/stream'

# data portrait files. note that you need two sub-folders: it-topics and users.
PORTRAIT_FOLDER = '/media/egraells/752c8c13-336e-435f-8afb-e69408bdcdb4/aurora/portraits'

