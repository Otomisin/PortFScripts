import os
from osgeo import gdal, ogr, osr
import numpy as np


def calculate_zonal_stats(vector_path, layer_name=None, raster_path=None, additional_fields=None, subset_filter=None,
                          pop_thresholds=None, output_format='table'):
    """
    Calculate zonal statistics for each feature in the shapefile or geodatabase with enhanced filtering and thresholds.

    Parameters:
    vector_path (str): Path to the input shapefile or geodatabase
    layer_name (str): Name of the layer within the geodatabase (optional for shapefile)
    raster_path (str): Path to the input raster
    additional_fields (dict): Additional fields to extract from the shapefile or geodatabase
    subset_filter (str): SQL-like filter for features
    pop_thresholds (dict): Population thresholds for indicators
    output_format (str): Output format ('table' or 'dict')
    """
    try:
        # Detect driver based on file extension
        driver_name = "OpenFileGDB" if vector_path.endswith(
            ".gdb") else "ESRI Shapefile"
        driver = ogr.GetDriverByName(driver_name)
        vector_ds = driver.Open(vector_path, 0)  # 0 = read-only

        if vector_ds is None:
            raise Exception("Could not open shapefile or geodatabase")

        raster_ds = gdal.Open(raster_path)
        if raster_ds is None:
            raise Exception("Could not open raster")

        print("Files loaded successfully!")

        # Select layer
        if vector_path.endswith(".gdb"):
            if not layer_name:
                raise Exception("Layer name is required for geodatabases")
            layer = vector_ds.GetLayerByName(layer_name)
        else:
            layer = vector_ds.GetLayer()

        if layer is None:
            raise Exception(f"Could not find the layer in {vector_path}")

        # Apply subset filter if provided
        if subset_filter and subset_filter.strip():
            layer.SetAttributeFilter(subset_filter)
        else:
            layer.SetAttributeFilter(None)
            print("Processing all features (no filter applied)")

        if pop_thresholds is None:
            pop_thresholds = {'min': 0, 'max': float('inf')}

        geo_transform = raster_ds.GetGeoTransform()
        raster_sr = osr.SpatialReference()
        raster_sr.ImportFromWkt(raster_ds.GetProjection())

        results = []
        feature_count = layer.GetFeatureCount()
        print(f"\nProcessing {feature_count} features...")

        for feature in layer:
            fid = feature.GetFID()
            geom = feature.GetGeometryRef()

            if geom is None or geom.IsEmpty():
                print(f"Feature ID {fid} has null/empty geometry")
                continue

            result = {'FID': fid}

            # Extract additional fields
            if additional_fields:
                for output_name, field_name in additional_fields.items():
                    field_value = feature.GetField(field_name)
                    result[output_name] = field_value if field_value is not None else None

            # Geometry bounding box
            minx, maxx, miny, maxy = geom.GetEnvelope()

            px_min = int((minx - geo_transform[0]) / geo_transform[1])
            px_max = int((maxx - geo_transform[0]) / geo_transform[1]) + 1
            py_min = int((maxy - geo_transform[3]) / geo_transform[5])
            py_max = int((miny - geo_transform[3]) / geo_transform[5]) + 1

            px_min, py_min = max(0, px_min), max(0, py_min)
            px_max, py_max = min(raster_ds.RasterXSize, px_max), min(
                raster_ds.RasterYSize, py_max)

            width, height = px_max - px_min, py_max - py_min

            if width <= 0 or height <= 0:
                print(f"Feature ID {fid} has invalid dimensions")
                continue

            mem_drv = gdal.GetDriverByName('MEM')
            mask_ds = mem_drv.Create('', width, height, 1, gdal.GDT_Byte)

            new_gt = (geo_transform[0] + px_min * geo_transform[1], geo_transform[1], 0,
                      geo_transform[3] + py_min * geo_transform[5], 0, geo_transform[5])
            mask_ds.SetGeoTransform(new_gt)
            mask_ds.SetProjection(raster_ds.GetProjection())

            mem_driver = ogr.GetDriverByName('Memory')
            mem_ds = mem_driver.CreateDataSource('')
            mem_layer = mem_ds.CreateLayer('temp', srs=raster_sr)

            feat_defn = mem_layer.GetLayerDefn()
            feat = ogr.Feature(feat_defn)
            feat.SetGeometry(geom)
            mem_layer.CreateFeature(feat)

            gdal.RasterizeLayer(mask_ds, [1], mem_layer, burn_values=[1])

            raster_data = raster_ds.GetRasterBand(
                1).ReadAsArray(px_min, py_min, width, height)
            mask_data = mask_ds.GetRasterBand(1).ReadAsArray()

            if raster_data is not None and mask_data is not None:
                raster_data = raster_data.astype(float)
                raster_data[np.isnan(raster_data)] = 0
                masked_data = np.ma.masked_array(
                    raster_data, mask=mask_data == 0)
                pop_sum = float(np.ma.sum(masked_data))
                if np.isnan(pop_sum):
                    pop_sum = 0
            else:
                pop_sum = 0

            result['Population'] = int(pop_sum)

            if pop_sum > pop_thresholds['max']:
                result['Threshold'] = '↑'
            elif pop_sum < pop_thresholds['min']:
                result['Threshold'] = '↓'
            else:
                result['Threshold'] = '-'

            results.append(result)

            mask_ds, mem_ds = None, None

        # Output result
        if output_format == 'dict':
            return results

        if results:
            columns = list(results[0].keys())
            col_widths = {
                col: max(len(str(r[col])) for r in results + [{col: col}]) for col in columns}

            header = " | ".join(f"{col:>{col_widths[col]}}" for col in columns)
            separator = "-" * len(header)

            print("\n" + separator)
            print(header)
            print(separator)

            for result in results:
                row = " | ".join(
                    f"{str(result[col]):>{col_widths[col]}}" for col in columns)
                print(row)

            print(separator)

            total_pop = sum(r['Population'] for r in results)
            print(f"\nSummary:")
            print(f"Total features processed: {len(results)}")
            print(f"Total population: {total_pop:,}")
            print(
                f"Features above threshold: {sum(1 for r in results if r['Threshold'] == '↑')}")
            print(
                f"Features below threshold: {sum(1 for r in results if r['Threshold'] == '↓')}")
            print(
                f"Features within threshold: {sum(1 for r in results if r['Threshold'] == '-')}")

        else:
            print("\nNo features processed.")

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

    finally:
        vector_ds = None
        raster_ds = None


# Example usage
if __name__ == "__main__":
    parameters = {
        # Path to the .gdb, not the layer
        # Use either .shp or .gdb
        "vector_path": r"C:\Users\orena\OneDrive\02_JOBS\IOM\1_OPERATIONS\Ethiopia\EA_2025\EA_2025_Operation_MAP.gdb",
        "layer_name": "test",  # Layer name inside the geodatabase
        "raster_path": r"C:/Users/orena/OneDrive/02_JOBS/IOM/1_OPERATIONS/Ethiopia/EA_2025/eth_general_2020_geotiff/MetaFocus_v1.tif",
        "additional_fields": {
            "Admin3": "admin3Name"
        },
        "subset_filter": "admin3Name = 'Tahtay Adiyabo'",
        "pop_thresholds": {
            "min": 2000,
            "max": 3500
        },
        "output_format": "table"
    }

    calculate_zonal_stats(
        parameters["vector_path"],
        layer_name=parameters["layer_name"],  # Must provide for .gdb
        raster_path=parameters["raster_path"],
        additional_fields=parameters["additional_fields"],
        subset_filter=parameters["subset_filter"],
        pop_thresholds=parameters["pop_thresholds"],
        output_format=parameters["output_format"]
    )
