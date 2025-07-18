logger = logging.getLogger('sivista_app')

start_time = time.time()
timeout = 20

routing_order = {
    'pdiffcon': 1,
    'ndiffcon': 2,
    'ppoly': 1,
    'npoly': 2
}

# # Routing edge weights per data base unit.
horizontal_edge_weights = {
    'metal0': 10,
    'back_metal0': 1,
    'nanosheet': 1,
}
vertical_edge_weights = {
    'ndiffcon': 20,
    'pdiffcon': 20,
    'poly': 20,
    'npoly': 20,
    'ppoly': 20,
}

# Via weights.
via_weightage = {
    ('metal0', 'ndiffcon'): 5,
    ('metal0', 'pdiffcon'): 5,
    ('back_metal0', 'ndiffcon'): 5,
    ('back_metal0', 'pdiffcon'): 5,
    ('metal0', 'poly'): 5,
    ('metal0', 'npoly'): 5,
    ('metal0', 'ppoly'): 5,
    ('nanosheet', 'ndiffcon'): 5,
    ('nanosheet', 'pdiffcon'): 5,
    ('nanosheet', 'poly'): 5,
    ('nanosheet', 'npoly'): 5,
    ('nanosheet', 'ppoly'): 5,
}

def has_timed_out(start_time, timeout):
    return (int(time.time() - start_time)) > timeout

# ToDo:Logic can be optimized
def create_rectangle_from_center(center_x, center_y, length, height):
    # Calculate the half-length and half-height
    half_length = length // 2
    half_height = height // 2
    
    # Calculate the coordinates of the lower-left and upper-right corners
    ll_x = center_x - half_length
    ll_y = center_y - half_height
    ur_x = center_x + half_length
    ur_y = center_y + half_height
    
    # Create the rectangle as a pya.Box object
    rectangle = pya.Box(ll_x, ll_y, ur_x, ur_y)
    return rectangle

def flipping(tech, layout):
    '''This function has the flipping logic'''
    if tech.backside_power_rail:
        if tech.flipped == "R0":
            if tech.height_req == 1:
                layout.transform(db.DCplxTrans(1.0, 0, True, 0, (tech.cell_height + (tech.power_rail_width/2)) * 0.001))
            else:
                layout.transform(db.DCplxTrans(1.0, 0, True, 0, (tech.cell_height - (tech.power_rail_width/2)) * 0.001))
        if tech.flipped == "Mx":
            logger.info("Performing Vertical Flip")
            layout.transform(db.DCplxTrans(1.0, 0, False, 0, (tech.power_rail_width/2) * 0.001))
        if tech.flipped == "My":
            logger.info("Performing Horizontal Flip")
            if tech.height_req == 1:
                layout.transform(db.DCplxTrans(1.0, 180, False, tech.cell_width * 0.001, (tech.cell_height + (tech.power_rail_width/2)) * 0.001))
            else:
                layout.transform(db.DCplxTrans(1.0, 180, False, tech.cell_width * 0.001, (tech.cell_height - (tech.power_rail_width/2)) * 0.001))
    else:
        if tech.flipped == "R0":
            layout.transform(db.DCplxTrans(1.0, 0, True, 0, tech.cell_height * 0.001))
        if tech.flipped == "Mx":
            logger.info("Performing Vertical Flip")
        if tech.flipped == "My":
            logger.info("Performing Horizontal Flip")
            layout.transform(db.DCplxTrans(1.0, 180, False, tech.cell_width * 0.001, tech.cell_height * 0.001))
