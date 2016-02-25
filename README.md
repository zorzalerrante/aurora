# Aurora Twittera

This repository contains the source of the "Aurora Twittera" by me ([Eduardo Graells-Garrido](https://twitter.com/carnby)), done during my PhD thesis (2011-2016). +
You can see this project running live at http://auroratwittera.cl.

The purpose of AT is to build visualization of algorithmic results based on Tweets, aimed at encouraging behavioral change.
Particularly, it has focused on two different problems:

  1. In a geographically centralized country (Chile), how can we encourage exposure to geographically diverse content in Twitter?
  2. Since people connect with like-minded others due to homophily, how can we encourage exposure to a more diverse group of people?

In both cases, this project implements algorithms that run on Twitter data, and visualizations that allow users to explore
the algorithmic results. The algorithms are aimed at providing non-biased information, and the visualizations are aimed at
allowing users to break-free of cognitive and social biases that distort their decision-making process.

This project has been used in the following publications:

  * [Balancing diversity to counter-measure geographical centralization in microblogging platforms](http://dl.acm.org/citation.cfm?id=2631823) by
  Eduardo Graells-Garrido and Mounia Lalmas. Presented at ACM Hypertext'14.
  * [Encouraging Diversity- and Representation-Awareness in Geographically Centralized Content](http://arxiv.org/abs/1510.01920)
  by Eduardo Graells-Garrido, Mounia Lalmas and Ricardo Baeza-Yates. To be presented at ACM Intelligent User Interfaces'16.
  * [Finding Intermediary Topics Between People of Opposing Views: A Case Study](http://arxiv.org/abs/1506.00963) by Eduardo Graells-Garrido, Mounia Lalmas and
  Ricardo Baeza-Yates. Presented at the Social Personalisation and Search Workshop, held jointly with SIGIR'15.
  * [Data Portraits and Intermediary Topics: Encouraging Exploration of Politically Diverse Profiles](http://arxiv.org/abs/1601.00481)
  by Eduardo Graells-Garrido, Mounia Lalmas and Ricardo Baeza-Yates. To be presented at ACM Intelligent User Interfaces'16.

Even though a previous, less clean version of this code has been running
for more than a year on a production server, the code is not production-ready by any means - it was constructed iteratively
during my PhD.

This document explains how to setup and run this project, but a more technical view is still missing.

Note that AT works with Python 3.4.

## Installation Steps

AT is a django app, so first make sure that you have a server that allows to run django apps as well as serving static files.
The requirements.txt file contains the dependencies of the project, which you can install using pip:

```
$ pip install -r requirements.txt
```

Then you have to edit the settings.py file, as with any django project.

### Project Data and Data Folders

First, you need a "project folder" which will contain several text and database files (see folder `projects/cl`):

  * stopwords/es.txt - a list of stopwords for Spanish (note that the filename depends on the allowed languages setting).
  * stopwords/other.txt - a list of other stopwords to consider (e.g., non-words, English words, etc).
  * allowed_sources.txt - a list of allowed Twitter clients.
  Currently, we discard tweets that are automatically generated (but we accept a non-automatic retweet of an automatic tweet!).
  * allowed_time_zones.txt - a list of allowed time zones. We discard tweets that pass the filters but are from other time-zones.
  * discard_keywords.txt - black-list of keywords, screen names and hashtags.
  * discard_locations.txt - black-list of locations (this is checked against the self-reported locations in user profiles).
  * discard_time_zones.txt - black-list of time zones. For instance, there are other countries that share the same offset than yours.
  * discard_urls.txt - black-list of URLs in tweets. For instance, check-ins are discarded.
  * keywords.txt - list of keywords to query the Twitter API.
  * places_cl.json - a django-serialized list of locations (via the dumpdata command). See the places/models.py file to see the structure.
  Basically, this is an ad-hoc gazzetteer.

One you have all these files, proceed to create the following folders that will hold crawled data:

```
/home/egraells/aurora/data/portraits/users
/home/egraells/aurora/data/portraits/it-topics
/home/egraells/aurora/data/stream
```

These paths are configurable in your settings file.

### Database

Setup a database using PostgreSQL, update the settings file accordingly, and then run:

```
$ python manage.py makemigrations
$ python manage.py makemigrations birds
$ python manage.py makemigrations analysis
$ python manage.py makemigrations portraits
$ python manage.py makemigrations interactions
$ python manage.py makemigrations places
$ python manage.py makemigrations timelines
$ python manage.py migrate
```

This will create all the necessary tables to hold AT data.

### Initial Data

Load initial (location) data.

```
$ python manage.py loaddata projects/cl/places_cl.json
Installed 2691 object(s) from 1 fixture(s)
```

Since this data was made ad-hoc by manually inserting rows in a database, you are on your own if you need a gazzetteer for
a different country.

### Create Twitter Account and Application

You need a Twitter account for the application to work. For instance, in AT is [@todocl](https://twitter.com/todocl).

After you have created your account, go to https://apps.twitter.com and create an application. By doing so, the application will have a _consumer key_ and a
_consumer_secret_. On the same page you can generate the authorization keys for your Twitter account, to be able to do APi requests
on your behalf. Put those keys in the settings file like this:

```
TWITTER_USER_KEYS = {
  'consumer_key': 'your_consumer_key',
  'consumer_secret': 'your_consumer_secret',
  'access_token_key': 'your_access_token_key',
  'access_token_secret': 'your_access_token_secret'
}
```
## Components

### Geographically Diverse Timelines

So, you have configured everything... it's time to crawl some tweets and generate some geographically diverse timelines, to
encourage users to explore de-centralized timelines (Chile is a centralized country, and people tend to mention and retweet more
people from its capital than what is expected given the population distribution).

To crawl tweets you need to run the filter_stream command like this:

```
$ python manage.py filter_stream --minutes 5
```

This will run the script for 5 minutes. As query keywords and parameters, the script will use the data sources
you indicated on the settings file. The output will be gzipped files in the data folder you indicated, with one JSON-encoded
tweet per line. The script will also import the accepted tweets (according to the project settings) into the database.

If you have gzipped Tweets and you want to import them into the database, you can run the following command:

```
$ python manage.py process_stream_files --path '/media/egraells/113A88F901102CA6/data/aurora/stream-data/201602/*.gz'
```

Note that the path is a string. Otherwise, bash will expand the parameter. The script is not prepared for that.

Once you have enough tweets, you can generate a timeline with the following command:

```
$ python manage.py generate_timeline --hours 10 --turns 10 --size 20
```

You can see an example of timeline in http://auroratwittera.cl/timelines

### Data Portraits

Data Portraits are visual representations of the topics that represent an user's presence on Twitter. We use these
portraits as a context to display recommendations (_who to follow_) based on an algorithm that discovers _intermediary
topics_ between users.

The application allows any Twitter user to connect with the system and create their profiles through the website UI.
When this happens, the application crawls his/her tweets, stores them on the filesystem (to avoid mixing portrait and
geographically diverse tweets), and then creates the portrait. As recommendation candidates, we consider all users who
are present on the database.

Additionally, you can create demo portraits that will be showcased on the homepage of the project, by using the following
command:

```
$ python manage.py create_demo_portrait --screen_name todocl
```

Note that portrait creation, either through the website (an active portrait) or the command line (a demo portrait), only
stores meta-data into the database. To actually crawl tweets you need to run the crawler:

```
$ python manage.py crawl_portrait_data
```

Again, it is important to know that portrait tweets are not saved on the database, because we do not
want to mix portrait tweets (which may be private, or not related to the country of interest) with geographically diverse
ones. They are stored in the portraits/users folder that you created earlier.

As mentioned, portraits can contain _who to follow_ recommendations. For this you need to have a working recommendation model.
To generate the intermediary topics model you need to run the following command:

```
$ python manage.py generate_intermediary_topics_model
```

Note that you must have tweets in the database, because the model is created using those tweets.


## Server Setup

Assuming that you have everything working as expected on the server (django, nginx, gunicorn, etc), then the question
you might have now is: _how do I run this automatically on the server?_
My way of doing this right now is by using crontab
and supervisord.

Here is the crontab example from the current version of the project at http://auroratwittera.cl:

```
# m h  dom mon dow   command
0 0 * * 2,5,7 cd /home/django/django_project && /usr/bin/python manage.py generate_intermediary_topics_model --days 2 --percentile 75 >> /home/django/it_model.log 2>&1
0 2 * * * cd /home/django/django_project && /usr/bin/python manage.py delete_old_tweets --days 2 && vacuumdb -f -v >> /home/django/vacuum.log 2>&1
0 1 * * * cd /home/django/django_project && /usr/bin/python manage.py check_portrait_permissions >> /home/django/permissions.log 2>&1
*/5 * * * * cd /home/django/django_project && /usr/bin/python manage.py filter_stream --minutes 5 >> /home/django/crawl.log 2>&1
0 6,7,8,9,10,11,12,13,14,15,16,17,18,19,20 * * * cd /home/django/django_project && /usr/bin/python manage.py generate_timeline --post_timeline --hours 3 --turns 10 --update_users --size 60 >> /home/django/timeline.log 2>&1
```

Note that:

  * The intermediary topics model is generated three times a week.
  * Every day at 2AM, tweets older than two days are deleted, to keep the database small and with fresh users only.
  * Every day at 1AM, the system checks whether someone removed app permissions from Twitter, and deactivates portraits if needed.
  * Every 5 minutes the tweet crawler is restarted. The crawler stops after 5 minutes.
  * Every hour from 6AM to 8PM UTC a geographically diverse timeline is generated. Note the `--post_timeline` argument:
  this indicates that your account associated with the system will retweet the tweets selected for inclusion into the
  geographically diverse timeline.

You might wonder where is the crawler of portrait tweets, because it is not on the crontab. It's actually running as a daemon within `supervisor`. This is
the relevant configuration:

```
[program:portrait_crawl]
command=/usr/bin/python manage.py crawl_portrait_tweets --n_recommendations 50 --wait_time 30 --renew_user_data --n_times 60 --notify --notify_after 7 --update_every 7
directory=/home/django/django_project
user=django
stdout_logfile=/home/django/portrait_crawl.log
autorestart=true
```

## What else?

At this point you have a running system! But there are things not covered on this document that, although explained on the research
papers, are not explicit here, and will be updated in the future. These include:

  * Explanation of logging of interaction data and condition assignment to users.
  * Structure of the applications (there are several django application modules in the project).
  * Explanation of the implementation of the published algorithms.
  * Clean-up of unused files.
  * Anything else...? Please, feel free to open issues.

## Credits

  * We include the following Javascript libraries: [d3.js](http://d3js.org), [underscore.js](http://underscorejs.org/),
  [jQuery](http://jquery.com/), [masonry](http://masonry.desandro.com/), [imagesloaded](https://desandro.github.io/imagesloaded/),
  [moment.js](http://momentjs.com/), [spin](http://fgnass.github.io/spin.js/), [seedrandom](https://github.com/davidbau/seedrandom),
  [require.js](http://requirejs.org/), [d3-queue](https://github.com/d3/d3-queue)(but the old version, queue.js),
  [PNotify](http://sciactive.github.io/pnotify/), [d3-cloud](https://github.com/jasondavies/d3-cloud).
  * We include [Bootstrap 3.3.6](http://getbootstrap.com).
  * We use two functions and a color palette from the [D3Plus](http://d3plus.org/) project.
  * Tokenization uses code from http://sentiment.christopherpotts.net/code-data/happyfuntokenizing.py.

## Citing Aurora Twittera

If you use this code, please cite the relevant paper from the list at the beginning of this list. For instance, if you
work with the recommendation model and visualization, cite the Data Portraits paper. If you work with the implementation
of the filtering algorithm for diverse timelines, cite the "Balancing Diversity" paper. Otherwise, please cite the
"Encouraging Diversity- and Representation- Awareness" paper.

## License

The MIT License (MIT)
Copyright (c) 2016 Eduardo Graells-Garrido

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
