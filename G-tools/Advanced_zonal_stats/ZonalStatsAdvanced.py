import arcpy
import os


class Toolbox(object):
    def __init__(self):
        self.label = "Zonal_Stats_Advanced"
        self.alias = "RasterTools"
        self.tools = [RasterProcessing]


class RasterProcessing(object):
    def __init__(self):
        self.label = "Zonal_Stats_Advanced"
        self.description = "Processes a population raster by clipping it to an administrative boundary, calculates population totals using zonal statistics, and generates a feature layer with both raw and rounded population sums. The output includes a cleaned feature layer with Pop_sum (double) and Pop_sum_rounded (long) fields."
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input raster parameter
        input_raster = arcpy.Parameter(
            displayName="Input Population Raster",
            name="input_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )
        input_raster.description = "Raster file representing the population data to be processed."

        # Administrative boundary parameter
        admin_boundary = arcpy.Parameter(
            displayName="Administrative Boundary",
            name="admin_boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        admin_boundary.description = "Feature layer representing the administrative boundary used for clipping the raster."

        # Output geodatabase parameter (optional)
        output_gdb = arcpy.Parameter(
            displayName="Output Geodatabase",
            name="output_gdb",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
        )
        output_gdb.description = "Geodatabase where output files will be stored. If not provided, defaults to the input raster directory."
        output_gdb.filter.list = ["Local Database"]

        # Output prefix parameter (optional)
        output_prefix = arcpy.Parameter(
            displayName="Output Prefix",
            name="output_prefix",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        output_prefix.description = "Prefix to be added to all output files. If not provided, a shortened name of the input raster will be used."

        return [input_raster, admin_boundary, output_gdb, output_prefix]

    def execute(self, parameters, messages):
        try:
            # Retrieve parameter values
            input_raster = parameters[0].valueAsText
            admin_boundary = parameters[1].valueAsText
            output_gdb = parameters[2].valueAsText or os.path.dirname(
                input_raster)
            output_prefix = parameters[3].valueAsText or os.path.splitext(
                os.path.basename(input_raster))[0][:10] + "_PreEnum"

            # Get input raster name for field suffix
            raster_name = os.path.splitext(os.path.basename(input_raster))[0]
            # Clean the raster name to be a valid field name (remove special characters and spaces)
            # Limit to 10 chars for field name length restrictions
            field_suffix = ''.join(e for e in raster_name if e.isalnum())[:10]

            # Set workspace environment
            arcpy.env.workspace = output_gdb
            arcpy.env.overwriteOutput = True

            # Create a temporary copy of the administrative boundary
            messages.addMessage(
                "\nCreating a temporary copy of the administrative boundary...")
            temp_admin_boundary = os.path.join(
                output_gdb, f"{output_prefix}_TempBoundary")
            arcpy.management.CopyFeatures(admin_boundary, temp_admin_boundary)

            # Step 1: Clip raster to administrative boundary
            messages.addMessage(
                "\nClipping raster to administrative boundary...")
            clipped_raster = os.path.join(
                output_gdb, f"{output_prefix}_Clipped")
            arcpy.management.Clip(
                in_raster=input_raster,
                rectangle="#",
                out_raster=clipped_raster,
                in_template_dataset=temp_admin_boundary,
                nodata_value="0",
                clipping_geometry="ClippingGeometry",
                maintain_clipping_extent="NO_MAINTAIN_EXTENT"
            )

            # Step 2: Calculate zonal statistics
            messages.addMessage("\nCalculating Zonal Statistics...")
            zonal_stats_name = f"{output_prefix}_ZonalStats"
            zonal_stats_output = os.path.join(output_gdb, zonal_stats_name)

            # Create unique ID field if it doesn't exist
            if not arcpy.ListFields(temp_admin_boundary, "UNIQUE_ID"):
                arcpy.management.AddField(
                    in_table=temp_admin_boundary,
                    field_name="UNIQUE_ID",
                    field_type="LONG",
                    field_precision=0,
                    field_scale=0
                )
                arcpy.management.CalculateField(
                    in_table=temp_admin_boundary,
                    field="UNIQUE_ID",
                    expression="!OBJECTID!",
                    expression_type="PYTHON3"
                )

            # Calculate zonal statistics
            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data=temp_admin_boundary,
                zone_field="UNIQUE_ID",
                in_value_raster=clipped_raster,
                out_table=zonal_stats_output,
                statistics_type="SUM",
                ignore_nodata="DATA"
            )

            # Step 3: Join statistics and create final output
            messages.addMessage(
                "\nJoining statistics and creating final output...")
            final_output = os.path.join(output_gdb, f"{output_prefix}_Final")
            arcpy.management.CopyFeatures(temp_admin_boundary, final_output)

            arcpy.management.JoinField(
                in_data=final_output,
                in_field="UNIQUE_ID",
                join_table=zonal_stats_output,
                join_field="UNIQUE_ID",
                fields=["SUM"]
            )

            # Add and calculate population fields with custom suffix
            pop_sum_field = f"Pop_sum_{field_suffix}"
            pop_sum_rounded_field = f"Pop_sum_rounded_{field_suffix}"

            # Add Pop_sum field with suffix
            arcpy.management.AddField(
                in_table=final_output,
                field_name=pop_sum_field,
                field_type="DOUBLE"
            )

            arcpy.management.CalculateField(
                in_table=final_output,
                field=pop_sum_field,
                expression="!SUM! if !SUM! is not None else 0",
                expression_type="PYTHON3"
            )

            # Clean up intermediate fields
            arcpy.management.DeleteField(
                in_table=final_output,
                drop_field=["SUM", "UNIQUE_ID"]
            )

            # Create final cleaned output
            cleaned_output = os.path.join(
                output_gdb, f"{output_prefix}_Final_Cleaned")
            arcpy.management.CopyFeatures(final_output, cleaned_output)

            # Verify the cleaned output exists
            if not arcpy.Exists(cleaned_output):
                messages.addWarningMessage(
                    f"Failed to create final output: {cleaned_output}")
            else:
                # Add and calculate rounded population field with suffix
                arcpy.management.AddField(
                    in_table=cleaned_output,
                    field_name=pop_sum_rounded_field,
                    field_type="LONG"
                )

                arcpy.management.CalculateField(
                    in_table=cleaned_output,
                    field=pop_sum_rounded_field,
                    expression=f"round(!{pop_sum_field}!)",
                    expression_type="PYTHON3"
                )

                # Add results to map
                self.add_to_map(
                    cleaned_output, f"{output_prefix}_Final_Cleaned", messages)

            # Clean up temporary files
            arcpy.management.Delete(temp_admin_boundary)

            messages.addMessage("Processing completed successfully!")
            messages.addMessage(
                f"Created fields: {pop_sum_field} and {pop_sum_rounded_field}")

            return

        except arcpy.ExecuteError:
            messages.addError(arcpy.GetMessages(2))
            raise
        except Exception as e:
            messages.addError(str(e))
            raise

    def add_to_map(self, layer_path, layer_name, messages):
        """
        Enhanced method to add layer to ArcGIS Pro map with better error handling and credentials management

        Parameters:
        layer_path (str): Path to the layer file
        layer_name (str): Name to display in the map
        messages: ArcGIS messages object for logging
        """
        try:
            # Verify layer path exists
            if not arcpy.Exists(layer_path):
                messages.addWarningMessage(
                    f"Layer {layer_path} does not exist. Cannot add to map.")
                return False

            # Get the current project and active map
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
            except Exception as e:
                messages.addWarningMessage(
                    f"Could not access current project: {str(e)}")
                return False

            # Get the active map view
            try:
                map_view = aprx.activeMap
                if not map_view:
                    # If no active map, try to get the first map
                    maps = aprx.listMaps()
                    if maps:
                        map_view = maps[0]
                        messages.addMessage(
                            "No active map found. Using first available map.")
                    else:
                        messages.addWarningMessage(
                            "No maps found in the project.")
                        return False
            except Exception as e:
                messages.addWarningMessage(
                    f"Error accessing map view: {str(e)}")
                return False

            # Try to add the layer with credential handling
            try:
                # Remove existing layer with same name if it exists
                for lyr in map_view.listLayers(layer_name):
                    map_view.removeLayer(lyr)
                    messages.addMessage(
                        f"Removed existing layer named {layer_name}")

                # Add the new layer
                added_layer = map_view.addDataFromPath(layer_path)

                if added_layer:
                    # Rename the layer if needed
                    if added_layer.name != layer_name:
                        added_layer.name = layer_name

                    # Move the layer to the top of the TOC
                    map_view.moveLayer(added_layer, None, "TOP")

                    messages.addMessage(
                        f"Successfully added and configured {layer_name} to the map")
                    return True
                else:
                    # Try alternative method if first attempt fails
                    result = arcpy.mp.LayerFile(layer_path)
                    map_view.addLayer(result)
                    messages.addMessage(
                        f"Added {layer_name} to map using alternative method")
                    return True

            except Exception as e:
                # Try one final method - using MakeFeatureLayer
                try:
                    arcpy.management.MakeFeatureLayer(layer_path, layer_name)
                    temp_layer = arcpy.management.SaveToLayerFile(layer_name,
                                                                  os.path.join(arcpy.env.scratchFolder, f"{layer_name}.lyrx"))
                    map_view.addDataFromPath(temp_layer.getOutput(0))
                    messages.addMessage(
                        f"Successfully added {layer_name} using feature layer method")
                    return True
                except Exception as nested_e:
                    messages.addWarningMessage(
                        f"All attempts to add layer failed. Final error: {str(nested_e)}")
                    return False

        except Exception as e:
            messages.addWarningMessage(
                f"Unexpected error while adding layer to map: {str(e)}")
            return False
