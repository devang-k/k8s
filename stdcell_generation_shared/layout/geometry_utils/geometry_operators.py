def optimize_shape_merge(shapes):
    """Efficiently combines a list of shapes into a single merged region."""
    region = pya.Region(shapes)
    merged = pya.Region()

    # Accumulate all polygons
    merged |= region

    # Perform region merging
    merged.merge()

    # Replace original shapes with the merged result
    shapes.clear()
    shapes.insert(merged)

    return shapes

def is_near_region(point: Tuple[int, int], region: pya.Region, margin: int) -> bool:
    """Check if the point lies within a square margin of the given region."""
    pt = pya.Point(*point)
    proximity_box = pya.Box(pt - pya.Vector(margin, margin), pt + pya.Vector(margin, margin))
    return not region.interacting(pya.Region(proximity_box)).is_empty()

def get_nearby_points(points: Iterable[Tuple[int, int]], region: pya.Region, margin: int) -> list:
    """Returns points that fall within the specified margin of a given region."""
    return [point for point in points if is_near_region(point, region, margin)]

def is_point_near_region(point: Tuple[int, int], region: pya.Region, x_margin: int, y_margin: int) -> bool:
    """Check if a point lies within a specified margin around a region."""
    pt = pya.Point(*point)
    margin_box = pya.Box(pt - pya.Vector(x_margin, y_margin), pt + pya.Vector(x_margin, y_margin))
    return not pya.Region(margin_box).inside(region).is_empty()

def contains_point_with_margin(point: Tuple[int, int], region: pya.Region, margin: int) -> bool:
    """Check if a point lies within the region, allowing for a margin around it."""
    offset = pya.Vector(margin, margin)
    area = pya.Region(pya.Box(pya.Point(*point) - offset, pya.Point(*point) + offset))
    return not area.inside(region).is_empty()

def filter_points_within_region(points: Iterable[Tuple[int, int]], region: pya.Region, margin: int) -> list:
    """Return points that are considered inside the region, accounting for a margin."""
    return [pt for pt in points if contains_point_with_margin(pt, region, margin)]
