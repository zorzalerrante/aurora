import pandas
import pytz

# see documentation for pandas here http://pandas.pydata.org/pandas-docs/stable/timeseries.html?highlight=date_range
def daterange_queryset(queryset, start, end, attribute='datetime'):
        gte = attribute + '__gte'
        lt = attribute + '__lt'
        return queryset.filter(**{gte: start, lt: end})


def build_timeseries(queryset, start, end, unit='minutes', multiples=1, attribute='datetime', plain=False,
                     isoformat=True, normalize=False):
    valid_freqs = {
        'minutes': 't',
        'days': 'd',
        'weeks': 'w',
        'months': 'm',
        'years': 'a',
        'hours': 'h'
    }

    maybe_naive_units = pandas.date_range(start, end, freq='{0}{1}'.format(multiples, valid_freqs[unit]))
    try:
        units = [pytz.timezone("UTC").localize(d) for d in maybe_naive_units]
    except ValueError:
        units = maybe_naive_units

    pairs = zip(units[0:-2], units[1:])

    ts = [{
        'count': daterange_queryset(queryset, p[0].to_datetime(), p[1].to_datetime(), attribute=attribute).count(),
        'datetime': (p[0]).isoformat() if isoformat else p[0]
    } for p in pairs]

    if normalize:
        max_date = max(ts, key=lambda x: x['count'])
        max_val = float(max_date['count'])
        for t in ts:
            t['count'] = t['count'] / max_val

    if plain:
        return [x['count'] for x in ts]

    return ts

