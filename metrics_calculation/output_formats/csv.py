import csv

def write_to_csv(output_file, data):
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Layer", "Total Polygon Area", "Total Polygon Length", "Number of Polygons"])
        for layer, metrics in data.items():
            writer.writerow([layer, metrics["total_area"], metrics["total_length"], metrics["num_polygons"]])
