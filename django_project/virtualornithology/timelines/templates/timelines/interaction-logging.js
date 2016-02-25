// event tracking
{% include 'javascript/interaction-logging.js' %}

var timeline_pk = null;

var log_event = function(current_event) {
    _.defaults(current_event, {timeline: timeline_pk, target : '', tweet: null});
    push_event(current_event);
};

var dispatcher = d3.dispatch('loaded', 'details', 'click', 'fav', 'rt', 'reply');

['details', 'click', 'fav', 'rt', 'reply'].forEach(function(event) {
    dispatcher.on(event + '.base', function(tweet, src) {
        console.log(event, tweet);
        log_event({name: 'timeline_' + event, tweet: tweet.fields.internal_id, href: src, location: tweet.fields.geolocation});
    });
});

dispatcher.on('loaded.base', function(screen) {
    console.log(event, screen);
    log_event({'name': 'loaded', 'screen_width': screen.width, 'screen_height': screen.height, 'hash': window.location.hash});
});
