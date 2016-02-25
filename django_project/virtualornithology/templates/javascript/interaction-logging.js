
var user_events = [];
var n_seconds = 3 * 1000;
var ping_window = 10 * 1000;
var timer_id = null;

var send_events = function() {
    {% if record_interactions %}
    if (user_events.length == 0) {
        //log_event({'name': 'ping'});
        return;
    }

    aurora.xhr_post(
        "{%  url 'interactions:record-event' %}",
        {'source_app': '{{ current_app }}', 'user_events': user_events},
        function(error, response) {
            console.log(error);
            console.log(response);
            if (response != null) {
                console.log('user events cleared');
                user_events = [];
            } else {
                //alert('error!' + JSON.stringify(error));
            }
        });
    {% endif %}
};

// an external function defined by each app, named log_event, calls this function after event pre-processing
var push_event = function(current_event) {
    current_event['{{ client_datetime_var }}'] = moment().format();
    user_events.push(current_event);
    console.log(user_events);
};

window.onbeforeunload = function() {
    {% if record_interactions %}
    if (user_events.length) {
        log_event({'name': '{{ current_app }}_closed'});
        send_events();
    }
    {% endif %}
};


var bind_twitter_events = function() {
    try {
        if (twttr) {
            twttr.ready(function (twttr) {
                /*
                twttr.events.bind('click', function (event) {
                    console.log('click', this, event);
                    log_event({'name': 'twt_click'});
                });
                */

                twttr.events.bind('tweet', function (event) {
                    console.log('tweet', this, event);
                    log_event({'name': 'twt_reply'});
                });

                twttr.events.bind('follow', function (event) {
                    var followed_user_id = event.data.user_id;
                    var followed_screen_name = event.data.screen_name;

                    console.log('follow', this, event);
                    log_event({'name': 'twt_follow', 'target': followed_user_id});
                });

                twttr.events.bind('retweet', function(event) {
                    var retweeted_tweet_id = event.data.source_tweet_id;
                    console.log('retweet', this, event);
                    log_event({'name': 'twt_retweet', 'target': retweeted_tweet_id});
                });

                twttr.events.bind('favorite', function(event) {
                    var favorited_tweet_id = event.data.tweet_id;
                    console.log('favorite', this, event);
                    log_event({'name': 'twt_fav', 'target': favorited_tweet_id});
                });

            });
        }
    } catch(e) {
        console.log('twttr not loaded');
    }
};

var ping_fn = function() {
    if (user_events.length == 0) {
        log_event({'name': 'ping'});
    }
    ping_window *= 2;
    timeout_fn();
};

var timeout_fn = function() {
    window.setTimeout(ping_fn, ping_window);
};

var init_interaction_logging = function(include_twitter) {
    timer_id = window.setInterval(send_events, n_seconds);
    timeout_fn();
};
