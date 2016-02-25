var width = null;
var height = null;

var calc_size = function() {
    var main_container = d3.select('#page-content-wrapper div.container-fluid');
    var navbar = d3.select('nav.navbar');
    var footer = d3.select('div.footer');
    var sidebar = d3.select('div.sidebar');

    console.log('main', main_container.node(), main_container.node().clientHeight);
    //console.log('navbar', navbar.clientHeight);
    //console.log('sidebar', sidebar);
    //console.log('sidebar', sidebar.node().clientWidth);
    //console.log('footer', footer.clientHeight);

    width = window.innerWidth;

    if (!sidebar.empty()) {
        width -= sidebar.node().clientWidth;
    }

    height = window.innerHeight;
    if (!navbar.empty()) {
        height -= navbar.node().clientHeight;// - footer.clientHeight;
    }

    d3.select('body')
        .style('padding-top', !navbar.empty()? navbar.node().clientHeight : 0);
        //.style('padding-bottom', footer.clientHeight);

    main_container.style({
        'top': !navbar.empty()? navbar.node().clientHeight + 'px' : 0,
        'left': 0, //sidebar.node().clientWidth + 'px',
        'position': 'relative'
    });

    if (!sidebar.empty()) {
        sidebar.style({
            'top': !navbar.empty()? navbar.node().clientHeight + 'px' : 0,
            'height': (height) + 'px'
        });
    }

    main_container.style({
        "width": (width) + "px",
        "height": (height) + "px"
    });
};

calc_size();

var size_dispatcher = d3.dispatch('resize');

d3.select(window).on('resize', function() {
    calc_size();
    size_dispatcher.resize(width, height);
});
