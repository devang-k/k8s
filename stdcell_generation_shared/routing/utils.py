def calculate_nanosheet_region(shapes):
    for layer, _shapes in shapes.items():
        if layer == pdiff:
            pnanosheet_region = optimize_shape_merge(_shapes)
        if layer == ndiff:
            nnanosheet_region = optimize_shape_merge(_shapes)
    nanosheet_region = pya.Region(pnanosheet_region) + pya.Region(nnanosheet_region)
    nanosheet_region.merge()
    return nanosheet_region

def polygon_centers(shapes, layer_name):
    """Provides the list for the center of the polygon"""
    polygon_center_list= []
    for layer, _shapes in shapes.items():
        if layer == layer_name:
            polygon_center_list = [s.bbox().center().x for s in _shapes]
    return polygon_center_list