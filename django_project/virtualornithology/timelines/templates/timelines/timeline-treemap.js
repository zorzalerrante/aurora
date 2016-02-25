var max = null;
var scale = 1;
var complete = 0;
var keyword = "";
var maxLength = 30;

var tweet_padding = 0;
var label_padding = 0;

// legend stuff
var legend_visible = false;

var min_font_size = d3.scale.linear().range([14, 18])
    .domain([400, 1920]);

var max_font_size = d3.scale.linear().range([18, 48])
    .domain([400, 1920]);

var vis_events = d3.dispatch('cell_click', 'cell_enter', 'cell_exit');

var font_size = d3.scale.linear().range([min_font_size(width), max_font_size(width)]);

var nest_by_location = function(tweets) {
    console.log('nesting', tweets);
    tweets.forEach(function(tweet, i) {
        tweet['__rank__'] = i;
    });

    var nest = d3.nest().key(function(d) {
        return +d.fields.geolocation;
    });
    var nested = nest.entries(tweets);

    var entries = {'key': 'root', 'children': [], 'weight': 0, 'tweets': tweets};

    nested.forEach(function(d, i) {
        var location = {key: 'location-' + d.key, pk: d.key};
        location.children = d.values.map(function(tweet) {
            var tweet_node = {key: 'tweet-' + tweet.pk, content: tweet, children: null, parent: d, weight: tweet.fields.weight};
            tweet['__node__'] = tweet_node;
            return tweet_node;
        });
        entries.children.push(location);
    });

    return entries;
};

var current_data = null;
var current_tweet_data = function() {
    console.log('current location', selected_location);
    console.log('current_tweet_data', current_data);
    if (selected_location == 0) {
        // just the top-{{ timeline_home_tweets }} tweets. hopefully one per location
        current_data.tweets.forEach(function(tweet, i) {
            tweet['__node__']['weight'] = i < {{ timeline_home_tweets }} ? tweet.fields.weight : 0;
            tweet['__node__']['active'] = i < {{ timeline_home_tweets }};
        });
    } else {
        current_data.tweets.forEach(function(tweet, i) {
            tweet['__node__']['weight'] = tweet.fields.geolocation == selected_location ? tweet.fields.weight : 0;
            tweet['__node__']['active'] = tweet.fields.geolocation == selected_location;
        });
    }

    current_data.children.forEach(function (d) {
        d.weight = d3.sum(d.children, function (e) {
            console.log('tweet weight', e.weight, e.content.fields.weight, e);
            return Math.sqrt(e.weight);
        });
    });

    current_data.weight = d3.sum(current_data.children, function (e) {
        return e.weight
    });

    return current_treemap()
            .sticky(true)
            .nodes(current_data);
};

var treemap = {
    'square': d3.layout.treemap()
        .value(function (d) {
            return d.weight;
        })
        .children(function (d) {
            return d.children;
        })
        .padding(function (d) {
            switch (d.depth) {
                case 1:
                    return [label_padding, 0, 0, 0];
                    break;
                case 2:
                    return [0, tweet_padding, 0, tweet_padding];
                    break;
                default:
                    return 0;
            }
        })
        .mode('squarify')
        .size([width, height]).sticky(true),
    'dice': d3.layout.treemap()
        .value(function (d) {
            return d.weight;
        })
        .children(function (d) {
            return d.children;
        })
        .padding(function (d) {
            switch (d.depth) {
                case 1:
                    return [label_padding, 0, 0, 0];
                    break;
                case 2:
                    return [0, tweet_padding, 0, tweet_padding];
                    break;
                default:
                    return 0;
            }
        })
        .mode('dice')
        .size([width, height]).sticky(true)
};

var current_treemap = function() {
    return (selected_location == 0 ? treemap.square : treemap.dice)
};

var render = function() {
    var data = current_tweet_data();

    console.log('render', data);
    font_size
        .domain([
            d3.min(data.filter(function(d) { return d.depth == 2 && d.active; }), function(d) { return d.weight; }),
            , d3.max(data.filter(function(d) { return d.depth == 2 && d.active; }), function(d) { return d.weight; })
        ]);

    console.log(font_size.domain());

    var cell = div.selectAll("div.node")
        .data(data, function(d) { return d.key; });

    cell.enter()
        .append("div")
        .each(function(d) {
            var node = d3.select(this);

            if (d.depth == 1) {
                node.append("div")
                    .attr("class", "node-label")
                    .text(function(d) {
                        var loc = categories.get(d.key);
                        return loc.fields.code + ': ' + loc.fields.name;
                    });
            } else if (d.depth == 2) {
                var tweet = d.content;

                var node_tweet = node.append("div")
                    .attr("class", "node-tweet")
                    .html(tweet.fields.html);

                node_tweet.style({
                    'font-size': font_size(d.weight) + 'px'
                });
            }
        })
        .style('background', function(d) {
            if (d.depth == 2) {
                return time_color_scale(d)
            } else if (d.depth == 1) {
                return color_scale(location_id(d.pk))
            }

            return null;
         })
        .style('opacity', function(d) {
            if (d.depth < 2) {
                return 1.0;
            }

            return legend_visible ? 0.0 : 1.0;
        })
        .each(function(d, i) {
            var color;
            if (d.depth == 2) {
                color = time_color_scale(d);
            }
            else if (d.depth == 1) {
                color = color_scale(location_id(d.pk));
            }
            else {
                return null;
            }

            color = color_text(color);

            d3.select(this).style('color', color);

            d3.select(this)
                .selectAll('a')
                .style('color', color)
                .on('click', function() {
                    //console.log('tweet click', this, d);
                    dispatcher.click.apply(this, [d.content, d3.select(this).attr('href')]);
                    d3.event.stopPropagation();
                });

            d3.select(this)
                .selectAll('div.tweet-actions a')
                .style('color', color);

            vis_events.cell_enter.apply(this, arguments);
        })
        .style("left", 0)
        .style("top", 0)
        .style("width", 0)
        .style("height", 0);

    cell.attr("class", function(d) {
            var base_class = "node node-depth-" + d.depth;
            if (d.dx < d.dy) {
                base_class += ' tall-node';
            } else {
                base_class += ' wide-node';
            }

            if (d.dx < 100 || d.dy < 100) {
                base_class += ' small-node';
            }
            return base_class;
        }).style('display', 'block');
    cell.exit()
        .each(function(d) {
            vis_events.cell_exit.apply(this, arguments);
        })
        .transition()
        .delay(10)
        .style('opacity', 0.0)
        .remove();

    cell.transition()
        .delay(300)
        .style("left", function(d) { return d.x + "px"; })
        .style("top", function(d) { return d.y + "px"; })
        .style("width", function(d) {
            var value = Math.max(0, d.dx - tweet_padding);
            return value  + "px";
        })
        .style("height", function(d) {
            var value = Math.max(0, d.dy - tweet_padding);
            return value  + "px";
        })
        .call(aurora.end_all, function() {
            cell.filter(function(d) { return !d.active; })
                .style('display', function (d) {
                    return d.active ? 'block' : 'none';
                });
        });

    cell.on('click', function(d, i) {
        if (d.depth == 2) {
            vis_events.cell_click.apply(this, arguments);
        }
    });
};