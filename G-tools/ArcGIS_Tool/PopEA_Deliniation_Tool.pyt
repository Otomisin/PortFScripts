import arcpy
import os


class Toolbox(object):
    def __init__(self):
        self.label = "PopEA Delineation Tool"
        self.alias = "RasterTools"
        self.tools = [RasterProcessing]


class RasterProcessing(object):
    def __init__(self):
        self.label = "PopEA Delineation Tool"
        self.description = "Process population raster data through binary conversion, polygon creation, bounding geometry, aggregation, and zonal statistics calculation."
        self.canRunInBackground = False

    def getParameterInfo(self):
        input_raster = arcpy.Parameter(
            displayName="Input Population Raster",
            name="input_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        admin_boundary = arcpy.Parameter(
            displayName="Administrative Boundary",
            name="admin_boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )

        output_gdb = arcpy.Parameter(
            displayName="Output Geodatabase (optional)",
            name="output_gdb",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
        )
        output_gdb.filter.list = ["Local Database"]

        output_prefix = arcpy.Parameter(
            displayName="Output Name Prefix (optional)",
            name="output_prefix",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )

        simplify = arcpy.Parameter(
            displayName="Simplify Polygons",
            name="simplify",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )
        simplify.value = True

        max_vertices = arcpy.Parameter(
            displayName="Maximum Vertices per Feature",
            name="max_vertices",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        )

        first_agg_distance = arcpy.Parameter(
            displayName="First Aggregation Distance",
            name="first_agg_distance",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        first_agg_distance.value = "100 Meters"

        second_agg_distance = arcpy.Parameter(
            displayName="Second Aggregation Distance",
            name="second_agg_distance",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        second_agg_distance.value = "10 Meters"

        filter_value = arcpy.Parameter(
            displayName="Threshold Definition",
            name="filter_value",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
        )
        filter_value.value = 650

        filter_threshold = arcpy.Parameter(
            displayName="Filter Population Threshold",
            name="filter_threshold",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
        )
        # filter_threshold.filter.list = ["None", "1", "0"]
        filter_threshold.filter.list = [
            "None", "Above Threshold (1)", "Below Threshold (0)"]
        filter_threshold.value = "None"
        filter_threshold.description = "Choose whether to filter polygons based on population threshold: 'Above Threshold' keeps polygons with population above the threshold value, 'Below Threshold' keeps polygons below it, and 'None' keeps all polygons."

        subadmin_boundary = arcpy.Parameter(
            displayName="Subadministrative Boundary",
            name="subadmin_boundary",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input"
        )

        # Update parameters list to include new parameter
        return [input_raster, admin_boundary, subadmin_boundary, output_gdb, output_prefix,
                simplify, max_vertices, first_agg_distance, second_agg_distance,
                filter_value, filter_threshold]

    def execute(self, parameters, messages):
        input_raster = parameters[0].valueAsText
        admin_boundary = parameters[1].valueAsText
        subadmin_boundary = parameters[2].valueAsText  # Corrected order
        output_gdb = parameters[3].valueAsText or arcpy.env.workspace
        output_prefix = parameters[4].valueAsText or os.path.splitext(
            os.path.basename(input_raster))[0] + "_PreEnum"
        simplify = parameters[5].value
        max_vertices = parameters[6].value
        first_agg_distance = parameters[7].valueAsText
        second_agg_distance = parameters[8].valueAsText
        filter_value = parameters[9].value
        filter_threshold = parameters[10].value

        if not output_gdb:
            messages.addError(
                "No valid output workspace specified or found in current environment")
            return

        arcpy.env.workspace = output_gdb
        arcpy.env.overwriteOutput = True

        try:
            arcpy.CheckOutExtension("Spatial")

            # Check for active map at the start
            has_active_map = False
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                if aprx.activeMap:
                    has_active_map = True
                else:
                    messages.addWarningMessage(
                        "No active map found - layers will be created but not added to display")
            except Exception:
                messages.addWarningMessage(
                    "Could not access map document - layers will be created but not added to display")

            arcpy.CheckOutExtension("Spatial")

            # Step 1: Clip raster to admin boundary
            clipped_name = f"{output_prefix}_clipped"
            clipped_raster = os.path.join(output_gdb, clipped_name)
            arcpy.management.Clip(
                in_raster=input_raster,
                rectangle="#",
                out_raster=clipped_raster,
                in_template_dataset=admin_boundary,
                nodata_value="#",
                clipping_geometry="ClippingGeometry"
            )

            # Step 2: Create binary raster
            binary_name = f"{output_prefix}_binary"
            binary_raster = arcpy.sa.Con(
                arcpy.sa.Raster(clipped_raster) > 0,
                1,
                0
            )
            binary_raster.save(os.path.join(output_gdb, binary_name))

            # Step 3: Convert raster to polygon
            polygon_name = f"{output_prefix}_polygon"
            out_polygons = os.path.join(output_gdb, polygon_name)
            arcpy.conversion.RasterToPolygon(
                in_raster=os.path.join(output_gdb, binary_name),
                out_polygon_features=out_polygons,
                simplify="SIMPLIFY" if simplify else "NO_SIMPLIFY",
                raster_field="Value",
                create_multipart_features="SINGLE_OUTER_PART",
                max_vertices_per_feature=max_vertices
            )

            # Step 4: Perform Minimum Bounding Geometry (MB1)
            mb1_name = f"{output_prefix}_MB1"
            mb1_output = os.path.join(output_gdb, mb1_name)
            arcpy.management.MinimumBoundingGeometry(
                in_features=out_polygons,
                out_feature_class=mb1_output,
                geometry_type="CONVEX_HULL",
                group_option="NONE"
            )

            # Step 5: Aggregate polygons (Agg1)
            agg1_name = f"{output_prefix}_MB1_Agg1"
            agg1_output = os.path.join(output_gdb, agg1_name)
            arcpy.cartography.AggregatePolygons(
                in_features=mb1_output,
                out_feature_class=agg1_output,
                aggregation_distance=first_agg_distance,
                minimum_area="0 SquareMeters",
                minimum_hole_size="0 SquareMeters",
                orthogonality_option="NON_ORTHOGONAL"
            )

            # Step 6: Perform Minimum Bounding Geometry again (MB2)
            mb2_name = f"{output_prefix}_MB2"
            mb2_output = os.path.join(output_gdb, mb2_name)
            arcpy.management.MinimumBoundingGeometry(
                in_features=agg1_output,
                out_feature_class=mb2_output,
                geometry_type="CONVEX_HULL",
                group_option="NONE"
            )

            # Step 7: Aggregate polygons again (Agg2)
            agg2_name = f"{output_prefix}_MB2_Agg2"
            agg2_output = os.path.join(output_gdb, agg2_name)
            arcpy.cartography.AggregatePolygons(
                in_features=mb2_output,
                out_feature_class=agg2_output,
                aggregation_distance=second_agg_distance,
                minimum_area="0 SquareMeters",
                minimum_hole_size="0 SquareMeters",
                orthogonality_option="NON_ORTHOGONAL"
            )

            # Step 8: Calculate Zonal Population Statistics
            zonal_stats_name = f"{output_prefix}_ZonalStats"
            zonal_stats_output = os.path.join(output_gdb, zonal_stats_name)

            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data=agg2_output,
                zone_field="OBJECTID",
                in_value_raster=clipped_raster,
                out_table=zonal_stats_output,
                statistics_type="SUM",
                ignore_nodata="DATA"
            )

            # Step 9: Append ZonalStats to Agg2 polygons with a new name
            agg2_zstats_name = f"{output_prefix}_MB2_Agg2_{filter_value}"
            agg2_zstats_output = os.path.join(output_gdb, agg2_zstats_name)
            arcpy.management.CopyFeatures(agg2_output, agg2_zstats_output)
            arcpy.management.JoinField(
                in_data=agg2_zstats_output,
                in_field="OBJECTID",
                join_table=zonal_stats_output,
                join_field="OBJECTID",
                fields=["SUM"]
            )

            # Step 10: Add Binary column based on filter_value
            binary_column = f"threshfig_{filter_value}"
            arcpy.management.AddField(
                in_table=agg2_zstats_output,
                field_name=binary_column,
                field_type="SHORT"
            )

            arcpy.management.CalculateField(
                in_table=agg2_zstats_output,
                field=binary_column,
                expression=f"1 if !SUM! > {filter_value} else 0",
                expression_type="PYTHON3"
            )

            # Step 11: Filter based on Binary column (if specified)
            filtered_output = agg2_zstats_output  # Default to unfiltered output
            if filter_threshold != "None":
                filtered_output_name = f"{agg2_zstats_name}_filtered"
                filtered_output = os.path.join(
                    output_gdb, filtered_output_name)

                # Create a feature layer first
                temp_layer = "temp_filter_layer"
                arcpy.management.MakeFeatureLayer(
                    in_features=agg2_zstats_output,
                    out_layer=temp_layer
                )

                # Apply the selection on the layer
                actual_threshold = "1" if "Above" in filter_threshold else "0"
                arcpy.management.SelectLayerByAttribute(
                    in_layer_or_view=temp_layer,
                    selection_type="NEW_SELECTION",
                    where_clause=f"{binary_column} = {actual_threshold}"
                )

                # Copy the selected features to the new output
                arcpy.management.CopyFeatures(
                    in_features=temp_layer,
                    out_feature_class=filtered_output
                )

                # Clean up the temporary layer
                arcpy.management.Delete(temp_layer)

                self.add_to_map(filtered_output,
                                filtered_output_name, messages)

            # After binary filtering, add new Euclidean Allocation step
            messages.addMessage("\nPerforming Euclidean Allocation...")
            euc_allo_name = f"{output_prefix}_EucAllo"
            euc_allo_output = os.path.join(output_gdb, euc_allo_name)

            # Get the filtered output name from the previous step
            filtered_name = f"{output_prefix}_MB2_Agg2_{filter_value}_filtered"
            filtered_output = os.path.join(output_gdb, filtered_name)

            # Perform Euclidean Allocation
            out_allocation_raster = arcpy.sa.EucAllocation(
                in_source_data=filtered_output,
                maximum_distance=None,
                in_value_raster=None,
                cell_size=input_raster,
                source_field="OBJECTID",
                out_distance_raster=None,
                out_direction_raster=None,
                distance_method="PLANAR",
                in_barrier_data=None,
                out_back_direction_raster=None
            )
            out_allocation_raster.save(euc_allo_output)

            # Clip the Euclidean Allocation raster
            messages.addMessage("\nClipping Euclidean Allocation raster...")
            euc_allo_clip_name = f"{euc_allo_name}_Clip"
            euc_allo_clip_output = os.path.join(output_gdb, euc_allo_clip_name)

            arcpy.management.Clip(
                in_raster=euc_allo_output,
                rectangle="#",  # Using the extent of the admin boundary
                out_raster=euc_allo_clip_output,
                in_template_dataset=admin_boundary,
                nodata_value="-1",
                clipping_geometry="ClippingGeometry",
                maintain_clipping_extent="MAINTAIN_EXTENT"
            )

            # Step 12: Convert Euclidean Allocation raster to polygon
            messages.addMessage(
                "\nConverting Euclidean Allocation raster to polygon...")
            raster_poly_name = f"{output_prefix}_EucAllo_Poly"
            raster_poly_output = os.path.join(output_gdb, raster_poly_name)

            arcpy.conversion.RasterToPolygon(
                in_raster=euc_allo_clip_output,
                out_polygon_features=raster_poly_output,
                simplify="SIMPLIFY",
                raster_field="Value",
                create_multipart_features="SINGLE_OUTER_PART",
                max_vertices_per_feature=None
            )

            # Step 13: Union with Subadmin boundary
            if subadmin_boundary:
                messages.addMessage(
                    "\nPerforming Union with Subadmin boundary...")
                union_name = f"{output_prefix}_EucAllo_Union"
                union_output = os.path.join(output_gdb, union_name)

                arcpy.analysis.Union(
                    in_features=[raster_poly_output, subadmin_boundary],
                    out_feature_class=union_output,
                    join_attributes="ALL",
                    cluster_tolerance=None,
                    gaps="NO_GAPS"
                )
                base_features_for_singlepart = union_output
            else:
                messages.addMessage(
                    "\nSkipping Union step (no subadmin boundary provided)...")
                base_features_for_singlepart = raster_poly_output

            # Step 14: Convert multipart to singlepart
            messages.addMessage("\nConverting multipart to singlepart...")
            singlepart_name = f"{output_prefix}_EucAllo_Single"
            singlepart_output = os.path.join(output_gdb, singlepart_name)

            arcpy.management.MultipartToSinglepart(
                in_features=base_features_for_singlepart,
                out_feature_class=singlepart_output
            )

            # Step 15: Calculate final Zonal Statistics
            messages.addMessage("\nCalculating final Zonal Statistics...")
            final_zonal_stats_name = f"{output_prefix}_Final_ZonalStats"
            final_zonal_stats_output = os.path.join(
                output_gdb, final_zonal_stats_name)

            arcpy.sa.ZonalStatisticsAsTable(
                in_zone_data=singlepart_output,
                zone_field="OBJECTID",
                in_value_raster=clipped_raster,
                out_table=final_zonal_stats_output,
                statistics_type="SUM",
                ignore_nodata="DATA"
            )

            # Create a copy of singlepart features for the final output
            # Changed name to be more descriptive
            final_output_name = f"{output_prefix}_Final_Output_WithStats"
            final_output = os.path.join(output_gdb, final_output_name)
            arcpy.management.CopyFeatures(singlepart_output, final_output)

            # Join the final zonal statistics to the final output
            arcpy.management.JoinField(
                in_data=final_output,
                in_field="OBJECTID",
                join_table=final_zonal_stats_output,
                join_field="OBJECTID",
                fields=["SUM"]
            )

            # Add field to store population values more clearly
            arcpy.management.AddField(
                in_table=final_output,
                field_name="Population",
                field_type="DOUBLE"
            )

            # Calculate the population field
            arcpy.management.CalculateField(
                in_table=final_output,
                field="Population",
                expression="!SUM!",
                expression_type="PYTHON3"
            )

            #################################################
            # ADDING LAYERS TO MAP ##########################
            #################################################

            # # Add the final output to the map
            # self.add_to_map(final_output, final_output_name, messages)

            # # Add outputs to the current map
            # # Add outputs to the current map in order of operations
            # # Step 1: Clipped raster
            # self.add_to_map(clipped_raster, clipped_name, messages)

            # # Step 2: Binary raster
            # self.add_to_map(os.path.join(
            #     output_gdb, binary_name), binary_name, messages)

            # # Step 3: Initial polygon conversion
            # self.add_to_map(out_polygons, polygon_name, messages)

            # # Step 4-7: Bounding geometry and aggregation steps
            # self.add_to_map(mb1_output, mb1_name, messages)
            # self.add_to_map(agg1_output, agg1_name, messages)
            # self.add_to_map(mb2_output, mb2_name, messages)
            # self.add_to_map(agg2_output, agg2_name, messages)

            # # Step 8-10: Initial zonal statistics and filtering
            # self.add_to_map(zonal_stats_output, zonal_stats_name, messages)
            # self.add_to_map(agg2_zstats_output, agg2_zstats_name, messages)

            # # Step 11-12: Euclidean allocation steps
            # self.add_to_map(euc_allo_output, euc_allo_name, messages)
            # self.add_to_map(euc_allo_clip_output, euc_allo_clip_name, messages)
            # self.add_to_map(raster_poly_output, raster_poly_name, messages)

            # # Step 13-14: Union and singlepart conversion
            # # self.add_to_map(union_output, union_name, messages)
            # if subadmin_boundary:
            #     self.add_to_map(union_output,
            #                     f"{output_prefix}_EucAllo_Union",
            #                     messages)
            # self.add_to_map(singlepart_output, singlepart_name, messages)

            # # Step 15: Final statistics and output
            # self.add_to_map(final_zonal_stats_output,
            #                 final_zonal_stats_name, messages)

            # # Final output with all statistics (always last)
            # self.add_to_map(final_output, final_output_name, messages)

            if has_active_map:
                messages.addMessage("\nAdding layers to map...")
            # Add all outputs to the map in order of operations
            # Step 1: Add clipped raster - Initial population raster clipped to admin boundary
            self.add_to_map(clipped_raster, clipped_name, messages)

            # Step 2: Add binary raster - Converted population values to 1/0 based on presence
            self.add_to_map(os.path.join(
                output_gdb, binary_name), binary_name, messages)

            # Step 3: Add initial polygon conversion - Binary raster converted to polygons
            self.add_to_map(out_polygons, polygon_name, messages)

            # Step 4: Add first minimum bounding geometry (MB1) - Convex hulls of initial polygons
            self.add_to_map(mb1_output, mb1_name, messages)

            # Step 5: Add first aggregation result (Agg1) - MB1 polygons aggregated at first distance
            self.add_to_map(agg1_output, agg1_name, messages)

            # Step 6: Add second minimum bounding geometry (MB2) - Convex hulls of first aggregation
            self.add_to_map(mb2_output, mb2_name, messages)

            # Step 7: Add second aggregation result (Agg2) - MB2 polygons aggregated at second distance
            self.add_to_map(agg2_output, agg2_name, messages)

            # Step 8: Add initial zonal statistics - Population statistics for aggregated polygons
            self.add_to_map(zonal_stats_output, zonal_stats_name, messages)

            # Step 9: Add polygons with population threshold calculations
            self.add_to_map(agg2_zstats_output, agg2_zstats_name, messages)

            # Step 10: Add Euclidean allocation raster - Shows areas of influence
            self.add_to_map(euc_allo_output, euc_allo_name, messages)

            # Step 11: Add clipped Euclidean allocation - Allocation confined to admin boundary
            self.add_to_map(euc_allo_clip_output, euc_allo_clip_name, messages)

            # Step 12: Add allocation polygons - Euclidean allocation converted to polygons
            self.add_to_map(raster_poly_output, raster_poly_name, messages)

            # Step 13: Add union result if subadmin boundary was provided
            if subadmin_boundary:
                self.add_to_map(union_output,
                                f"{output_prefix}_EucAllo_Union",
                                messages)

            # Step 14: Add final zonal statistics table
            self.add_to_map(final_zonal_stats_output,
                            final_zonal_stats_name, messages)

            # Step 15: Add final output with all statistics
            self.add_to_map(final_output, final_output_name, messages)

            # Add summary of created layers
            messages.addMessage("\nCreated layers:")
            messages.addMessage(f"- Clipped raster: {clipped_name}")
            messages.addMessage(f"- Binary raster: {binary_name}")
            messages.addMessage(f"- Initial polygons: {polygon_name}")
            messages.addMessage(
                f"- First minimum bounding geometry: {mb1_name}")
            messages.addMessage(f"- First aggregation: {agg1_name}")
            messages.addMessage(
                f"- Second minimum bounding geometry: {mb2_name}")
            messages.addMessage(f"- Second aggregation: {agg2_name}")
            messages.addMessage(
                f"- Initial zonal statistics: {zonal_stats_name}")
            messages.addMessage(f"- Filtered polygons: {agg2_zstats_name}")
            messages.addMessage(f"- Euclidean allocation: {euc_allo_name}")
            messages.addMessage(f"- Clipped allocation: {euc_allo_clip_name}")
            messages.addMessage(f"- Allocation polygons: {raster_poly_name}")
            if subadmin_boundary:
                messages.addMessage(
                    f"- Union result: {output_prefix}_EucAllo_Union")
            messages.addMessage(
                f"- Final zonal statistics: {final_zonal_stats_name}")
            messages.addMessage(f"- Final output: {final_output_name}")

            messages.addMessage("\nProcessing completed successfully!")

        except arcpy.ExecuteError as e:
            messages.addError(str(e))
            messages.addError(arcpy.GetMessages(2))
        except Exception as e:
            messages.addError(f"An error occurred: {str(e)}")
        finally:
            arcpy.CheckInExtension("Spatial")

    def add_to_map(self, layer_path, layer_name, messages):
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            active_map = aprx.activeMap
            if active_map:
                active_map.addDataFromPath(layer_path)
                messages.addMessage(f"Added {layer_name} to the map")
                return True
            return False
        except Exception as e:
            return False
