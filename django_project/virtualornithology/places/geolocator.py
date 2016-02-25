from .models import KnownName
import regex as re 


# instead of doing name processing here, we prefer to have a list of already known names for different locations, and match against those.
# we return the most specific location(s). we make the best effort to avoid duplicate locations.
def geolocate(name):
    name = KnownName.prepare_name(name)
    queryset = KnownName.objects.filter(normalized_name=name)

    specific_locations = []
    candidates = set([k.location for k in queryset.select_related()])

    if not candidates:
        return specific_locations

    max_depth = max(candidates, key=lambda x: x.depth).depth
    min_depth = min(candidates, key=lambda x: x.depth).depth
    depths = {}

    # we group by depth to filter locations that have childs in the results. example: Santiago(city) -> Santiago (municipality) 
    for d in range(min_depth, max_depth + 1):
        depths[d] = []

    for c in candidates:
        depths[c.depth].append(c)
        
    for d in range(min_depth, max_depth):
        for parent in depths[d]:
            has_childs = bool(filter(lambda x: x.parent == parent, depths[d+1]))
            if not has_childs:
                specific_locations.append(parent)

    specific_locations.extend(depths[max_depth])

    return specific_locations


# TODO: use a _real_ pattern! the idea is that we can add many known texts here
coordinate_re = (
    re.compile(r'.+: (-?.+),(-?.+)'), 
    re.compile(r'(-?.+),(-?.+)')
)


def extract_lat_lon(text):
    res = None

    for exp in coordinate_re:
        matched = exp.match(text)
        if matched:
            try:
                res = map(float, matched.groups())
            except ValueError:
                res = None
            finally:
                break

    return res
