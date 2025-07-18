logger = logging.getLogger('sivista_app')


class Writer:

    def write_layout(self,
                     layout: db.Layout,
                     top_cell: db.Cell,
                     output_dir: str,
                     file_name: str
                     ) -> None:
        pass


def remap_layers(layout: db.Layout, output_map: Dict[str, Union[Tuple[int, int], List[Tuple[int, int]]]]) -> db.Layout:
    """
    Rename layer to match the scheme defined in the technology file.
    :param layout:
    :param output_map: Output mapping from layer names to layer numbers.
    :return:
    """
    logger.debug("Remap layers.")
    layout2 = db.Layout()

    for top1 in layout.each_cell():
        top2 = layout2.create_cell(top1.name)
        layer_infos1 = layout.layer_infos()
        for layer_info in layer_infos1:

            src_layer = (layer_info.layer, layer_info.datatype)

            if src_layer not in layer_stack.layermap_reverse:
                msg = "Layer {} not defined in `layermap_reverse`.".format(src_layer)
                logger.warning(msg)
                dest_layers = src_layer
            else:
                src_layer_name = layer_stack.layermap_reverse[src_layer]

                if src_layer_name not in output_map:
                    msg = "Layer '{}' will not be written to the output. This might be alright though.". \
                        format(src_layer_name)
                    logger.warning(msg)
                    continue

                dest_layers = output_map[src_layer_name]

            if not isinstance(dest_layers, list):
                dest_layers = [dest_layers]

            src_idx = layout.layer(layer_info)
            for dest_layer in dest_layers:
                dest_idx = layout2.layer(*dest_layer)
                top2.shapes(dest_idx).insert(top1.shapes(src_idx))

    return layout2
