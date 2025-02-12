from qgis.core import *
from qgis.analysis import QgsNativeAlgorithms
import processing
from math import radians, cos, sin, asin, sqrt
import math

# Parameter Definitions
parameters = {
    "shapefile_path": r"C:\Users\orenaike\OneDrive\02_JOBS\IOM\1_OPERATIONS\Ethiopia\EA_2025\EAS\EASCheck\eth_verification_gat\eth_verification_gat_v2.shp",
    "raster_path": r"C:/Users/orenaike/OneDrive/02_JOBS/IOM/1_OPERATIONS/Ethiopia/EA_2025/eth_general_2020_geotiff/MetaFocus_v1.tif",
    "subset_filter": "admn3Nm = 'Tahtay Adiyabo'",  # Can be None
#    "subset_filter": None,  # Can be None
    "old_pop_column": "Met_Pop",  # Name of the old population column
    "min_value": 2000,
    "max_value": 3500,
    "worldpop_filter": None,  # Example: "(pop_sum >= 2000 AND pop_sum <= 3500)" or None
    "fix_geometry_method": 1,  # 1: Structure repair; 2: Topology repair
    "zonal_statistics": [1],  # Statistics to calculate (e.g., [1] for sum)
    "output_layer_memory": "memory:",
}

# Helper Functions
def calculate_centroid(feature):
    centroid = feature.geometry().centroid().asPoint()
    return centroid.y(), centroid.x()

def calculate_area(feature):
    geom = feature.geometry()
    projected_geom = QgsGeometry(geom)
    source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
    dest_crs = QgsCoordinateReferenceSystem("EPSG:32637")
    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
    projected_geom.transform(transform)
    return projected_geom.area() / 1_000_000

def calculate_polsby_popper(feature):
    geom = feature.geometry()
    projected_geom = QgsGeometry(geom)
    source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
    dest_crs = QgsCoordinateReferenceSystem("EPSG:32637")
    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
    projected_geom.transform(transform)
    
    area = projected_geom.area()
    perimeter = projected_geom.length()
    
    if perimeter == 0:
        return 0
    
    return (4 * math.pi * area) / (perimeter * perimeter)

def calculate_bounds_height(feature):
    """Calculate the height of bounding box in meters"""
    return feature.geometry().boundingBox().height() * 10000

def get_population_indicator(pop_value, min_value, max_value):
    if pop_value is None:
        return ""
    if pop_value < min_value:
        return "↓"
    elif pop_value > max_value:
        return "↑"
    return " "

# Load the shapefile
layer = QgsVectorLayer(parameters["shapefile_path"], "EAS Layer", "ogr")

if not layer.isValid():
    print("Layer failed to load!")
else:
    print("Layer loaded successfully!")

    # Fix geometries
    fix_params = {
        'INPUT': layer,
        'METHOD': parameters["fix_geometry_method"],
        'OUTPUT': parameters["output_layer_memory"]
    }
    fixed_layer = processing.run("native:fixgeometries", fix_params)['OUTPUT']

    # Apply filters
    combined_filter = None
    subset_filter = parameters["subset_filter"]
    if subset_filter:
        combined_filter = subset_filter

    if combined_filter:
        fixed_layer.setSubsetString(combined_filter)

    # Check if raster is already loaded
    raster_layer = None
    for layer in QgsProject.instance().mapLayers().values():
        if layer.source() == parameters["raster_path"]:
            raster_layer = layer
            print("Raster already loaded, reusing it.")
            break

    # If raster is not loaded, load it
    if not raster_layer:
        raster_layer = QgsRasterLayer(parameters["raster_path"], "Population Raster")
        if not raster_layer.isValid():
            print("Raster failed to load!")
        else:
            QgsProject.instance().addMapLayer(raster_layer)
            print("Raster loaded successfully!")

    if raster_layer and raster_layer.isValid():
        # Zonal statistics
        zonal_params = {
            'INPUT': fixed_layer,
            'INPUT_RASTER': raster_layer,
            'RASTER_BAND': 1,
            'COLUMN_PREFIX': 'pop_',
            'STATISTICS': parameters["zonal_statistics"],
            'OUTPUT': parameters["output_layer_memory"]
        }
        try:
            result = processing.run("native:zonalstatisticsfb", zonal_params)
            result_layer = result['OUTPUT']
            features = []
            below_min = 0
            within_range = 0
            above_max = 0

            for feature in result_layer.getFeatures():
                if not feature.geometry() or feature.geometry().isEmpty():
                    print(f"Feature with ID {feature.id()} has null geometry.")
                    continue

                feature_id = feature.id()
                old_pop = feature[parameters["old_pop_column"]]
                new_pop = feature['pop_sum']
                vertices_count = sum(1 for _ in feature.geometry().vertices())
                lat, lon = calculate_centroid(feature)
                pp_index = calculate_polsby_popper(feature)
                bounds_height = calculate_bounds_height(feature)

                old_pop_str = "No Data" if old_pop is None else f"{int(old_pop):,}"
                new_pop_str = "No Data" if new_pop is None else f"{int(new_pop):,}"

                if new_pop is not None:
                    if new_pop < parameters["min_value"]:
                        below_min += 1
                    elif parameters["min_value"] <= new_pop <= parameters["max_value"]:
                        within_range += 1
                    elif new_pop > parameters["max_value"]:
                        above_max += 1

                worldpop_filter = parameters["worldpop_filter"]
                if worldpop_filter:
                    filter_condition = eval(worldpop_filter.replace("pop_sum", str(new_pop))) if new_pop is not None else False
                    if not filter_condition:
                        continue

                features.append((lat, lon, vertices_count, old_pop_str, new_pop_str, 
                               feature_id, new_pop, calculate_area(feature), 
                               pp_index, bounds_height))

            # Sort features
            features.sort(key=lambda x: (-x[0], x[1]))

            # Print results
            total_features = len(features)
            if subset_filter:
                print(f"\nTotal Rows Processed in {subset_filter}: {total_features}")
            else:
                print(f"\nTotal Rows Processed: {total_features}")

            print("-" * 85)
            print(f"{'Vert':<4} | {'B_height(m)':>9} | {'Orig Pop':>8} | {'MetaPop':>10} | {'FID':>4} | {'Area(km²)':>8} | {'PP Index':>7}")
            print("-" * 85)

            for lat, lon, vertices_count, old_pop, new_pop_str, feature_id, new_pop, area, pp_index, bounds_height in features:
                indicator = get_population_indicator(new_pop, parameters["min_value"], parameters["max_value"])
                formatted_new_pop = f"{indicator}{new_pop_str}"
                
                pp_index_str = f"{pp_index:>7.3f}"
                if pp_index < 0.25:
                    pp_index_str += "*"
                
                print(f"{vertices_count:<4} | {bounds_height:>9.3f} | {old_pop:>8} | {formatted_new_pop:>10} | {feature_id:>4} | {area:>8.2f} | {pp_index_str}")

            print("-" * 85)

            # Print summary
            print("\nSummary:")
            if subset_filter:
                print(f"Total Rows Processed in {subset_filter}: {total_features}")
            else:
                print(f"Total Rows Processed: {total_features}")
            print(f"Below {parameters['min_value']}: {below_min}")
            print(f"Within {parameters['min_value']}-{parameters['max_value']}: {within_range}")
            print(f"Above {parameters['max_value']}: {above_max}")

        except QgsProcessingException as e:
            print(f"Error running the zonal statistics: {e}")