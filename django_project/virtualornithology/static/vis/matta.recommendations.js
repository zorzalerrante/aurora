
define("matta_circlepack", ["d3", "matta"], function (d3, matta) {
    
/**
 * mod_matta_circlepack was scaffolded using matta - https://github.com/carnby/matta
 * Variables that start with an underscore (_) are passed as arguments in Python.
 * Variables that start with _data are data parameters of the visualization, and expected to be given as datum.
 *
 * For instance, d3.select('#figure').datum({'graph': a_json_graph, 'dataframe': a_json_dataframe}).call(visualization)
 * will fill the variables _data_graph and _data_dataframe.
 */

var matta_matta_circlepack = function() {
    var __fill_data__ = function(__data__) {
        
            func_matta_circlepack.tree(__data__.tree);
        
    };

    
        var _dispatcher = d3.dispatch('node_click');
    

    var func_matta_circlepack = function (selection) {
        console.log('selection', selection);

        var _vis_width = _width - _padding.left - _padding.right;
        var _vis_height = _height - _padding.top - _padding.bottom;

        selection.each(function(__data__) {
            __fill_data__(__data__);

            var container = null;
            var figure_dom_element = this;

            if (d3.select(this).select('svg.matta_circlepack-container').empty()) {
                
                    var svg = d3.select(this).append('svg')
                        .attr('width', _width)
                        .attr('height', _height)
                        .attr('class', 'matta_circlepack-container');

                    

                    container = svg.append('g')
                        .classed('matta_circlepack-container', true)
                        .attr('transform', 'translate(' + _padding.left + ',' + _padding.top + ')');

                
            } else {
                container = d3.select(this).select('svg.matta_circlepack-container');
            }

            console.log('container', container.node());

            
                
var diameter = Math.min(_vis_width, _vis_height),
    format = d3.format(",d");

var pack = d3.layout.pack()
    .size([diameter - 4, diameter - 4])
    .value(function(d) { return d[_node_value]; });

var node = container.datum(_data_tree).selectAll('.node')
    .data(pack.nodes);

node.enter().append('g').each(function(d) {
    var self = d3.select(this);
    self.append('circle');
    self.append('text');
});

node.attr('class', function(d) { return d.children ? "node node-depth-" + d.depth  : "node-leaf node node-depth-" + d.depth; })
    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

node.selectAll('circle')
    .attr({
        'r': function(d) { return d.r - _node_padding; },
        'fill-opacity': _node_opacity,
        'fill': _node_color,
        'stroke-width': _node_border,
        'stroke': _node_border_color
    }).on('click', function(d, i) {
        _dispatcher.node_click.apply(this, arguments);
    });


node.selectAll('text').call(matta.labeler(_node_label));
            

        });
    };

    
        var _data_tree = null;
        func_matta_circlepack.tree = function(__) {
            if (arguments.length) {
                _data_tree = __;
                console.log('DATA tree', _data_tree);
                return func_matta_circlepack;
            }
            return _data_tree;
        };
    

    
    
        var _node_label = null;
        func_matta_circlepack.node_label = function(__) {
            if (arguments.length) {
                _node_label = __;
                console.log('set node_label', _node_label);
                return func_matta_circlepack;
            }
            return _node_label;
        };
    
        var _font_size = 14;
        func_matta_circlepack.font_size = function(__) {
            if (arguments.length) {
                _font_size = __;
                console.log('set font_size', _font_size);
                return func_matta_circlepack;
            }
            return _font_size;
        };
    
        var _sticky = true;
        func_matta_circlepack.sticky = function(__) {
            if (arguments.length) {
                _sticky = __;
                console.log('set sticky', _sticky);
                return func_matta_circlepack;
            }
            return _sticky;
        };
    
        var _node_border_color = "rgb(31, 119, 180)";
        func_matta_circlepack.node_border_color = function(__) {
            if (arguments.length) {
                _node_border_color = __;
                console.log('set node_border_color', _node_border_color);
                return func_matta_circlepack;
            }
            return _node_border_color;
        };
    
        var _node_border = 1;
        func_matta_circlepack.node_border = function(__) {
            if (arguments.length) {
                _node_border = __;
                console.log('set node_border', _node_border);
                return func_matta_circlepack;
            }
            return _node_border;
        };
    
        var _node_children = "children";
        func_matta_circlepack.node_children = function(__) {
            if (arguments.length) {
                _node_children = __;
                console.log('set node_children', _node_children);
                return func_matta_circlepack;
            }
            return _node_children;
        };
    
        var _padding = {"top": 0, "right": 0, "left": 0, "bottom": 0};
        func_matta_circlepack.padding = function(__) {
            if (arguments.length) {
                _padding = __;
                console.log('set padding', _padding);
                return func_matta_circlepack;
            }
            return _padding;
        };
    
        var _width = 600;
        func_matta_circlepack.width = function(__) {
            if (arguments.length) {
                _width = __;
                console.log('set width', _width);
                return func_matta_circlepack;
            }
            return _width;
        };
    
        var _node_id = "id";
        func_matta_circlepack.node_id = function(__) {
            if (arguments.length) {
                _node_id = __;
                console.log('set node_id', _node_id);
                return func_matta_circlepack;
            }
            return _node_id;
        };
    
        var _node_color = "rgb(31, 119, 180)";
        func_matta_circlepack.node_color = function(__) {
            if (arguments.length) {
                _node_color = __;
                console.log('set node_color', _node_color);
                return func_matta_circlepack;
            }
            return _node_color;
        };
    
        var _label_leaves_only = true;
        func_matta_circlepack.label_leaves_only = function(__) {
            if (arguments.length) {
                _label_leaves_only = __;
                console.log('set label_leaves_only', _label_leaves_only);
                return func_matta_circlepack;
            }
            return _label_leaves_only;
        };
    
        var _node_padding = 2;
        func_matta_circlepack.node_padding = function(__) {
            if (arguments.length) {
                _node_padding = __;
                console.log('set node_padding', _node_padding);
                return func_matta_circlepack;
            }
            return _node_padding;
        };
    
        var _height = 600;
        func_matta_circlepack.height = function(__) {
            if (arguments.length) {
                _height = __;
                console.log('set height', _height);
                return func_matta_circlepack;
            }
            return _height;
        };
    
        var _node_opacity = 0.25;
        func_matta_circlepack.node_opacity = function(__) {
            if (arguments.length) {
                _node_opacity = __;
                console.log('set node_opacity', _node_opacity);
                return func_matta_circlepack;
            }
            return _node_opacity;
        };
    
        var _node_value = "weight";
        func_matta_circlepack.node_value = function(__) {
            if (arguments.length) {
                _node_value = __;
                console.log('set node_value', _node_value);
                return func_matta_circlepack;
            }
            return _node_value;
        };
    
    

    

    
        return d3.rebind(func_matta_circlepack, _dispatcher, 'on');
    
};
    return matta_matta_circlepack;
});
