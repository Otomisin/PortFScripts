# PopEA Delineation Tool

A robust ArcGIS toolbox for automated generation of enumeration areas based on population density and administrative boundaries.

## Overview

The PopEA Delineation Tool is designed to process population raster data (such as WorldPop) to create logical enumeration areas for surveys and census operations. It combines population distribution data with administrative boundaries to generate areas that reflect both population patterns and administrative divisions.

## Features

- Automated processing of population raster data
- Two-stage polygon aggregation for optimal area delineation
- Population threshold-based filtering
- Integration with administrative boundaries
- Comprehensive zonal statistics calculation
- Euclidean allocation for complete coverage
- Flexible output options and customization

## Requirements

- ArcGIS Pro 2.9 or higher
- Spatial Analyst extension
- Python 3.x (included with ArcGIS Pro)
- Sufficient storage space for intermediate outputs
- Administrative boundary data
- Population raster data (e.g., WorldPop)

## Installation

1. Clone this repository or download the .pyt file
```bash
git clone https://github.com/yourusername/popea-delineation-tool.git
```

2. Open ArcGIS Pro
3. In the Catalog pane, right-click on Toolboxes
4. Select "Add Toolbox" and navigate to the downloaded .pyt file
5. The tool will appear as "PopEA Delineation Tool" in your toolbox

## Usage

### Basic Steps

1. Open the tool in ArcGIS Pro
2. Input your population raster dataset
3. Specify your administrative boundary
4. Set your subadministrative boundary
5. Configure optional parameters as needed
6. Run the tool

### Required Inputs

- **Population Raster**: WorldPop or similar population distribution data
- **Administrative Boundary**: Primary area of interest
- **Subadministrative Boundary**: Secondary boundaries for final join

### Optional Parameters

- **Output Geodatabase**: Location for output files
- **Output Name Prefix**: Custom prefix for output files
- **Simplify Polygons**: Option to simplify polygon geometries
- **Aggregation Distances**: Customize the 2-stage aggregation process
- **Filter Value**: Population threshold (default: 650)
- **Binary Filter**: Filter options based on population threshold

## Output Files

The tool generates several outputs, with the final results being:

- `[prefix]_Final_Output_WithStats`: Final enumeration areas with population statistics
- Various intermediate outputs for quality control and verification

## Best Practices

1. **Data Preparation**
   - Ensure your population raster is in the correct projection
   - Verify administrative boundaries are clean and topologically correct
   - Have sufficient disk space for processing

2. **Parameter Selection**
   - Adjust aggregation distances based on settlement patterns
   - Set population thresholds according to local requirements
   - Consider simplification options for complex inputs

3. **Quality Control**
   - Review intermediate outputs
   - Verify population statistics
   - Check boundary alignments

## Troubleshooting

Common issues and solutions:

- **Memory Errors**: Reduce input raster size or increase available memory
- **Processing Time**: Adjust simplification parameters for faster processing
- **Boundary Mismatches**: Check projection systems of input data

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Insert your chosen license here]

## Credits

Developed by IOM DTM

## Contact

[Your contact information or organization's contact]

## Changelog

### Version 1.0.0 (2025-01-11)
- Initial release
- Basic functionality implemented
- Documentation completed

---

For more detailed technical documentation, please refer to the [Wiki](link-to-wiki).