
define("portrait_graph", ["d3", "matta", "moment", "wordcloud"], function (d3, matta, moment, wordcloud) {
    
/**
 * Author: Eduardo Graells-Garrido, @carnby.
License: MIT.
 * mod_portrait_graph was scaffolded using matta - https://github.com/carnby/matta
 * Variables that start with an underscore (_) are passed as arguments in Python.
 * Variables that start with _data are data parameters of the visualization, and expected to be given as datum.
 *
 * For instance, d3.select('#figure').datum({'graph': a_json_graph, 'dataframe': a_json_dataframe}).call(visualization)
 * will fill the variables _data_graph and _data_dataframe.
 *
 */

var matta_portrait_graph = function() {
    var __fill_data__ = function(__data__) {
        
            func_portrait_graph.graph(__data__.graph);
        
    };

    
        var _dispatcher = d3.dispatch('node_click', 'word_click', 'bin_click', 'reset', 'clean_popups', 'built_time_axis', 'shown_tweet');
    

    var func_portrait_graph = function (selection) {
        console.log('selection', selection);

        var _vis_width = _width - _padding.left - _padding.right;
        var _vis_height = _height - _padding.top - _padding.bottom;

        selection.each(function(__data__) {
            __fill_data__(__data__);

            var container = null;
            var figure_dom_element = this;

            if (d3.select(this).select('svg.portrait_graph-container').empty()) {
                
                    var svg = d3.select(this).append('svg')
                        .attr('width', _width)
                        .attr('height', _height)
                        .attr('class', 'portrait_graph-container');

                    
                        svg.append('rect')
                            .attr('width', _width)
                            .attr('height', _height)
                            .attr('fill', 'snow');
                    

                    container = svg.append('g')
                        .classed('portrait_graph-container', true)
                        .attr('transform', 'translate(' + _padding.left + ',' + _padding.top + ')');

                
            } else {
                container = d3.select(this).select('svg.portrait_graph-container');
            }

            console.log('container', container.node());

            
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
            

        });
    };

    
        var _data_graph = null;
        func_portrait_graph.graph = function(__) {
            if (arguments.length) {
                _data_graph = __;
                console.log('DATA graph', _data_graph);
                return func_portrait_graph;
            }
            return _data_graph;
        };
    

    
    
        var _link_highlight_opacity = 0.9;
        func_portrait_graph.link_highlight_opacity = function(__) {
            if (arguments.length) {
                _link_highlight_opacity = __;
                console.log('set link_highlight_opacity', _link_highlight_opacity);
                return func_portrait_graph;
            }
            return _link_highlight_opacity;
        };
    
        var _inactive_word_color = "dimgray";
        func_portrait_graph.inactive_word_color = function(__) {
            if (arguments.length) {
                _inactive_word_color = __;
                console.log('set inactive_word_color', _inactive_word_color);
                return func_portrait_graph;
            }
            return _inactive_word_color;
        };
    
        var _link_opacity = 0.03;
        func_portrait_graph.link_opacity = function(__) {
            if (arguments.length) {
                _link_opacity = __;
                console.log('set link_opacity', _link_opacity);
                return func_portrait_graph;
            }
            return _link_opacity;
        };
    
        var _inactive_color = "gainsboro";
        func_portrait_graph.inactive_color = function(__) {
            if (arguments.length) {
                _inactive_color = __;
                console.log('set inactive_color', _inactive_color);
                return func_portrait_graph;
            }
            return _inactive_color;
        };
    
        var _link_highlight_color = "tan";
        func_portrait_graph.link_highlight_color = function(__) {
            if (arguments.length) {
                _link_highlight_color = __;
                console.log('set link_highlight_color', _link_highlight_color);
                return func_portrait_graph;
            }
            return _link_highlight_color;
        };
    
        var _height = 590;
        func_portrait_graph.height = function(__) {
            if (arguments.length) {
                _height = __;
                console.log('set height', _height);
                return func_portrait_graph;
            }
            return _height;
        };
    
        var _word_box_color = "linen";
        func_portrait_graph.word_box_color = function(__) {
            if (arguments.length) {
                _word_box_color = __;
                console.log('set word_box_color', _word_box_color);
                return func_portrait_graph;
            }
            return _word_box_color;
        };
    
        var _link_width = 2.5;
        func_portrait_graph.link_width = function(__) {
            if (arguments.length) {
                _link_width = __;
                console.log('set link_width', _link_width);
                return func_portrait_graph;
            }
            return _link_width;
        };
    
        var _max_node_ratio = 18;
        func_portrait_graph.max_node_ratio = function(__) {
            if (arguments.length) {
                _max_node_ratio = __;
                console.log('set max_node_ratio', _max_node_ratio);
                return func_portrait_graph;
            }
            return _max_node_ratio;
        };
    
        var _bin_color = "indigo";
        func_portrait_graph.bin_color = function(__) {
            if (arguments.length) {
                _bin_color = __;
                console.log('set bin_color', _bin_color);
                return func_portrait_graph;
            }
            return _bin_color;
        };
    
        var _avoid_overlaps = true;
        func_portrait_graph.avoid_overlaps = function(__) {
            if (arguments.length) {
                _avoid_overlaps = __;
                console.log('set avoid_overlaps', _avoid_overlaps);
                return func_portrait_graph;
            }
            return _avoid_overlaps;
        };
    
        var _bin_inactive_color = "silver";
        func_portrait_graph.bin_inactive_color = function(__) {
            if (arguments.length) {
                _bin_inactive_color = __;
                console.log('set bin_inactive_color', _bin_inactive_color);
                return func_portrait_graph;
            }
            return _bin_inactive_color;
        };
    
        var _histogram_bins = 48;
        func_portrait_graph.histogram_bins = function(__) {
            if (arguments.length) {
                _histogram_bins = __;
                console.log('set histogram_bins', _histogram_bins);
                return func_portrait_graph;
            }
            return _histogram_bins;
        };
    
        var _width = 1000;
        func_portrait_graph.width = function(__) {
            if (arguments.length) {
                _width = __;
                console.log('set width', _width);
                return func_portrait_graph;
            }
            return _width;
        };
    
        var _bin_opacity = 0.75;
        func_portrait_graph.bin_opacity = function(__) {
            if (arguments.length) {
                _bin_opacity = __;
                console.log('set bin_opacity', _bin_opacity);
                return func_portrait_graph;
            }
            return _bin_opacity;
        };
    
        var _color_scale_range = null;
        func_portrait_graph.color_scale_range = function(__) {
            if (arguments.length) {
                _color_scale_range = __;
                console.log('set color_scale_range', _color_scale_range);
                return func_portrait_graph;
            }
            return _color_scale_range;
        };
    
        var _node_color = "palegoldenrod";
        func_portrait_graph.node_color = function(__) {
            if (arguments.length) {
                _node_color = __;
                console.log('set node_color', _node_color);
                return func_portrait_graph;
            }
            return _node_color;
        };
    
        var _wordcloud_padding = 160;
        func_portrait_graph.wordcloud_padding = function(__) {
            if (arguments.length) {
                _wordcloud_padding = __;
                console.log('set wordcloud_padding', _wordcloud_padding);
                return func_portrait_graph;
            }
            return _wordcloud_padding;
        };
    
        var _link_distance = 100;
        func_portrait_graph.link_distance = function(__) {
            if (arguments.length) {
                _link_distance = __;
                console.log('set link_distance', _link_distance);
                return func_portrait_graph;
            }
            return _link_distance;
        };
    
        var _word_box_opacity = 0.75;
        func_portrait_graph.word_box_opacity = function(__) {
            if (arguments.length) {
                _word_box_opacity = __;
                console.log('set word_box_opacity', _word_box_opacity);
                return func_portrait_graph;
            }
            return _word_box_opacity;
        };
    
        var _word_colors = {"mention": "#d95f02", "other": "#1b9e77", "hashtag": "#7570b3"};
        func_portrait_graph.word_colors = function(__) {
            if (arguments.length) {
                _word_colors = __;
                console.log('set word_colors', _word_colors);
                return func_portrait_graph;
            }
            return _word_colors;
        };
    
        var _max_font_size = 60;
        func_portrait_graph.max_font_size = function(__) {
            if (arguments.length) {
                _max_font_size = __;
                console.log('set max_font_size', _max_font_size);
                return func_portrait_graph;
            }
            return _max_font_size;
        };
    
        var _padding = {"top": 30, "right": 30, "left": 30, "bottom": 30};
        func_portrait_graph.padding = function(__) {
            if (arguments.length) {
                _padding = __;
                console.log('set padding', _padding);
                return func_portrait_graph;
            }
            return _padding;
        };
    
        var _font_weight = "bold";
        func_portrait_graph.font_weight = function(__) {
            if (arguments.length) {
                _font_weight = __;
                console.log('set font_weight', _font_weight);
                return func_portrait_graph;
            }
            return _font_weight;
        };
    
        var _node_id = "id";
        func_portrait_graph.node_id = function(__) {
            if (arguments.length) {
                _node_id = __;
                console.log('set node_id', _node_id);
                return func_portrait_graph;
            }
            return _node_id;
        };
    
        var _font_scale = "sqrt";
        func_portrait_graph.font_scale = function(__) {
            if (arguments.length) {
                _font_scale = __;
                console.log('set font_scale', _font_scale);
                return func_portrait_graph;
            }
            return _font_scale;
        };
    
        var _node_opacity = 0.75;
        func_portrait_graph.node_opacity = function(__) {
            if (arguments.length) {
                _node_opacity = __;
                console.log('set node_opacity', _node_opacity);
                return func_portrait_graph;
            }
            return _node_opacity;
        };
    
        var _color_scale_domain = null;
        func_portrait_graph.color_scale_domain = function(__) {
            if (arguments.length) {
                _color_scale_domain = __;
                console.log('set color_scale_domain', _color_scale_domain);
                return func_portrait_graph;
            }
            return _color_scale_domain;
        };
    
        var _font_opacity = 1.0;
        func_portrait_graph.font_opacity = function(__) {
            if (arguments.length) {
                _font_opacity = __;
                console.log('set font_opacity', _font_opacity);
                return func_portrait_graph;
            }
            return _font_opacity;
        };
    
        var _typeface = "Lato";
        func_portrait_graph.typeface = function(__) {
            if (arguments.length) {
                _typeface = __;
                console.log('set typeface', _typeface);
                return func_portrait_graph;
            }
            return _typeface;
        };
    
        var _inactive_word_opacity = 0.5;
        func_portrait_graph.inactive_word_opacity = function(__) {
            if (arguments.length) {
                _inactive_word_opacity = __;
                console.log('set inactive_word_opacity', _inactive_word_opacity);
                return func_portrait_graph;
            }
            return _inactive_word_opacity;
        };
    
        var _min_node_ratio = 4;
        func_portrait_graph.min_node_ratio = function(__) {
            if (arguments.length) {
                _min_node_ratio = __;
                console.log('set min_node_ratio', _min_node_ratio);
                return func_portrait_graph;
            }
            return _min_node_ratio;
        };
    
        var _tooltip_container = "body";
        func_portrait_graph.tooltip_container = function(__) {
            if (arguments.length) {
                _tooltip_container = __;
                console.log('set tooltip_container', _tooltip_container);
                return func_portrait_graph;
            }
            return _tooltip_container;
        };
    
        var _histogram_height = 110;
        func_portrait_graph.histogram_height = function(__) {
            if (arguments.length) {
                _histogram_height = __;
                console.log('set histogram_height', _histogram_height);
                return func_portrait_graph;
            }
            return _histogram_height;
        };
    
        var _min_font_size = 14;
        func_portrait_graph.min_font_size = function(__) {
            if (arguments.length) {
                _min_font_size = __;
                console.log('set min_font_size', _min_font_size);
                return func_portrait_graph;
            }
            return _min_font_size;
        };
    
    

    

    
        
            d3.rebind(func_portrait_graph, _dispatcher, 'node_click');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'word_click');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'bin_click');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'reset');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'clean_popups');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'built_time_axis');
        
            d3.rebind(func_portrait_graph, _dispatcher, 'shown_tweet');
        
        d3.rebind(func_portrait_graph, _dispatcher, 'on');
    

    return func_portrait_graph;
};
    return matta_portrait_graph;
});
