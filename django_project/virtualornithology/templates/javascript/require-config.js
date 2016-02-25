require.config({
    urlArgs: 'bust=1.1.2',
    paths: {
        d3: '{{ STATIC_URL }}matta-libs/d3.v3.min',
        aurora: '{{ STATIC_URL }}libs/aurora',
        moment: '{{ STATIC_URL }}libs/moment-with-locales.min',
        underscore: '{{ STATIC_URL }}libs/underscore-min',
        masonry: '{{ STATIC_URL }}libs/masonry.pkgd.min',
        imagesLoaded: '{{ STATIC_URL }}libs/imagesloaded.pkgd.min',
        spin: '{{ STATIC_URL }}libs/spin.min',
        matta: '{{ STATIC_URL }}matta-libs/matta',
        wordcloud: '{{ STATIC_URL }}matta-libs/d3.layout.cloud',
        seedrandom: '{{ STATIC_URL }}libs/seedrandom.min'
    }
});