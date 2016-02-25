var render = function(data) {
    var entries = nest_by_location(data);
    console.log('entries', entries);

    var cluster = timeline_container.selectAll('div.clustered-tweets')
        .data(entries.children, function(c) { return c.key; });

    cluster.enter().append('div')
        .attr({class: 'clustered-tweets'})
        .html(function(c) {
            var cat = categories.get(c.key);
            return '<div class="panel panel-default">'
                + '<div class="panel-heading">'
                + '<strong>' + cat.fields.name + '</strong>'
                + '</div>'
                + '<div class="panel-body"><ul class="list-unstyled list-tweets"></ul></div>'
                + '</div>';
        })
        .style('opacity', 0.0)
        .each(function(d, i) {
            d3.select(this).select('div.panel')
                .style('border-color', function() {
                    if (d == null) {
                        return;
                    }
                    return color_scale(location_id(d.pk));
                });

            d3.select(this).select('div.panel-heading')
                .style('background-color', function() {
                    if (d == null) {
                        return;
                    }
                    return color_scale(location_id(d.pk));
                })
                .style('color', color_text(color_scale(location_id(d.pk))));
        })
        .each(function(c) {
            var tweet = d3.select(this).select('ul.list-tweets')
                .selectAll('li.tweet')
                .data(c.children, function(tweet) { console.log('child', tweet); return tweet.key; });

            tweet.enter()
                .append('li')
                .attr('class', 'tweet')
                .sort(function(a, b) {
                    return d3.descending(moment(a.content.fields.datetime).toDate(), moment(b.content.fields.datetime).toDate());
                })
                .html(function(d) { return tweet_template(d.content); })
                .each(function(d) {
                    var tweet = d.content;
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
                    console.log(d.parent);
                    if ((i + 1) < d.parent.values.length) {
                        d3.select(this).append('hr');
                    }

                    d3.select(this).selectAll('a')
                        .on('click', function() {
                            console.log('tweet click', this, d);
                            dispatcher.click.apply(this, [d.content, d3.select(this).attr('href')]);
                        });
                });
        })
        .transition()
        .delay(500)
        .style('opacity', 1.0)
        {% if not mobile %}
        .call(end_all, masonry_timeline)
        {% endif %};

    cluster.exit()
        .transition()
        .delay(500)
        .style('opacity', 0.0)
        .remove()
        {% if not mobile %}
        .call(end_all, masonry_timeline)
        {% endif %};

};