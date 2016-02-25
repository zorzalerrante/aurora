{% include 'javascript/interaction-logging.js' %}

var log_event = function(current_event) {
    current_event['portrait_current'] = {{ portrait_current_pk }};
    push_event(current_event);
};
