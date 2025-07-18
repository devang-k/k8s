def write_to_markdown(output_file, data):
    with open(output_file, "w") as f:
        f.write("# Metrics Analysis\n")
        for layer, metrics in data.items():
            f.write(f"## Layer: {layer}\n")
            f.write(f"- **Total Area**: {metrics['total_area']}\n")
            f.write(f"- **Total Length**: {metrics['total_length']}\n")
            f.write(f"- **Number of Polygons**: {metrics['num_polygons']}\n")
