# Zonal Statistics Advanced Tool

## Overview
The Zonal Statistics Advanced Tool is a custom ArcGIS Pro geoprocessing tool designed to process population raster data using administrative boundaries. It performs raster clipping, zonal statistics calculations, and generates feature layers with both raw and rounded population sums.

## Features
- Clips population raster to administrative boundaries
- Calculates zonal statistics for population totals
- Generates output with both raw (double) and rounded (long) population fields
- Automatically adds suffix from input raster name to output fields
- Includes robust map display functionality
- Supports custom output geodatabase and naming prefixes

## Requirements
- ArcGIS Pro (Licensed)
- Spatial Analyst Extension
- Python 3.x

## Installation
1. Clone or download this repository to your local machine
2. Open ArcGIS Pro
3. In the Catalog pane, connect to the folder containing the toolbox
4. The tool will appear under the "Zonal_Stats_Advanced" toolbox

## Parameters

### Required Parameters
1. **Input Population Raster**
   - Type: Raster Layer
   - Description: Input raster file containing population data
   - Format: Any valid raster format supported by ArcGIS Pro

2. **Administrative Boundary**
   - Type: Feature Layer
   - Description: Feature layer defining the boundaries for analysis
   - Format: Any valid vector format supported by ArcGIS Pro

### Optional Parameters
3. **Output Geodatabase**
   - Type: Workspace
   - Description: Location where output files will be stored
   - Default: Same directory as input raster

4. **Output Prefix**
   - Type: String
   - Description: Prefix for all output files
   - Default: First 10 characters of input raster name + "_PreEnum"

## Outputs
The tool generates several outputs in the specified geodatabase:

1. **{prefix}_Final_Cleaned**
   - Type: Feature Layer
   - Contains:
     - Pop_sum_{rastername}: Raw population sum (double)
     - Pop_sum_rounded_{rastername}: Rounded population sum (long)
   - Automatically added to the current map

### Intermediate Files (automatically cleaned up)
- {prefix}_TempBoundary
- {prefix}_Clipped
- {prefix}_ZonalStats
- {prefix}_Final

## Usage Example
```python
# Tool parameters example
Input Population Raster: eth_meta_focus.tif
Administrative Boundary: EAS_2025_ExportFeatures
Output Geodatabase: C:/GIS/Outputs/Analysis.gdb
Output Prefix: test
```

This will create:
- test_Final_Cleaned (with fields Pop_sum_ethmetafoc and Pop_sum_rounded_ethmetafoc)

## Processing Steps
1. Creates temporary copy of administrative boundary
2. Clips raster to boundary
3. Calculates zonal statistics
4. Joins statistics to boundary
5. Creates and calculates population fields
6. Cleans up intermediate files
7. Adds result to current map

## Error Handling
- Robust error handling for map addition
- Detailed progress messages
- Cleanup of temporary files even if processing fails
- Validation of input parameters

## Best Practices
1. Ensure input raster and boundary are in the same coordinate system
2. Verify sufficient disk space in output location
3. Check that Spatial Analyst extension is available
4. Use meaningful output prefixes for better organization

## Known Limitations
- Field names are limited to valid ArcGIS field naming conventions
- Raster name suffix is limited to 10 characters
- Requires active ArcGIS Pro session for map display

## Troubleshooting
1. **Map Display Issues**
   - Verify ArcGIS Pro is running
   - Check active map exists
   - Ensure sufficient permissions

2. **Processing Errors**
   - Verify input data validity
   - Check coordinate systems match
   - Ensure sufficient disk space
   - Verify Spatial Analyst license

## Support
For issues or questions:
1. Check the troubleshooting section
2. Verify input data meets requirements
3. Contact tool administrator

## Future Considerations

### 1. Enhanced Statistical Options
Plans to add a parameter for selecting various statistical calculations:

- **Mean** - Average of all cells in each zone
- **Majority** - Most frequent value in each zone
- **Maximum** - Highest value in each zone
- **Median** - Middle value in each zone
- **Minimum** - Lowest value in each zone
- **Minority** - Least frequent value in each zone
- **Range** - Difference between highest and lowest values
- **Standard Deviation** - Statistical dispersion measure
- **Sum** - Total of all values (currently implemented)

### 2. Additional Planned Enhancements
- Multiple raster input support for batch processing
- Custom field naming templates
- Optional weighted calculations
- Export capabilities for various formats
- Integration with automated workflows
- Additional validation checks for input data
- Performance optimizations for large datasets
- Support for different aggregation methods
- Optional preprocessing steps (e.g., raster resampling)


## Version History
- 1.0.0 (January 2025)
  - Initial release
  - Basic functionality
- 1.1.0 (January 2025)
  - Added raster name suffix to output fields
  - Enhanced map display reliability
  - Improved error handling