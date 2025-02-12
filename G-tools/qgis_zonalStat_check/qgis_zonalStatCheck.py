# "admin3Name" = 'Tahtay Adiyabo' AND ("Pop_sum_ro" < 2000 OR "Pop_sum_ro" > 3500)

# Parameter Definitions
shapefile_path = r"C:/Users/orenaike/OneDrive/02_JOBS/IOM/1_OPERATIONS/Ethiopia/EA_2025/EAS/EAS.shp"
raster_path = r"C:/Users/orenaike/OneDrive/02_JOBS/IOM/1_OPERATIONS/Ethiopia/EA_2025/World_Pop/eth_ppp_2020_UNadj_constrained.tif"

# Filters
subset_filter = "admin3Name = 'Tahtay Adiyabo'"  # Filter by admin3Name
pop_sum_filter = None  # Optional filter by Pop_sum_ro, set to None if not needed
# pop_sum_filter = "(\"Pop_sum_ro\" < 2000 OR \"Pop_sum_ro\" > 3500)"  # Filter for Pop_sum_ro outside 2000 and 3500
# pop_sum_filter = "(\"Pop_sum_ro\" >= 2000 AND \"Pop_sum_ro\" <= 3500)"  # Filter for Pop_sum_ro between 2000 and 3500


# Geometry fix and zonal statistics parameters
fix_geometry_method = 1  # Method for fixing geometries
zonal_statistics = [1]  # Sum statistics
output_layer_memory = "memory:"  # Memory layer output

# Load the shapefile as a vector layer
layer = QgsVectorLayer(shapefile_path, "EAS Layer", "ogr")

# Check if the layer is valid
if not layer.isValid():
    print("Layer failed to load!")
else:
    print("Layer loaded successfully!")

    # Fix geometries
    fix_params = {
        'INPUT': layer,
        'METHOD': fix_geometry_method,
        'OUTPUT': output_layer_memory
    }
    fixed_layer = processing.run("native:fixgeometries", fix_params)['OUTPUT']

    # Apply filter conditionally
    if pop_sum_filter:  # Check if pop_sum_filter is defined
        combined_filter = f"({subset_filter}) AND {pop_sum_filter}"
    else:
        # Use only subset_filter if no pop_sum_filter is provided
        combined_filter = subset_filter

    fixed_layer.setSubsetString(combined_filter)

    # Load the raster layer
    raster_layer = QgsRasterLayer(raster_path, "Population Raster")
    if not raster_layer.isValid():
        print("Raster failed to load!")
    else:
        print("Raster loaded successfully!")

        # Run zonal statistics
        zonal_params = {
            'INPUT': fixed_layer,
            'INPUT_RASTER': raster_layer,
            'COLUMN_PREFIX': 'pop_',
            'STATISTICS': zonal_statistics,
            'OUTPUT': output_layer_memory
        }

        try:
            result = processing.run("native:zonalstatisticsfb", zonal_params)
            result_layer = result['OUTPUT']

            # Collect features into a list with calculated vertices count
            features = []
            for feature in result_layer.getFeatures():
                gat_id = feature['GATid']
                feature_id = feature.id()
                pop_sum = feature['pop_sum']
                vertices_count = sum(1 for _ in feature.geometry().vertices())

                # Handle None values for population sum
                if pop_sum is None:
                    pop_sum_value = 0  # Use 0 for sorting purposes
                    pop_sum_str = "No Data"
                else:
                    pop_sum_value = int(pop_sum)
                    pop_sum_str = f"{pop_sum_value:,}"

                # Append feature data to list
                features.append((vertices_count, pop_sum_value,
                                pop_sum_str, gat_id, feature_id))

            # Sort features by vertices count (descending order)
            features.sort(key=lambda x: x[0], reverse=True)

            # Create and print table header
            print("\nPopulation Summary (Filtered and Sorted by Vertices Count):")
            print("-" * 85)
            print(
                f"{'Vertices Count':<15} | {'Population Sum':>15} | {'GAT ID':<10} | {'Feature ID':<10}")
            print("-" * 85)

            # Print sorted table rows
            for vertices_count, pop_sum_value, pop_sum_str, gat_id, feature_id in features:
                print(
                    f"{vertices_count:<15} | {pop_sum_str:>15} | {str(gat_id):<10} | {feature_id:<10}")

            print("-" * 85)

        except QgsProcessingException as e:
            print(f"Error running the zonal statistics: {e}")
