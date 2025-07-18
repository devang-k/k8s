# Metrics Calculation Documentation

## Introduction

The `calculate_metrics.py` script is part of the DTCO-ML Standard Cell Library Optimization project. Its purpose is to calculate various metrics from GDSII JSON files, which are commonly used in semiconductor fabrication processes. This documentation provides an overview of what the script does, why it does it, how it accomplishes its tasks, and the format specification for the layer map file.

## Purpose

The primary purpose of this script is to analyze GDSII JSON files and extract key metrics related to the layers and elements within those files. These metrics are vital for optimizing semiconductor design libraries. The script calculates the following metrics:

1. Total polygon area / metal volume per layer.
2. Total cell area.
3. Highest metal layer.

## Usage

To use the script, follow the usage instructions below:

```
Usage:
    python calculate_metrics.py input_path/ layer_map_file [--output-format FORMAT]

Options:
    input_path/        Path to a JSON file or a directory containing JSON files for analysis.
    layer_map_file     Path to the layer map file defining mappings between GDSII layers and purposes.
    --output-format FORMAT   (optional) Specify the desired output format for calculated metrics.
                             Available options: "csv," "json," or "markdown." Default is "json."
```

### Input Parameters

- `input_path/`: This parameter specifies the path to a JSON file or a directory containing JSON files that you want to process for metrics calculation.

- `layer_map_file`: The script relies on a layer map file to map layers and purposes from GDSII layernums and datatypes. This file is essential for accurate metrics calculation.

- `--output-format FORMAT` (optional): Use this parameter to specify the desired output format for the calculated metrics. The available options are "csv," "json," or "markdown." If not provided, the default format is "json."

## How It Works

The script uses the Shapely library to perform geometric operations on polygonal shapes within the JSON files. It follows these steps to calculate metrics:

1. Reads the input JSON file(s) and extracts the relevant information, including layers, datatypes, and coordinates.

2. Processes the coordinates to create polygons and organize them by layer and purpose.

3. Calculates the total polygon area / metal volume, total cell area, and highest metal layer for each layer and purpose.

4. Writes the calculated metrics to an output file in the specified format (CSV, JSON, or Markdown).

## Layer Map Format Specification

The `layer_map_file` is a plain text file that defines the mapping between GDSII layers and their purposes. It follows this format:

```
# Layer map for mono-CFET technology

# layername                         layerurpose             stream#     datatype
NMOS_NANOSHEET                      drawing                 100         0
NMOS_ACT_PATTERNED                  drawing                 100         1
PMOS_NANOSHEET                      drawing                 101         0
PMOS_ACT_PATTERNED                  drawing                 101         1
NMOS_GATE                           drawing                 102         0
PMOS_GATE                           drawing                 103         0
SINGLE_DIFFUSION_BREAK              drawing                 121         0
NMOS_LI                             drawing                 104         0
PMOS_LI                             drawing                 105         0
VIA_LI_TO_BACKSIDE_POWER_TSVBAR     drawing                 111         0
VIA_PMOS_LI_TO_NMOS_LI              drawing                 123         0
VIA_M0_TO_PMOS_LI_VCT               drawing                 108         0
VIA_M0_TO_PMOS_GATE_VG              drawing                 106         0
M2_BACKSIDE_POWER_LINES             drawing                 300         0
BACKSIDE_POWER_LINES_LABEL          drawing                 300         1
M0                                  drawing                 200        0
M0_LABEL                            drawing                 200        1
CELL_BOUNDARY                       drawing                 1       0
```

This file provides the necessary mapping information for the script to identify layers and purposes accurately.

## Conclusion

The `calculate_metrics.py` script is a crucial tool for optimizing semiconductor design libraries. By extracting and analyzing metrics from GDSII JSON files, it enables data-driven improvements in the design process. Understanding its purpose, usage, and the format of the layer map file is essential for effectively utilizing this script in your semiconductor projects.