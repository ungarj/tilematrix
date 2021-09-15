import math

STRIPE_WIDTH_DEG = 6.
UTM_TOP = 84.
UTM_BOTTOM = -80
UTM_STRIPE_COUNT = 60


def utm_stripe_epsg(stripe_id):
    """
    Return EPSG code from UTM stripe ID.

    stripe_id: e.g. 33N --> EPSG:32633
    32: UTM EPSG prefix
    6 or 7: N or S
    33: UTM stripe
    """
    return "EPSG:32%s%s" % (
        "6" if _hemisphere(stripe_id) == "N" else "7",
        _stripe(stripe_id)
    )


def stripe_id_from_point(point):
    """
    Return UTM stripe ID from point.

    Parameters
    ----------
    point : Point geometry in EPSG:4326
    """
    stripe = int(math.ceil((180. + point.x) / STRIPE_WIDTH_DEG))
    if 0. <= point.y <= UTM_TOP:
        hemisphere = "N"
    elif UTM_BOTTOM <= point.y < 0.:
        hemisphere = "S"
    else:
        raise ValueError("point outside UTM bounds: %s", repr(point))
    return "%s%s" % (str(stripe), hemisphere)


def _stripe(stripe_id):
    s = stripe_id[:2]
    if int(s) > UTM_STRIPE_COUNT:
        raise ValueError("invalid UTM stripe ID: %s" % stripe_id)
    return s


def _hemisphere(stripe_id):
    if not isinstance(stripe_id, str) or len(stripe_id) != 3:
        raise TypeError("invalid UTM stripe ID: %s" % stripe_id)
    hemisphere = stripe_id[2]
    if hemisphere not in ["N", "S"]:
        raise ValueError("invalid UTM stripe ID: %s" % stripe_id)
    return hemisphere
