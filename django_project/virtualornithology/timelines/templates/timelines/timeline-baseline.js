var render = function(data) {
    console.log(data);

    var tweet = timeline_container.selectAll('div.single-tweet')
        .data(data, function(d) { return d.pk; });

    tweet.enter()
        .append('div')
        .attr({'class': 'single-tweet'})
        .style('opacity', 0.0)
        .html(function(d) {
            var cat = categories.get('location-' + d.fields.geolocation);
            return ''
            + '<div class="panel panel-default"><div class="panel-body"><ul class="list-unstyled">'
            + tweet_template(d)
            + '</ul></div><div class="panel-footer"><small>'
            + 'Desde <strong>' + cat.fields.name + '</strong>'
            +'</small></div></div>';
        })
        .each(function(d) {
            var tweet = d;
            if (tweet.fields.hasOwnProperty('media') && tweet.fields.media != null) {
                var p = d3.select(this).select('p.tweet-content');
                var img_width = p.node().clientWidth;
                var media = tweet.fields.media[0];
                var aspect_ratio = media.fields.aspect_ratio;

                d3.select(this).select('img.tweet-media')
                    .style({'width': img_width, 'height': img_width / aspect_ratio})
                    .attr({'width': img_width, 'height': img_width / aspect_ratio, 'alt': aspect_ratio});
            }
        })
        .each(function(d, i) {
            var dom_element = d3.select(this);
            dom_element.select('div.panel-footer')
                .style('background-color', function(d) {
                    if (d == null) {
                        return;
                    }
                    return color_scale(location_id(d.fields.geolocation));
                })
                .style('color', function(d) {
                    return color_text(color_scale(location_id(d.fields.geolocation)));
                });

            dom_element.select('div.panel')
                .style('border-color', function(d) {
                    if (d == null) {
                        return;
                    }
                    return color_scale(location_id(d.fields.geolocation));
                });

            dom_element.selectAll('a')
                .on('click', function() {
                    console.log('tweet click', this, d);
                    dispatcher.click.apply(this, [d, d3.select(this).attr('href')]);
                    d3.event.preventDefault();
                });
        });

    if (!tweet.exit().empty()) {
        tweet.exit()
            .transition()
            .delay(100)
            .style('opacity', 0.0)
            .remove()
            .call(end_all, masonry_timeline);
    }

    if (!tweet.enter().empty()) {
        tweet.sort(function(a, b) {
            return d3.descending(moment(a.fields.datetime).toDate(), moment(b.fields.datetime).toDate());
        })
        .call(masonry_timeline)
        .transition()
        .delay(100)
        .style('opacity', 1.0);
    }
};