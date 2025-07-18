def nwell_layer(shapes: Dict[str, db.Shapes],
                shape: Tuple[int, int],
                tech: None) -> None:
    """
    Nwell layer creation coordinates calculation.
    """
    width, height = shape

    top_y = height // 2 - tech.np_spacing // 2 + tech.gate_extension
    bottom_y = height // 2 - tech.np_spacing // 2 - tech.nanosheet_width - tech.gate_extension
    left_x = 0
    right_x = width
 
    n_well = db.Box(
        db.Point(left_x, top_y),
        db.Point(right_x, bottom_y)
    )

    shapes[nwell].insert(n_well)