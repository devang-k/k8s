def update_summary(tech, lvs, drc, cell_name, permuteKeys, placer_dict, layout_summary, file_name='null', shapes=None, remark=''):
    bounding_box = [s for s in shapes['cell_boundary']][0].polygon.bbox() if shapes else None
    layout_data = {
        'DRC': drc,
        'LVS': lvs,
        'Cells': cell_name,
        'File name': file_name,
        'Cell height (μm)': (bounding_box.top - bounding_box.bottom) / (tech.scaling_factor * 1000) if bounding_box else None,
        'Cell width (μm)': (bounding_box.right - bounding_box.left) / (tech.scaling_factor * 1000) if bounding_box else None,
    }
    for key in permuteKeys:
        val = getattr(tech, key[0])
        disp_key = None
        if key[1]:
            if type(key[1]) == tuple:
                disp_key = '-'.join([globals().get(k, k) for k in key[1]])
            else:
                disp_key = globals().get(key[1], key[1])
            val = val[key[1]]
        if key[0] == 'placer':
            val = placer_dict[val]
        if isinstance(val, (int, float)) and not isinstance(val, bool) and key[0] not in ['number_of_routing_tracks', 'height_req']:
            val /= tech.scaling_factor
        json_key = globals().get(key[0], key[0])
        if key[1]:
            json_key = f'{json_key}-{disp_key}'
        layout_data[tech.display_names.get(json_key, json_key)] = val
    for k in tech.__dict__.keys():
        if k in tech.display_names and tech.display_names.get(k, k) not in layout_data:
            val = getattr(tech, k)
            if isinstance(val, (int, float)) and not isinstance(val, bool) and k not in ['number_of_routing_tracks', 'height_req']:
                val /= tech.scaling_factor
            layout_data[tech.display_names.get(k, k)] = val
    layout_data['remark'] = remark
    layout_summary.append(layout_data)

def make_layout_summary_file(tech, lvs, drc, report_path, count, output_dir, gds_name='N/A', nets=[], highest_metal='N/A', lvs_extracted='N/A', lvs_reference='N/A'):
    layout_data = {
        'Layout ID number': count['total'],
        'Date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Tech file data': {tech.display_names.get(k, k): getattr(tech, k) for k in tech.__dict__.keys() if k in tech.display_names},
        'DRC pass': drc,
        'LVS pass': lvs,
        'Extracted netlist': '\n' + lvs_extracted,
        'Reference netlist': '\n' + lvs_reference,
        'GDS file name': gds_name,
        'Cell nets': nets,
        'Highest routed metal': highest_metal
    }
    text_content = "\n".join([f"{key}: {value}" for key, value in layout_data.items()])
    with open(output_dir + report_path, 'w') as text_file:
        text_file.write(text_content)
