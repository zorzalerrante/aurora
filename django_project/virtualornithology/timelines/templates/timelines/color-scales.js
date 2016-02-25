// from d3plus
var color_text = function(color) {
      var b, g, r, rgbColor, yiq;
      rgbColor = d3.rgb(color);
      r = rgbColor.r;
      g = rgbColor.g;
      b = rgbColor.b;
      yiq = (r * 299 + g * 587 + b * 114) / 1000;
      if (yiq >= 128) {
        return "#444444";
      } else {
        return "#f7f7f7";
      }
};

// from d3plus
var color_scale = d3.scale.ordinal().range(["#b22200", "#EACE3F", "#282F6B", "#B35C1E", "#224F20", "#5F487C", "#759143", "#419391", "#993F88", "#e89c89", "#ffee8d", "#afd5e8", "#f7ba77", "#a5c697", "#c5b5e5"]);
var recency_scale = d3.scale.sqrt().range([0.0, 1.0]).domain([1.0, 3.0]).clamp(true);

var time_color_scale = function(d) {
    var color = d3.hsl(color_scale(location_id(d.parent.pk)));
    color = color.darker(recency_scale(d.content.fields.recency));
    return color.toString();
};