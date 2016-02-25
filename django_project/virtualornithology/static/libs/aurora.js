/**
 * Aurora.js
 * This file contains auxiliary functions for Aurora Twittera de Chile.
 * Many of these functions have been written by someone else. I have given credit where credit is due at each
 * corresponding function.
 *
 * Author: Eduardo Graells-Garrido, @carnby
 * License: 3-clause BSD.
 */

define('aurora', ['d3', 'spin', 'pnotify', 'pnotify.buttons', 'pnotify.nonblock'], function(d3, Spinner, PNotify) {
    var aurora = {};

    aurora.get_cookie = function(name) {
        /**
         * Source: django documentation @ https://docs.djangoproject.com/en/dev/ref/csrf/
         */
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    aurora.xhr_post = function(url, params, callback) {
        /**
         * Sends a POST request to the specified URL. Conversion to string or JSON is handled by the function.
         * :param params: An object. Example: {'user_id': 9, 'choices': ['vanilla', 'chocolate']}
         */
        var xhr = d3.xhr(url);

        var cookie_value = aurora.get_cookie('csrftoken');

        if (cookie_value == null) {
            console.log('cookies disabled!');
            return;
        }

        xhr.header('X-CSRFToken', cookie_value);
        xhr.header('Content-type', 'application/x-www-form-urlencoded');

        var post_params = d3.entries(params).map(function(d) {
            var value = typeof d.value === 'object' ? JSON.stringify(d.value) : d.value;
            return encodeURIComponent(d.key) + '=' + value;
        });

        //console.log('post params', post_params);

        var post_data = post_params.join('&');
        //console.log('post data', post_data);

        xhr.post(post_data, function(error, response) {
            //console.log('query');
            //console.log('error', error);
            //console.log('response', response);
            callback(error, JSON.parse(response.response));
        });
    };

    aurora.spinner = function(spinner_target_name) {
        /**
         * Creates a spinner logo inserted into the specific target (note that IDs do not start with #).
         * Useful for loading event feedback.
         */
        var opts = {
            lines: 13,
            length: 20,
            width: 10,
            radius: 30,
            corners: 1,
            rotate: 0,
            direction: 1,
            color: '#afafaf',
            speed: 1,
            trail: 60,
            shadow: false,
            hwaccel: false,
            className: 'spinner',
            zIndex: 2e9,
            top: '50%',
            left: '50%'
        };

        var target = document.getElementById(spinner_target_name);
        return  new Spinner(opts).spin(target);
    };

    aurora.notify = function(popup_title, popup_text, popup_type) {
        /**
         * Creates a stacked notification on the corner of the screen.
         */
        new PNotify({
            title: popup_title,
            text: popup_text,
            delay: 5000,
            type: popup_type,
            nonblock: true,
            sticker: false,
            closer_hover: false,
            mouse_reset: false
        });
    };

    aurora.es_locale = function() {
        /**
         * An array to localize d3.js to spanish.
         * See https://github.com/mbostock/d3/wiki/Localization
         */
        return d3.locale({
            "decimal": ".",
            "thousands": ",",
            "grouping": [3],
            "currency": ["$", ""],
            "dateTime": "%a %b %e %X %Y",
            "date": "%m/%d/%Y",
            "time": "%H:%M:%S",
            "periods": ["AM", "PM"],
            "days": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
            "shortDays": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sab", "Dom"],
            "months": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
            "shortMonths": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        });
    };

    aurora.end_all = function(transition, callback) {
        /**
         * Calls the callback at the end of a transition.
         * Source: Mike Bostock https://groups.google.com/forum/#!msg/d3-js/WC_7Xi6VV50/j1HK0vIWI-EJ
         */
        var n = 0;
        transition
            .each(function() { ++n; })
            .each("end", function() { if (!--n) callback.apply(this, arguments); });
    };

    return aurora;
});