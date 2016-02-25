var selected_location = 0;
var filter_dispatcher = d3.dispatch('click', 'show_all');

var prepare_categories = function(locations, tweets) {
    color_scale.domain(d3.range(0, locations.length));

    locations.forEach(function(location, i) {
        categories.set('location-' + location.pk, location);
        location_id_map.set(location.pk, i);
        location.count = 0;
        location.background_color = color_scale(i);
        location.text_color = color_text(location.background_color);
    });

    var counts = _.countBy(tweets, function(d) {
        console.log(d);
        return 'location-' + d.fields.geolocation;
    });


    console.log('counts', counts);

    var valid_locations = 0;
    d3.entries(counts).forEach(function(d) {
        categories.get(d.key).count = d.value;
        ++valid_locations;
    });

    var location_codes = d3.map();
    locations.forEach(function(d, i) {
       if (categories.has('location-' + d.pk)) {
           location_codes.set(d.fields.code, d);
       }
    });

    var validate_hash = function() {
        if (window.location.hash) {
            var hash_location = window.location.hash.substr(1);
            console.log('hash location', hash_location);
            if (location_codes.has(hash_location)) {
                var current_location = location_codes.get(hash_location);
                maybe_filter_location(current_location);
            }
        }
    };

    var maybe_filter_location = function(d) {
        console.log('maybe filter location', d);
        if (!counts.hasOwnProperty('location-' + d.pk)) {
            aurora.notify('Región ' + d.fields.code + ' sin Tweets', 'No hay tweets destacados para <strong>' + d.fields.name + '</strong> en este resumen informativo.', 'warning');
            return;
        }

        if (selected_location != d.pk) {
            selected_location = d.pk;
            console.log('current location', d.pk);
            filter_colors();
            render();
            filter_dispatcher.click(d);
        }

        console.log('selected location', selected_location);
    };

    console.log('categories', categories.values());


    // filters
    var location_filter = d3.select('#location-filters').selectAll('a.location').data(locations);

    location_filter.enter()
            .append('a')
            .attr({
                'class': 'location list-group-item',
            })
            .attr('title', function(d) { return d.fields.name + ' (' + categories.get('location-' + d.pk).count + ' tweets)'; })
            .html(function(d) {
                var code = 'Región ' + d.fields.code;
                var badge = '<span class="badge">' + categories.get('location-' + d.pk).count + '</span>'
                if (categories.get('location-' + d.pk).count == 0) {
                    code = '<del>' + code + '</del>';
                } else {
                    code = badge + code;
                }
                return code;
            })
            .each(function(d) {
                $(d3.select(this).node()).tooltip({'placement': 'right', 'trigger': 'hover', 'container': 'body'});

                d3.select(this).on('click', function() {
                        maybe_filter_location(d);
                        window.location.hash = '#' + d.fields.code;
                    });
            });

    var filter_colors = function() {
        d3.select('a#toggle-all-locations')
            .transition()
            .delay(300)
            .style('background-color', selected_location == 0 ? '#217dbb' : '#888');

        location_filter.each(function(d, i) {
                d3.select(this)
                    .transition()
                    .delay(300)
                    .style('background-color', function() {
                        return counts.hasOwnProperty('location-' + d.pk) && (selected_location == 0 || selected_location == d.pk) ? d.background_color : '#888';
                    })
                    .style('color', function() {
                        return counts.hasOwnProperty('location-' + d.pk) && (selected_location == 0 || selected_location == d.pk) ? d.text_color : '#efefef';
                    });
            });
    };

    filter_colors();

    dispatcher.on('loaded.interaction', function() {
        validate_hash();
    });

    d3.select('a#toggle-all-locations').on('click', function() {
        if (selected_location == 0) {
            return;
        }
        window.location.hash = '';
        selected_location = 0;
        filter_colors();
        render();
        filter_dispatcher.show_all();
    });
};