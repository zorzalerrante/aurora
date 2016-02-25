{% if not mobile %}
var button_class = 'btn btn-default';
{% else %}
var button_class = 'btn btn-default btn-lg';
{% endif %}

var tweet_template = _.template('<li id="tweet-<%= fields.internal_id %>" class="media tweet tweet-wide">'
    + '<a target="_blank" class="pull-left" href="https://twitter.com/intent/user?screen_name=<%= fields.user.fields.screen_name %>" aria-label="<%= fields.user.fields.name %> (screen name: <%= fields.user.fields.screen_name %>)">'
    + '<img width="48" height="48" class="img-rounded" src="<%= fields.user.fields.profile_image_url %>">'
    + '</a>\n'
    + '<div class="media-body">'
    + '<p class="pull-right text-muted"><small><span class="glyphicon glyphicon-time"></span> <%= moment(fields.datetime).fromNow() %></small></p>'
    + '<a target="_blank" class="profile" href="https://twitter.com/intent/user?screen_name=<%= fields.user.fields.screen_name %>" aria-label="<%= fields.user.fields.name %> (screen name: <%= fields.user.fields.screen_name %>)">'
    + '<span class="full-name"><strong><%= fields.user.fields.name %></strong></span>&nbsp;'
    + '<span class="screen-name text-muted"><small>@<%= fields.user.fields.screen_name %></small></span>'
    + '</a>'
    + '<% if (fields.source_user != null) { %>'
    + '<p class="text text-retweet muted"><span class="glyphicon glyphicon-retweet"></span> Retweet a</span> <img width="16" height="16" class="img-rounded" src="<%= fields.source_user.fields.user.fields.profile_image_url %>"> &nbsp;'
    + '<a target="_blank" class="profile" href="https://twitter.com/intent/user?screen_name=<%= fields.source_user.fields.user.fields.screen_name %>" aria-label="<%= fields.source_user.fields.user.fields.name %> (screen name: <%= fields.source_user.fields.user.fields.screen_name %>)">'
    + '<strong><span class="screen-name">@<%= fields.source_user.fields.user.fields.screen_name %></span></strong>'
    + '</a>'
    + '</p>'
    + '<% } %>'
    + '<p class="text tweet-content"><%= fields.html %></p>'
    + '<% if (fields.hasOwnProperty(\'media\') && fields.media != null) { %>'
    + '<p><a href="<%= fields.media[0].fields.expanded_url %>" target="_blank"><img class="tweet-media img-responsive" src="<%= fields.media[0].fields.media_url %>" width="100%" /></a></p>'
    + '<% } %>'
    + '<p class="text-muted"><small>'
    + '<a target="_blank" href="https://twitter.com/intent/tweet?in_reply_to=<%= fields.internal_id %>" class="' + button_class +' reply-action web-intent" title="Reply"><span class="glyphicon glyphicon-share"></span> Responder</a>'
    + ' &nbsp; <a target="_blank" href="https://twitter.com/intent/retweet?tweet_id=<%= fields.internal_id %>" class="' + button_class +' retweet-action web-intent" title="Retweet"><span class="glyphicon glyphicon-retweet"></span> Retweet</a>'
    + ' &nbsp; <a target="_blank" href="https://twitter.com/intent/favorite?tweet_id=<%= fields.internal_id %>" class="' + button_class +' favorite-action web-intent" title="Favorite"><span class="glyphicon glyphicon-star"></span> Favorito</a>'
    + '</small></p></div></li>');

// tweet popovers
var detailed_tweet = null;

var showing_tweet_popover = function() {
    return detailed_tweet != null;
};

var prepare_tweet_popover = function(elem, tweet, placement, trigger) {
    if (placement == null) {
      placement = 'top';
    }
    console.log(elem, tweet);
    if (detailed_tweet != null) {
      $(detailed_tweet).popover('destroy');
        if (detailed_tweet === elem) {
            detailed_tweet = null;
            return;
        }
    }
    detailed_tweet = elem;
    $(detailed_tweet).popover({
      html: true,
      placement: placement,
      delay: 500,
      content: '<ul id="detailed-tweet-' + tweet.fields.internal_id + '" class="list-unstyled">' + tweet_template(tweet) + '</ul>',
      'trigger': trigger,
      container: 'body'
    });

    $(detailed_tweet).on('shown.bs.popover', function() {
        console.log(this);
        if (tweet.fields.hasOwnProperty('media') && tweet.fields.media != null) {
            var p = d3.select('#detailed-tweet-' + tweet.fields.internal_id).select('p.tweet-content');
            var img_width = p.node().clientWidth;
            var media = tweet.fields.media[0];
            var aspect_ratio = media.fields.aspect_ratio;

            d3.select(this).select('img.tweet-media')
                .style({'width': img_width, 'height': img_width / aspect_ratio})
                .attr({'width': img_width, 'height': img_width / aspect_ratio, 'alt': aspect_ratio});
        }
    });

    d3.selectAll('ul#detailed-tweet a').on('click', function() {
        console.log('tweet click', this, tweet);
        dispatcher.click.apply(this, [tweet, d3.select(this).attr('href')]);
    });
};

var show_tweet_popover = function() {
    $(detailed_tweet).popover('show');
};

var clear_tweet = function() {
    if (detailed_tweet != null) {
      $(detailed_tweet).popover('destroy');
      detailed_tweet = null;
    }
};

var media_aspect_ratio = function(media) {
    var aspect_ratio = 1.0;
    console.log(media.fields.sizes);
    if (media.fields.sizes.hasOwnProperty('large')) {
        aspect_ratio = 1.0 * media.fields.sizes.large.w / media.fields.sizes.large.h;
    } else if (media.sizes.hasOwnProperty('medium')) {
        aspect_ratio = 1.0 * media.fields.sizes.medium.w / media.fields.sizes.medium.h;
    } else if (media.fields.sizes.hasOwnProperty('small')) {
        aspect_ratio = 1.0 * media.fields.sizes.small.w / media.fields.sizes.small.h;
    }

    return aspect_ratio;
};