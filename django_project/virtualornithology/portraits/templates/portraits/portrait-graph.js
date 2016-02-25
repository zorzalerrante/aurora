// console.log(d3, moment);

matta.prepare_graph(_data_graph);

// data
var tweets = _data_graph.nodes.filter(function(d) { return d.type == 'tweet'; });
var terms = _data_graph.nodes.filter(function(d) { return d.type == 'term'; });

// containers
var axis_g = container.append('g').classed('axis', true);
var link_g = container.append('g').classed('link-container', true);
var time_g = container.append('g').classed('tweet-skyline', true);
var wordcloud_g = container.append('g').classed('wordcloud', true).attr('transform', 'translate(0, ' + _wordcloud_padding + ')');
var wordcloud_height = _vis_height - _wordcloud_padding;
var box_g = wordcloud_g.append('g').classed('box-container', true).attr("transform", "translate(" + [_vis_width >> 1, wordcloud_height >> 1] + ")");
var word_g = wordcloud_g.append('g').classed('words', true).attr("transform", "translate(" + [_vis_width >> 1, wordcloud_height >> 1] + ")");

// scales
var node_scale = d3.scale.sqrt()
    .domain(d3.extent(tweets, function(d) { return d.weight; }))
    .range([_min_node_ratio, _max_node_ratio]);

var time_scale = d3.time.scale()
    .domain(d3.extent(tweets, function(d) { return moment(d.datetime); }))
    .range([0, _vis_width])
    .nice();

var font_scale = matta.scale(_font_scale)
    .range([_min_font_size, _max_font_size])
    .domain(d3.extent(terms, function(d) { return d.weight; }));

// we need the time scale for this
var ticks = time_scale.ticks(_histogram_bins);
var binned_data = d3.layout.histogram()
    .bins(ticks)
    .value(function(d) { return moment(d.datetime); })
    (tweets);

var freq_scale = d3.scale.linear()
    .domain([0, d3.max(binned_data, function(d) { return d.y; })])
    .range([_histogram_height, 0]);

var time_axis = d3.svg.axis().scale(time_scale).orient('top');

_dispatcher.built_time_axis(time_axis);

var freq_axis = d3.svg.axis().scale(freq_scale).orient('right');

axis_g.append('g').classed('time-axis', true).attr('transform', 'translate(0, ' + -5 + ')').call(time_axis);
axis_g.append('g').classed('freq-axis', true).attr('transform', 'translate(' + _vis_width + ')').call(freq_axis)
    .append('text').text('Tweets').attr('transform', 'translate(-5)rotate(-90)').attr('text-anchor', 'end');

// Generate a histogram using uniformly-spaced bins.

var bin_width = time_scale(ticks[1]) - time_scale(ticks[0]) - 1;
//time_scale(moment(binned_data[0].x).add(binned_data[0].dx, 'milliseconds')))
// console.log('bin width', bin_width);

// console.log('ticks', time_scale.ticks());
// console.log('bins', binned_data[0], binned_data);

var bin_links = [];

binned_data.forEach(function(bin) {
    bin.words = d3.set();

    // select the most popular tweet
    if (bin.length > 0) {
        var sorted = bin.sort(function(a, b) { return d3.descending(a.weight, b.weight); });
        bin.current_tweet = sorted[0];
    }

    _data_graph.links.filter(function(d) { return bin.indexOf(d.source) >= 0; })
        .forEach(function(l) {
            //console.log('graph link', l);
            if (!bin.words.has(l.target.label)) {
                bin_links.push({'source': bin, 'target': l.target, 'tweet': l.source});
                bin.words.add(l.target.label);
            }
        });
    // console.log('bin', bin.words);
});

// console.log('histo y', freq_scale.domain(), freq_scale.range());
// console.log('delta', moment(binned_data[1].x).add(binned_data[1].dx, 'milliseconds'), time_scale(moment(binned_data[1].x).add(binned_data[1].dx, 'milliseconds')));

var skyline_circles = time_g.append('g');
var skyline_bars = time_g.append('g');

var bar = skyline_bars.selectAll("rect.bar")
    .data(binned_data);

bar.enter().append("rect")
    .attr("class", "bar")
    .attr("transform", function(d) { return "translate(" + time_scale(d.x) + "," + freq_scale(d.y) + ")"; });

bar.attr("x", 1)
    .attr("width", bin_width)
    .attr("height", function(d) { return _histogram_height - freq_scale(d.y); })
    .attr('fill', _bin_color)
    .attr('opacity', _bin_opacity);

bar.on('click', function(d, i) {
    _dispatcher.bin_click.apply(this, arguments);
    d3.event.stopPropagation();
});

_dispatcher.on('bin_click', function(d, i) {
    // console.log('bin click', d, i);
    bar.attr('fill', _bin_inactive_color);
    d3.select(this).attr('fill', _bin_color);
});

// draw tweet moon

var tweet_circle = skyline_circles.selectAll('circle.moon').data(binned_data.filter(function(d) { return d.y > 0; }));
var active_tooltip = null;

tweet_circle.enter().append('circle').classed('moon', true)
    .attr({
        'cx': function(d) { return time_scale(d.x); },
        'cy': function(d) { return freq_scale(d.y); },
        'r': function(d) { return node_scale(d3.max(d, function(tweet) { return tweet.weight; })); },
        'fill': _inactive_color,
        'opacity': _node_opacity,
        'stroke-width': 1,
        'stroke': 'silver'
    }).each(function(d) {
        // console.log(d);
        $(this).popover({
            'content': function() {
                var tweet = d.current_tweet;
                //console.log(tweet);
                var img = '';
                if (tweet.hasOwnProperty('media') && tweet.media) {
                    console.log('img', tweet.media);
                    img = '<p>' + //<a href="' + tweet.media.expanded_url + '" target="_blank">' +
                        '<img class="tweet-media img-rounded img-responsive" src="' + tweet.media.media_url + '" width="100%" />' + //'</a>'
                        '</p>';
                }

                // console.log('popover fn', this, tweet);
                return '<img class="img img-rounded pull-left" width="48" height="48" src="' + tweet.avatar + '"/>'
                    + '<p style="margin-left: 52px; margin-top: 0; text-align: left;"><strong>@' + tweet.author + '</strong><br />' + tweet.label + '</p>' +
                    '<span class="clearfix"></span>' + img;
                },
            'trigger' : 'manual',
            'html': true,
            'container': figure_dom_element,
            'placement': time_scale(d.x) >= _vis_width * 0.5 ? 'left' : 'right'
        })
    });

tweet_circle.on('click', function(d, i) {
    _dispatcher.node_click.apply(this, arguments);
    d3.event.stopPropagation();
});

var deactivate_tooltip = function() {
    if (active_tooltip != null) {
        $(active_tooltip).popover('hide');
        d3.select(active_tooltip).attr('fill', _inactive_color);
        active_tooltip = null;
    }
};

var activate_tooltip = function(d, i) {
    d3.select(this).attr('fill', _node_color);
    //console.log('activate tooltip', d.current_tweet);
    if (d.current_tweet.hasOwnProperty('media') && d.current_tweet.media) {
        var el = d3.select('body').append('img').style('display', 'none');
        var self = this;
        el.on('load', function() {
            // only proceed if nothing happened in-between (like clicking somewhere else)
            if (active_tooltip == self) {
                $(self).popover('show');
                $(self).on('shown.bs.popover', function() {
                    _dispatcher.shown_tweet.apply(this, [d.current_tweet, i]);
                });
            }
            el.remove();
        }).attr('src', d.current_tweet.media.media_url);
    } else {
        $(this).popover('show');
        $(this).on('shown.bs.popover', function() {
            _dispatcher.shown_tweet.apply(this, [d.current_tweet, i]);
        });
    }
    active_tooltip = this;
};

_dispatcher.on('node_click', function(d, i) {
    if (active_tooltip != this) {
        deactivate_tooltip();
        activate_tooltip.apply(this, arguments);

        // see bin_click.tooltip below
        var bin = bar.filter(function(d2) { return d == d2});
        // console.log('bin', bin);
        if (!bin.empty()) {
            _dispatcher.bin_click.apply(bin.node(), arguments);
        }
    } else {
        deactivate_tooltip();
    }
});

_dispatcher.on('word_click.tooltip', deactivate_tooltip);
_dispatcher.on('bin_click.tooltip', function(d, i) {
    var moon = tweet_circle.filter(function(d2) { return d == d2});

    // console.log('moon', moon);
    if (!moon.empty()) {
        if (active_tooltip != moon.node()) {
            deactivate_tooltip();
        }
        activate_tooltip.apply(moon.node(), arguments);
    }
});

_dispatcher.on('clean_popups.tooltip', function() {
    //console.log('clean popups');
    deactivate_tooltip();
});

container.on('click', deactivate_tooltip);

// draw words
var statusText = container.append('text').attr('class', "wordcloud-status").attr('y', 10);

var complete = 0;
var max = terms.length;

var word_color = function(d){
    if (d.text[0] == '#') {
        return _word_colors.hashtag;
    }
    if (d.text[0] == '@') {
        return _word_colors.mention;
    }
    return _word_colors.other;
};

var cloud_draw = function(words, bounds) {
    statusText.style("display", "none");
    // console.log('words', words);
    var scale = bounds ? Math.min(
        _vis_width / Math.abs(bounds[1].x - _vis_width / 2),
        _vis_width / Math.abs(bounds[0].x - _vis_width / 2),
        wordcloud_height / Math.abs(bounds[1].y - wordcloud_height / 2),
        wordcloud_height / Math.abs(bounds[0].y - wordcloud_height / 2)) / 2 : 1;

    var text = word_g.selectAll('text')
        .data(words, function(d) { return d.text; });

    text.enter()
        .append('text')
        .attr("transform", function(d) { return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")"; })
        .attr("text-anchor", "middle")
        .style("font-size", function(d) { return d.size + "px"; })
        .style("font-family", function(d){ return d.font; })
        .style("font-weight", _font_weight)
        .style("opacity", _font_opacity)
        .style("fill", word_color)
        .text(function(d){ return d.text; });

    text.each(function(d) {
        d.bbox = this.getBBox();
    });

    text.on('click', function(d, i) {
        _dispatcher.word_click.apply(this, arguments);
        d3.event.stopPropagation();
    });

    var bbox = box_g.selectAll('rect')
        .data(words);

    bbox.enter()
        .append('rect')
        .attr("transform", function(d) { return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")"; })
        .attr('rx', 5)
        .attr('ry', 5);

    bbox.style({
            'fill': _word_box_color,
            'opacity': _word_box_opacity,
            'display': 'none',
            'stroke-width': 1,
            'stroke': 'dimgray'
        })
        .attr({
            'width': function(d) { return d.bbox.width * 1.15; },
            'height': function(d) { return d.bbox.height * 1.1; },
            'x': function(d) { return -(d.bbox.width * 1.15) * 0.5; },
            'y': function(d) { return -(d.bbox.height * 1.1) * 0.8; }
        });

    var word_positions = d3.map();
    words.forEach(function(d) {
        var x = d.x + _vis_width * 0.5;
        var y = d.y + wordcloud_height * 0.5 + _wordcloud_padding;
        word_positions.set(d.text, {'x': x, 'y': y});
        //console.log('word pos', d, x, y);
    });

    // console.log('word positions', word_positions);
    var diagonal = d3.svg.diagonal()
        .source(function(d) {
            var res = word_positions.get(d.target.label);
            // console.log('source', d, res);
            return res;
        })
        .target(function(d) {
            //var res = {'x': time_scale(moment(d.source.datetime)), 'y': _max_node_ratio * 1.5};
            var res = {'x': time_scale(moment(d.source.x)) + bin_width * 0.5, 'y': _histogram_height + 5};
            // console.log('target', d, res);
            return res;
        });


    var link = link_g.selectAll('path.link')//.data(_data_graph.links.filter(function(d) {
        .data(bin_links.filter(function(d) {
            return word_positions.has(d.target.label);
        })
    );


    link.enter()
        .append('path').classed('link', true)
        .attr('d', diagonal)
        .attr('fill', 'none')
        .attr('stroke-width', _link_width)
        .attr('stroke', 'grey')
        .attr('opacity', _link_opacity);

    _dispatcher.on('word_click.links', function(d, i) {
        // console.log(d, i);
        link.attr('stroke', 'grey')
            .attr('opacity', _link_opacity);

        //tweet_circle.attr('fill', 'grey').attr('opacity', 0.15);
        bar.attr('fill', _bin_inactive_color);

        bbox.style({'display': 'none'});

        link.filter(function(l) { return l.target.label == d.text; })
            .attr('stroke', _link_highlight_color)
            .attr('opacity', _link_highlight_opacity)
            .each(function (l) {
                bar.filter(function(bin) { return bin.words.has(d.text); })
                    .attr('fill', _bin_color).attr('opacity', _node_opacity)
                    .filter(function(bin) { return l.source == bin; })
                    .each(function(bin) {
                        // console.log('link bin', l, bin);
                        bin.current_tweet = l.tweet;
                    });

                bbox.filter(function(b) { return b.text == l.target.label})
                    .style({'display': 'block'});
            })
            .call(matta.move_to_front);

        text.style({'fill': _inactive_word_color, 'opacity': _inactive_word_opacity});
        d3.select(this).style({'fill': word_color, 'opacity': _font_opacity});
    });

    _dispatcher.on('bin_click.links', function(d) {
        //d3.select(this).call(matta.move_to_front);

        link.attr('stroke', 'grey')
            .attr('opacity', _link_opacity);

        bbox.style({'display': 'none'});

        text.style({'fill': _inactive_word_color, 'opacity': _inactive_word_opacity});
        link.filter(function(l) { return l.source == d; })
            .attr('stroke', _link_highlight_color)
            .attr('opacity', _link_highlight_opacity)
            .each(function (l) {
                bbox.filter(function(b) { return b.text == l.target.label})
                    .style({'display': 'block'});

                text.filter(function(b) { return b.text == l.target.label})
                    .style({'fill': word_color, 'opacity': _font_opacity});
            })
            .call(matta.move_to_front);
    });

    _dispatcher.on('reset.state', function() {
        bar.attr('fill', _bin_color)
            .attr('opacity', _bin_opacity);

        bbox.style({'display': 'none'});

        link.attr('stroke', 'grey')
            .attr('opacity', _link_opacity);

        text.style("opacity", _font_opacity)
            .style("fill", word_color);
        deactivate_tooltip();
    });
};



var layout = wordcloud()
    .size([_vis_width, wordcloud_height])
    .font(_typeface)
    .fontWeight(_font_weight)
    .fontSize(function(d) { return font_scale(d.weight); })
    .text(function(d) { return d.label; })
    .rotate(-5)
    .on("word", function(d) { return statusText.text(++complete + "/" + max); })
    .on("end", function(d, b) { return cloud_draw(d, b); });


statusText.style("display", null);
layout.stop().words(terms).start();
