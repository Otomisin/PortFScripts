# utils.py

"""
Utilities, calculations, and data models for the sampling calculator.
"""
import pandas as pd
import numpy as np
import math
from scipy.stats import chi2
import io
import streamlit as st
from datetime import datetime, timedelta


def validate_file(uploaded_file):
    """Validate uploaded Excel file and return sheets."""
    try:
        xls = pd.ExcelFile(uploaded_file)
        return xls.sheet_names
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None


def load_master_data(uploaded_file, sheet_name):
    """Load and validate master data from Excel file."""
    try:
        df_master = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        return df_master
    except Exception as e:
        st.error(f"Error loading master data: {str(e)}")
        return None


def load_master_data_with_uid(uploaded_file, sheet_name):
    """
    Load master data from Excel file and add a unique ID column.

    Args:
        uploaded_file: The uploaded Excel file
        sheet_name: Name of the sheet to read

    Returns:
        pd.DataFrame: DataFrame with added UniqueID column
    """
    try:
        # Read the Excel file
        df_master = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        # Create and add UniqueID column
        # Format: UID_1, UID_2, etc.
        df_master['UniqueID'] = [f'UID_{i+1}' for i in range(len(df_master))]

        return df_master
    except Exception as e:
        st.error(f"Error loading master data: {str(e)}")
        return None


def calculate_sample(population, params):
    """Calculate sample size based on parameters."""
    try:
        chinv = chi2.ppf(params['confidence_level'], df=1)
        sample_size = math.ceil(
            (chinv * population * params['probability'] * (1 - params['probability'])) /
            (((params['margin_of_error'] ** 2) * (population - 1)) +
             (chinv * params['probability'] * (1 - params['probability']))) *
            params['design_effect']
        )
        return sample_size
    except Exception as e:
        st.error(f"Error calculating sample size: {str(e)}")
        return None


# def create_sample_data(df, col_config, sampling_params=None):
#     """
#     Create sample data from master list following the DTM Handbook methodology.
#     Each stratum gets its own sample size calculated independently.
#     """
#     try:
#         # Validate column existence
#         required_cols = ['households', 'admin3', 'strata']
#         for col_type in required_cols:
#             col_name = col_config['master_data'][col_type]
#             if col_name not in df.columns:
#                 st.error(
#                     f"Required column '{col_name}' not found in the dataframe")
#                 return None

#         # Make a copy to avoid modifying the original DataFrame
#         df_copy = df.copy()

#         # Get column names from config
#         admin_col = col_config['master_data']['admin3']
#         strata_col = col_config['master_data']['strata']
#         households_col = col_config['master_data']['households']

#         # Ensure household column contains numeric data
#         df_copy[households_col] = pd.to_numeric(
#             df_copy[households_col], errors='coerce')

#         # Check if conversion produced any NaN values
#         if df_copy[households_col].isna().any():
#             na_count = df_copy[households_col].isna().sum()
#             if na_count > 0:
#                 st.warning(
#                     f"Found {na_count} non-numeric values in '{households_col}' column. These have been treated as 0.")
#                 # Replace NaN with 0 to avoid breaking calculations
#                 df_copy[households_col].fillna(0, inplace=True)

#         # Create strata name combining strata and admin3
#         # Convert to string to handle non-string data types
#         df_copy['Strata_name'] = df_copy[strata_col].astype(
#             str) + '_' + df_copy[admin_col].astype(str)

#         # Group data by admin3, strata, and strata_name
#         sample_data = df_copy.groupby([
#             admin_col,
#             strata_col,
#             'Strata_name'
#         ]).agg({
#             households_col: 'sum'
#         }).reset_index()

#         # Rename columns for clarity
#         column_mapping = {
#             admin_col: 'Admin3',
#             strata_col: 'Stratum',
#             households_col: 'Population (HH)'
#         }
#         sample_data.rename(columns=column_mapping, inplace=True)

#         # Sort by admin3 and stratum for consistency
#         sample_data = sample_data.sort_values(['Admin3', 'Stratum'])

#         # MODIFIED: Calculate sample size for each stratum separately
#         if sampling_params is not None:
#             # Apply the DTM handbook methodology - calculate sample for each stratum
#             sample_data['Sample'] = sample_data['Population (HH)'].apply(
#                 lambda pop: calculate_sample(pop, sampling_params)
#             )

#             # Ensure at least 1 sample for each stratum with population > 0
#             sample_data.loc[(sample_data['Sample'] < 1) & (
#                 sample_data['Population (HH)'] > 0), 'Sample'] = 1

#             # Calculate sample with reserve
#             sample_data['Sample_with_reserve'] = sample_data['Sample'].apply(
#                 lambda x: math.ceil(
#                     x * (1 + sampling_params['reserve_percentage']))
#             )

#             # Calculate clusters
#             sample_data['Clusters visited'] = sample_data['Sample_with_reserve'].apply(
#                 lambda x: math.ceil(
#                     x / sampling_params['interviews_per_cluster'])
#             )

#         # Add debug information
#         st.session_state['debug_info'] = {
#             'original_columns': list(df.columns),
#             'column_config': col_config,
#             'sample_data_columns': list(sample_data.columns),
#             'sample_data_shape': sample_data.shape
#         }

#         return sample_data

#     except Exception as e:
#         st.error(f"Error creating sample data: {str(e)}")
#         st.exception(e)  # This will show the full traceback in development
#         return None

def create_sample_data(df, col_config, sampling_params=None):
    """
    Create sample data from master list with improved error handling.
    Modified to calculate separate sample sizes for each stratum.
    """
    try:
        # Validate column existence
        required_cols = ['households', 'admin3', 'strata']
        for col_type in required_cols:
            col_name = col_config['master_data'][col_type]
            if col_name not in df.columns:
                st.error(
                    f"Required column '{col_name}' not found in the dataframe")
                return None

        # Make a copy to avoid modifying the original DataFrame
        df_copy = df.copy()

        # Get column names from config
        admin_col = col_config['master_data']['admin3']
        strata_col = col_config['master_data']['strata']
        households_col = col_config['master_data']['households']

        # Ensure household column contains numeric data
        df_copy[households_col] = pd.to_numeric(
            df_copy[households_col], errors='coerce')

        # Check if conversion produced any NaN values
        if df_copy[households_col].isna().any():
            na_count = df_copy[households_col].isna().sum()
            if na_count > 0:
                st.warning(
                    f"Found {na_count} non-numeric values in '{households_col}' column. These have been treated as 0.")
                # Replace NaN with 0 to avoid breaking calculations
                df_copy[households_col].fillna(0, inplace=True)

        # Create strata name combining strata and admin3
        # Convert to string to handle non-string data types
        df_copy['Strata_name'] = df_copy[strata_col].astype(
            str) + '_' + df_copy[admin_col].astype(str)

        # Group data by admin3, strata, and strata_name
        # Use agg with named functions to be explicit
        sample_data = df_copy.groupby([
            admin_col,
            strata_col,
            'Strata_name'
        ]).agg({
            households_col: 'sum'
        }).reset_index()

        # Rename columns for clarity with a more explicit approach
        column_mapping = {
            strata_col: 'Stratum',
            households_col: 'Population (HH)'
        }
        sample_data.rename(columns=column_mapping, inplace=True)

        # Sort by admin3 and stratum for consistency
        sample_data = sample_data.sort_values([admin_col, 'Stratum'])

        # NEW CODE: Apply sample size calculation to each stratum individually
        if sampling_params is not None:
            # Apply the sample size formula separately to each stratum
            sample_data['Sample'] = sample_data.apply(
                lambda row: calculate_sample(
                    row['Population (HH)'], sampling_params),
                axis=1
            )

            # Ensure at least 1 sample for each stratum with population > 0
            sample_data.loc[(sample_data['Sample'] < 1) & (
                sample_data['Population (HH)'] > 0), 'Sample'] = 1

            # Calculate sample with reserve
            sample_data['Sample_with_reserve'] = sample_data['Sample'].apply(
                lambda x: math.ceil(
                    x * (1 + sampling_params['reserve_percentage']))
            )

            # Calculate clusters
            sample_data['Clusters visited'] = sample_data['Sample_with_reserve'].apply(
                lambda x: math.ceil(
                    x / sampling_params['interviews_per_cluster'])
            )

        # Add debug information
        st.session_state['debug_info'] = {
            'original_columns': list(df.columns),
            'column_config': col_config,
            'sample_data_columns': list(sample_data.columns),
            'sample_data_shape': sample_data.shape
        }

        return sample_data

    except Exception as e:
        st.error(f"Error creating sample data: {str(e)}")
        st.exception(e)  # This will show the full traceback in development
        return None


def process_sampling_batch(df, sample_data, params, col_config):
    """
    Process sampling logic for a single batch (primary or replacement).
    Ensures UniqueID is preserved throughout the process.
    Also applies capacity constraints if enabled.
    """
    result = []
    dynamic_target_col = f"Interview_TARGET_{col_config['master_data']['households']}"

    try:
        # Set random seed if provided
        if 'random_seed' in params and params['random_seed'] is not None:
            np.random.seed(params['random_seed'])

        # Make a copy to avoid modifying the original
        df_copy = df.copy()

        # Get column names from config
        admin_col = col_config['master_data']['admin3']
        strata_col = col_config['master_data']['strata']
        households_col = col_config['master_data']['households']
        site_id_col = col_config['master_data']['site_id']
        # Add site name column
        site_name_col = col_config['master_data']['site_name']

        # Ensure households column is numeric
        df_copy[households_col] = pd.to_numeric(
            df_copy[households_col], errors='coerce')
        df_copy[households_col].fillna(0, inplace=True)

        # Check if UniqueID exists and add debugging info
        has_uniqueid = 'UniqueID' in df_copy.columns
        if has_uniqueid:
            st.session_state.setdefault('debug_uniqueid_processing', {}).update({
                'uniqueid_present_in_input': True,
                'unique_count': df_copy['UniqueID'].nunique(),
                'sample': df_copy['UniqueID'].head(5).tolist()
            })
        else:
            st.session_state.setdefault('debug_uniqueid_processing', {}).update({
                'uniqueid_present_in_input': False
            })

        # Make sure we have the required columns in df_copy
        for col in [admin_col, strata_col, households_col, site_id_col]:
            if col not in df_copy.columns:
                st.error(f"Required column '{col}' not found in input data.")
                return pd.DataFrame()

        # Make sure we have the required columns in sample_data
        # Make sure we have the required columns in sample_data
        # Make sure we have the required columns in sample_data
        required_sample_cols = ['Stratum', 'Sample_with_reserve']
        # Add the actual admin column name instead of hardcoded 'Admin3'
        if col_config and 'master_data' in col_config:
            admin_col_name = col_config['master_data']['admin3']
            required_sample_cols.append(admin_col_name)

        for col in required_sample_cols:
            if col not in sample_data.columns:
                st.error(f"Required column '{col}' not found in sample data.")
                return pd.DataFrame()

        # Group by both admin3 and strata
        for _, strata_row in sample_data.iterrows():
            # Get the admin and stratum values from the sample data
            admin_col_name = col_config['master_data']['admin3']
            admin_value = strata_row[admin_col_name]
            stratum_value = strata_row['Stratum']

            # Add debug information
            st.session_state.setdefault('debug_samples', []).append({
                'admin': admin_value,
                'stratum': stratum_value
            })

            filtered_df = df_copy[
                (df_copy[admin_col].astype(str) == str(admin_value)) &
                (df_copy[strata_col].astype(str) == str(stratum_value))
            ].copy()

            if filtered_df.empty:
                # Check if we're generating replacements
                if 'replacement_debug' in st.session_state:
                    # This is for replacement PSUs - suppress individual warnings
                    # Add to a tracking variable to summarize replacement issues later
                    if 'replacement_issues' not in st.session_state:
                        st.session_state['replacement_issues'] = []

                    st.session_state['replacement_issues'].append({
                        'admin': admin_value,
                        'stratum': stratum_value,
                        'issue': 'no_available_psus'
                    })
                else:
                    # This is for primary PSUs
                    st.warning(
                        f"No data found for cluster '{admin_value}' and stratum '{stratum_value}'. Skipping..."
                    )
                continue

            # In the process_sampling_batch function in utils.py

            # Check if UniqueID is preserved in filtered data
            if has_uniqueid:
                st.session_state['debug_uniqueid_processing'].update({
                    'uniqueid_in_filtered': 'UniqueID' in filtered_df.columns,
                    'filtered_sample': filtered_df['UniqueID'].head(3).tolist() if 'UniqueID' in filtered_df.columns else []
                })

            # Calculate cumulative households within the stratum
            # Sort to ensure consistent results but preserve UniqueID
            filtered_df = filtered_df.sort_values(
                households_col, ascending=False)
            filtered_df['Cumulative_HH'] = filtered_df[households_col].cumsum()
            filtered_df['Lower_bound'] = filtered_df['Cumulative_HH'] - \
                filtered_df[households_col] + 1
            filtered_df['Selections'] = 0

            # Calculate number of draws needed for this stratum
            sample_size = float(strata_row['Sample_with_reserve'])
            num_draws = int(math.ceil(
                sample_size / params['interviews_per_cluster']
            ))

            try:
                # Generate random numbers within stratum bounds
                lower_bound = max(1, int(filtered_df['Lower_bound'].min()))
                upper_bound = max(
                    lower_bound + 1, int(filtered_df['Cumulative_HH'].max() + 1))

                if lower_bound >= upper_bound:
                    st.warning(
                        f"Invalid bounds for stratum '{stratum_value}' in cluster '{admin_value}'. Using default selection."
                    )
                    # Just select the first row as a fallback
                    filtered_df.iloc[0, filtered_df.columns.get_loc(
                        'Selections')] = num_draws
                else:
                    # Generate the random samples
                    random_numbers = np.random.randint(
                        lower_bound,
                        upper_bound,
                        size=num_draws
                    )

                    # Apply selections based on random numbers
                    for rand in random_numbers:
                        filtered_df.loc[
                            (filtered_df['Lower_bound'] <= rand) &
                            (filtered_df['Cumulative_HH'] >= rand),
                            'Selections'
                        ] += 1

                # Calculate interview targets
                filtered_df[dynamic_target_col] = filtered_df['Selections'] * \
                    params['interviews_per_cluster']

                # Add strata information to output
                filtered_df['Stratum'] = stratum_value
                filtered_df['Strata_name'] = strata_row['Strata_name']
                # Ensure Admin3 is included
                filtered_df['Admin3'] = admin_value

                # Add the site name if not already present
                if site_name_col in df_copy.columns and site_name_col not in filtered_df.columns:
                    # Create a mapping from site_id to site_name
                    site_name_mapping = df_copy.set_index(
                        site_id_col)[site_name_col].to_dict()
                    filtered_df[site_name_col] = filtered_df[site_id_col].map(
                        site_name_mapping)

                # Make sure our filtered result has UniqueID if original had it
                if has_uniqueid and 'UniqueID' not in filtered_df.columns:
                    st.warning(
                        f"UniqueID column was lost during processing for stratum {stratum_value}")

                result.append(filtered_df)

            except ValueError as e:
                st.error(
                    f"Error generating random numbers for stratum '{stratum_value}' in cluster '{admin_value}': {str(e)}"
                )
                st.exception(e)
                continue
            except Exception as e:
                st.error(f"Unexpected error during sampling: {str(e)}")
                st.exception(e)
                continue

        # Combine all results
        if not result:
            st.error(
                "No samples could be generated. Please check your data and configuration.")
            return pd.DataFrame()

        final_df = pd.concat(result, ignore_index=True)

        # Add summary columns
        if not final_df.empty:
            final_df['Total_Selected'] = final_df['Selections'].sum()
            final_df['Stratum_Selected'] = final_df.groupby(
                'Stratum')['Selections'].transform('sum')

            # Check if UniqueID made it to the final dataframe
            if has_uniqueid:
                st.session_state['debug_uniqueid_processing'].update({
                    'uniqueid_in_final': 'UniqueID' in final_df.columns,
                    'final_sample': final_df['UniqueID'].head(3).tolist() if 'UniqueID' in final_df.columns else []
                })

        return final_df

    except Exception as e:
        st.error(f"Error processing sampling: {str(e)}")
        st.exception(e)
        return pd.DataFrame()


def process_sampling(df, sample_data, params, col_config):
    """
    Process sampling in two rounds - primary PSUs and replacements.

    Args:
        df (pd.DataFrame): Input master data
        sample_data (pd.DataFrame): Processed sample data with strata
        params (dict): Sampling parameters
        col_config (dict): Column configuration

    Returns:
        pd.DataFrame: Combined data with both primary and replacement PSUs
    """
    # First round - primary PSUs
    primary_sampled_data = process_sampling_batch(
        df, sample_data, params, col_config)

    # Mark the type of each PSU (we need to do this before checking if replacements are needed)
    if not primary_sampled_data.empty:
        primary_sampled_data['PSU_Type'] = 'Primary'

    # If replacements aren't needed, return just the primary data
    if not params.get('use_replacement_psus', False):
        return primary_sampled_data

    # Calculate how many replacement PSUs we need
    # Based on the number of selected primary PSUs
    selected_primary = primary_sampled_data[primary_sampled_data['Selections'] > 0]
    total_primary_selected = selected_primary.shape[0]
    replacement_count = math.ceil(
        total_primary_selected * params['replacement_percentage'])

    # Add debug information for troubleshooting
    st.session_state.setdefault('replacement_debug', {}).update({
        'total_primary_selected': total_primary_selected,
        'replacement_percentage': params['replacement_percentage'],
        'calculated_replacement_count': replacement_count
    })

    # Create a copy of the original dataframe for the second round
    df_for_replacement = df.copy()

    # Remove already selected PSUs
    selected_ids = set(
        selected_primary[col_config['master_data']['site_id']].unique())
    df_for_replacement = df_for_replacement[
        ~df_for_replacement[col_config['master_data']
                            ['site_id']].isin(selected_ids)
    ]

    # Track which strata have limited available PSUs for replacements
    available_psu_counts = {}
    if not df_for_replacement.empty:
        # Count available PSUs by admin and stratum
        admin_col = col_config['master_data']['admin3']
        strata_col = col_config['master_data']['strata']

        for (admin, stratum), group in df_for_replacement.groupby([admin_col, strata_col]):
            available_psu_counts[(admin, stratum)] = len(group)

        # Compare with sample_data to identify potential issues
        # Compare with sample_data to identify potential issues
        for _, row in sample_data.iterrows():
            admin_col_name = col_config['master_data']['admin3']
            admin = row[admin_col_name]
            stratum = row['Stratum']
            required_replacements = math.ceil(
                row['Clusters visited'] * params['replacement_percentage'])

            if (admin, stratum) in available_psu_counts:
                if available_psu_counts[(admin, stratum)] < required_replacements:
                    # Add to replacement issues
                    if 'replacement_issues' not in st.session_state:
                        st.session_state['replacement_issues'] = []

                    st.session_state['replacement_issues'].append({
                        'admin': admin,
                        'stratum': stratum,
                        'issue': 'insufficient_psus',
                        'available': available_psu_counts[(admin, stratum)],
                        'required': required_replacements
                    })
            else:
                # No PSUs available at all for this combination
                if 'replacement_issues' not in st.session_state:
                    st.session_state['replacement_issues'] = []

                st.session_state['replacement_issues'].append({
                    'admin': admin,
                    'stratum': stratum,
                    'issue': 'no_available_psus'
                })

    # Add debug info about available PSUs for replacement
    st.session_state['replacement_debug'].update({
        'selected_ids_count': len(selected_ids),
        'remaining_psus_for_replacement': len(df_for_replacement),
        'available_psu_counts': available_psu_counts
    })

    # Adjust parameters for the replacement round
    # We want fewer PSUs while maintaining the same methodology
    replacement_params = params.copy()

    # Modify the replacement sample_data to target specific replacement counts
    replacement_sample_data = sample_data.copy()

    # Adjust the Sample_with_reserve to target the right number of replacements
    # We maintain the same proportions across strata
    if not replacement_sample_data.empty:
        # Calculate the total original sample size
        original_total = replacement_sample_data['Sample_with_reserve'].sum()

        # Calculate a scaling factor to adjust to the desired replacement count
        if original_total > 0:
            target_interviews = replacement_count * \
                params['interviews_per_cluster']
            scaling_factor = target_interviews / original_total

            # Apply scaling to each stratum
            replacement_sample_data['Sample_with_reserve'] = (
                replacement_sample_data['Sample_with_reserve'] * scaling_factor
                # Ensure at least 1 per stratum
            ).apply(lambda x: max(math.ceil(x), 1))

            # Also update the Sample column to maintain consistency
            replacement_sample_data['Sample'] = (
                replacement_sample_data['Sample'] * scaling_factor
            ).apply(lambda x: max(math.ceil(x), 1))

            # Update Clusters visited
            replacement_sample_data['Clusters visited'] = replacement_sample_data['Sample_with_reserve'].apply(
                lambda x: math.ceil(x / params['interviews_per_cluster'])
            )

            # Add this to debug info
            st.session_state['replacement_debug'].update({
                'scaling_factor': scaling_factor,
                'target_interviews': target_interviews,
                'adjusted_sample_size': replacement_sample_data['Sample_with_reserve'].sum(),
                'estimated_clusters': replacement_sample_data['Clusters visited'].sum()
            })

    # Second round - replacement PSUs
    replacement_sampled_data = process_sampling_batch(
        df_for_replacement, replacement_sample_data, replacement_params, col_config)

    # Mark the type of each PSU
    if not replacement_sampled_data.empty:
        replacement_sampled_data['PSU_Type'] = 'Replacement'

    # Add debug info about results
    st.session_state['replacement_debug'].update({
        'primary_sampled_data_shape': primary_sampled_data.shape if not primary_sampled_data.empty else None,
        'replacement_sampled_data_shape': replacement_sampled_data.shape if not replacement_sampled_data.empty else None,
        'primary_selections': primary_sampled_data['Selections'].sum() if not primary_sampled_data.empty else 0,
        'replacement_selections': replacement_sampled_data['Selections'].sum() if not replacement_sampled_data.empty else 0,
    })

    # Combine results, with primary first, then replacements
    combined_results = []
    if not primary_sampled_data.empty:
        combined_results.append(primary_sampled_data)

    if not replacement_sampled_data.empty:
        combined_results.append(replacement_sampled_data)

    # If we have results to combine, do so; otherwise return primary data
    if combined_results:
        # Ensure all DataFrames have the same columns before concatenating
        common_cols = set.intersection(
            *[set(df.columns) for df in combined_results])
        aligned_dfs = [df[list(common_cols)] for df in combined_results]

        combined_data = pd.concat(aligned_dfs, ignore_index=True)
        return combined_data
    else:
        # Fallback to just primary data even if empty
        return primary_sampled_data


def prepare_download_file(grouped_data, sample_display, original_df=None, col_config=None, sampling_params=None):
    """
    Prepare Excel file for download with improved sheet naming and content.
    Ensures UniqueID and Households Population are preserved in output sheets.
    Only includes timestamp in the Summary sheet.

    Args:
        grouped_data (pd.DataFrame): Combined grouped data
        sample_display (pd.DataFrame): Sample data display
        original_df (pd.DataFrame, optional): Original input dataframe for including all columns
        col_config (dict, optional): Column configuration for mapping
        sampling_params (dict, optional): Sampling parameters used for calculations

    Returns:
        BytesIO: Excel file buffer
    """
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get unique strata
            strata = sample_display['Stratum'].unique()
            total_strata = len(strata)

            # Create a mapping between original DataFrame and grouped data
            # This helps us merge with the original data later
            mapping_cols = {}
            if col_config and original_df is not None:
                mapping_cols = {
                    'admin3': col_config['master_data']['admin3'],
                    'site_id': col_config['master_data']['site_id'],
                    'strata': col_config['master_data']['strata'],
                    'households': col_config['master_data']['households']
                }

            # Create a list to track all sheets and their descriptions
            all_sheets = []

            # Create summary sheet first - Include timestamp here
            if sampling_params is not None and original_df is not None and col_config is not None:
                # Calculate summary statistics
                total_sites = len(original_df)
                total_strata_count = original_df[col_config['master_data']['strata']].nunique(
                )
                total_selected_sites = grouped_data[grouped_data['Selections'] > 0].shape[0]

                # Compute metrics from output data
                # Sample without reserve
                total_samples = int(sample_display['Sample'].sum())
                total_with_reserve = int(
                    sample_display['Sample_with_reserve'].sum())

                # Calculate Primary PSU Interviews and Replacement PSU Interviews if applicable
                primary_psu_interviews = 0
                replacement_psu_interviews = 0

                if 'PSU_Type' in grouped_data.columns:
                    # Identify the interview target column dynamically
                    target_col = next((col for col in grouped_data.columns if col.startswith(
                        'Interview_TARGET_')), None)

                    if target_col:
                        # Calculate interviews for primary and replacement PSUs
                        primary_data = grouped_data[grouped_data['PSU_Type']
                                                    == 'Primary']
                        replacement_data = grouped_data[grouped_data['PSU_Type']
                                                        == 'Replacement']

                        if not primary_data.empty:
                            primary_psu_interviews = int(
                                primary_data[target_col].sum())

                        if not replacement_data.empty:
                            replacement_psu_interviews = int(
                                replacement_data[target_col].sum())

                # Create summary dataframe
                summary_data = {
                    'Parameter': [
                        'Sampling Output Summary',
                        'Generated on',
                        '',
                        'Sampling Configuration',
                        'Total Rows',
                        'Total PSU',
                        'Total Strata',
                        'Total Selected Sites',
                        'Samples without Reserve',  # Renamed from Total Samples for clarity
                        'Sample with Reserve',
                    ],
                    'Value': [
                        '',
                        timestamp,
                        '',
                        '',
                        total_sites,
                        original_df[col_config['master_data']
                                    ['site_id']].nunique(),
                        total_strata_count,
                        total_selected_sites,
                        total_samples,
                        total_with_reserve,
                    ]
                }

                # Add Primary and Replacement PSU Interview counts if we have PSU_Type
                if 'PSU_Type' in grouped_data.columns:
                    summary_data['Parameter'].extend([
                        'Primary PSU Interviews',
                        'Replacement PSU Interviews',
                        'Total Interviews',  # The actual total interviews to be conducted
                    ])

                    summary_data['Value'].extend([
                        primary_psu_interviews,
                        replacement_psu_interviews,
                        primary_psu_interviews + replacement_psu_interviews,
                    ])

                # Continue with the rest of the summary data
                # [Rest of the summary data code remains unchanged]
                summary_data['Parameter'].extend([
                    '',
                    'Sampling Parameters',
                    'Confidence Level',
                    'Margin of Error',
                    'Design Effect',
                    'Interviews per Cluster',
                    'Reserve Percentage',
                    'Probability',
                ])

                summary_data['Value'].extend([
                    '',
                    '',
                    sampling_params.get('confidence_level', 'N/A'),
                    sampling_params.get('margin_of_error', 'N/A'),
                    sampling_params.get('design_effect', 'N/A'),
                    sampling_params.get('interviews_per_cluster', 'N/A'),
                    sampling_params.get('reserve_percentage', 'N/A'),
                    sampling_params.get('probability', 'N/A'),
                ])

                # Add random seed if it exists
                if 'random_seed' in sampling_params:
                    summary_data['Parameter'].append('Random Seed')
                    summary_data['Value'].append(
                        sampling_params['random_seed'])

                # Add replacement PSUs information
                if sampling_params.get('use_replacement_psus', False):
                    summary_data['Parameter'].append('')
                    summary_data['Value'].append('')

                    summary_data['Parameter'].append('Replacement PSUs')
                    summary_data['Value'].append('Enabled')

                    summary_data['Parameter'].append('Replacement Percentage')
                    summary_data['Value'].append(
                        f"{sampling_params.get('replacement_percentage', 0.0) * 100:.0f}%")

                    summary_data['Parameter'].append('Note')
                    summary_data['Value'].append(
                        f"Approximately {sampling_params.get('replacement_percentage', 0.0) * 100:.0f}% additional PSUs generated as replacements")

                # Add capacity constraint information
                summary_data['Parameter'].append('')
                summary_data['Value'].append('')

                summary_data['Parameter'].append('Capacity Constraints')
                summary_data['Value'].append('Enabled' if sampling_params.get(
                    'use_capacity_constraints', False) else 'Disabled')

                if sampling_params.get('use_capacity_constraints', False):
                    constraint_type = sampling_params.get(
                        'capacity_adjustment_type', "None")
                    summary_data['Parameter'].append('Constraint Type')
                    summary_data['Value'].append(constraint_type)

                    if constraint_type == "Reduction Factor":
                        summary_data['Parameter'].append('Reduction Factor')
                        summary_data['Value'].append(
                            f"{sampling_params.get('reduction_factor', 0.7) * 100:.0f}%")
                        summary_data['Parameter'].append('Note')
                        summary_data['Value'].append(
                            f"Maximum interviews limited to {sampling_params.get('reduction_factor', 0.7) * 100:.0f}% of household count")

                # Add information about clusters with interview targets exceeding household counts
                if 'has_excess_interviews' in st.session_state and st.session_state['has_excess_interviews']:
                    excess_count = st.session_state.get(
                        'excess_interview_count', 0)
                    summary_data['Parameter'].append(
                        'Clusters Exceeding Capacity')
                    summary_data['Value'].append(excess_count)

                    summary_data['Parameter'].append('Note')
                    if not sampling_params.get('use_capacity_constraints', False) or sampling_params.get('capacity_adjustment_type') == "None":
                        summary_data['Value'].append(
                            "Interview targets exceed household counts in some clusters. No constraints were applied.")
                    else:
                        total_constrained = st.session_state.get(
                            'total_constrained_clusters', 0)
                        total_redistributed = sum(
                            stats.get('interviews_redistributed', 0)
                            for stats in st.session_state.get('constraint_stats', {}).values()
                        )
                        summary_data['Value'].append(
                            f"{total_constrained} clusters were constrained, {total_redistributed} interviews were redistributed.")

                # Add "All Sheets" section
                summary_data['Parameter'].append('')
                summary_data['Value'].append('')
                summary_data['Parameter'].append('Excel Sheets Overview')
                summary_data['Value'].append('')

                summary_df = pd.DataFrame(summary_data)

                # Write summary data to sheet
                summary_df.to_excel(
                    writer,
                    sheet_name='Summary',
                    index=False
                )

                all_sheets.append(
                    ('Summary', 'Overall sampling parameters and configuration summary'))

            # Add the original data to the output file - WITHOUT timestamp
            if original_df is not None:
                original_df_with_metadata = original_df.copy()
                # Write original data to sheet without any timestamp
                original_df_with_metadata.to_excel(
                    writer,
                    sheet_name='Original Data',
                    index=False
                )

                all_sheets.append(
                    ('Original Data', 'Complete input data as provided in the original file'))

            # Process each stratum - WITHOUT timestamps
            for stratum in strata:
                # Filter data for current stratum
                stratum_sample = sample_display[sample_display['Stratum'] == stratum].copy(
                )
                stratum_grouped = grouped_data[grouped_data['Stratum'] == stratum].copy(
                )

                # If we have the original dataframe and config, merge to get all columns
                if original_df is not None and col_config is not None:
                    # First, we need to adjust column names to match
                    merge_cols = []

                    # Use admin3 and site_id as merge columns
                    admin_col = mapping_cols['admin3']
                    site_id_col = mapping_cols['site_id']
                    strata_col = mapping_cols['strata']
                    households_col = mapping_cols['households']

                    # Create a filtered view of original data for this stratum
                    stratum_orig = original_df[original_df[strata_col] == stratum].copy(
                    )

                    # Prepare for merge - ensure column names match
                    stratum_orig_for_merge = stratum_orig.copy()

                    # Create a mapping dict for the merge
                    # We need to map grouped_data column names to original column names
                    if admin_col in stratum_grouped.columns and admin_col in stratum_orig_for_merge.columns:
                        merge_cols.append((admin_col, admin_col))

                    if site_id_col in stratum_orig_for_merge.columns:
                        merge_cols.append((site_id_col, site_id_col))

                    # Include UniqueID in merge columns if it exists in both dataframes
                    if 'UniqueID' in stratum_grouped.columns and 'UniqueID' in stratum_orig_for_merge.columns:
                        merge_cols.append(('UniqueID', 'UniqueID'))

                    # Perform the merge if we have merge columns
                    if merge_cols:
                        # Rename columns in grouped data for merge
                        grouped_for_merge = stratum_grouped.copy()
                        for grouped_col, orig_col in merge_cols:
                            if grouped_col != orig_col and grouped_col in grouped_for_merge.columns:
                                grouped_for_merge.rename(
                                    columns={grouped_col: orig_col}, inplace=True)

                        # Determine which columns to include from grouped data
                        group_cols_to_include = [
                            'Selections', f"Interview_TARGET_{col_config['master_data']['households']}"]

                        # Make sure site_id is included for the merge
                        if site_id_col not in group_cols_to_include:
                            group_cols_to_include.append(site_id_col)

                        # Include UniqueID if it exists
                        if 'UniqueID' in grouped_for_merge.columns:
                            group_cols_to_include.append('UniqueID')

                        # Now we can merge
                        try:
                            # Determine which columns to merge on
                            merge_on = ['UniqueID'] if 'UniqueID' in grouped_for_merge.columns and 'UniqueID' in stratum_orig_for_merge.columns else [
                                site_id_col]

                            # Merge with the original data to get all columns including the households column
                            merged_data = pd.merge(
                                stratum_orig_for_merge,
                                grouped_for_merge[group_cols_to_include],
                                on=merge_on,
                                how='right'
                            )

                            # Ensure households column is included
                            if households_col not in merged_data.columns:
                                # Try to get it from original data using UniqueID lookup
                                if 'UniqueID' in merged_data.columns and 'UniqueID' in stratum_orig_for_merge.columns:
                                    # Create a lookup dictionary for households by UniqueID
                                    household_lookup = stratum_orig_for_merge.set_index(
                                        'UniqueID')[households_col].to_dict()
                                    # Apply the lookup to the merged data
                                    merged_data[households_col] = merged_data['UniqueID'].map(
                                        household_lookup)
                                else:
                                    # Try site_id based lookup
                                    household_lookup = stratum_orig_for_merge.set_index(
                                        site_id_col)[households_col].to_dict()
                                    merged_data[households_col] = merged_data[site_id_col].map(
                                        household_lookup)

                            # Use the merged data instead
                            if not merged_data.empty:
                                stratum_grouped = merged_data
                        except Exception as e:
                            st.warning(
                                f"Error merging data for stratum {stratum}: {str(e)}")
                            # Continue with unmerged data

                            # Try to add households column directly if possible
                            if 'UniqueID' in stratum_grouped.columns and households_col not in stratum_grouped.columns:
                                if 'UniqueID' in original_df.columns:
                                    # Create a lookup dictionary for households by UniqueID
                                    household_lookup = original_df.set_index(
                                        'UniqueID')[households_col].to_dict()
                                    # Apply the lookup to add the households column
                                    stratum_grouped[households_col] = stratum_grouped['UniqueID'].map(
                                        household_lookup)

                # Create better sheet names
                # Excel sheet name limit
                sheet_name_grouped = f'Selected Sites - {stratum}'[:31]
                # Excel sheet name limit
                sheet_name_sample = f'Sample Summary - {stratum}'[:31]

                # Write to sheets WITHOUT timestamp
                stratum_grouped.to_excel(
                    writer,
                    sheet_name=sheet_name_grouped,
                    index=False
                )

                all_sheets.append(
                    (sheet_name_grouped, f'Detailed selected sampling sites for {stratum} stratum'))

                stratum_sample.to_excel(
                    writer,
                    sheet_name=sheet_name_sample,
                    index=False
                )

                all_sheets.append(
                    (sheet_name_sample, f'Summary of sample statistics for {stratum} stratum'))

            # Only include combined sheets if we have multiple strata - WITHOUT timestamps
            if total_strata > 1:
                # Also include combined sheets for overview
                all_grouped = grouped_data.copy()

                # Add households column to all_grouped if it's missing and UniqueID is present
                if original_df is not None and 'UniqueID' in all_grouped.columns:
                    households_col = col_config['master_data']['households']
                    if households_col not in all_grouped.columns:
                        # Create a lookup dictionary for households by UniqueID
                        household_lookup = original_df.set_index(
                            'UniqueID')[households_col].to_dict()
                        # Apply the lookup to add the households column
                        all_grouped[households_col] = all_grouped['UniqueID'].map(
                            household_lookup)

                all_sample = sample_display.copy()

                # Write without timestamp
                all_grouped.to_excel(
                    writer,
                    sheet_name='All Selected Sites',
                    index=False
                )

                all_sheets.append(
                    ('All Selected Sites', 'Combined view of all selected sites across all strata'))

                all_sample.to_excel(
                    writer,
                    sheet_name='All Sample Summary',
                    index=False
                )

                all_sheets.append(
                    ('All Sample Summary', 'Combined summary of sample statistics across all strata'))

            # Include a sheet specifically for replacement PSUs - WITHOUT timestamp
            if 'PSU_Type' in grouped_data.columns:
                replacement_data = grouped_data[grouped_data['PSU_Type'] == 'Replacement'].copy(
                )
                if not replacement_data.empty:
                    # Write without timestamp
                    replacement_data.to_excel(
                        writer,
                        sheet_name='Replacement PSUs',
                        index=False
                    )

                    all_sheets.append(
                        ('Replacement PSUs', 'Backup/replacement PSUs that can be used if primary sites are inaccessible'))

                    # Also add a combined view with primary and their replacements
                    combined_view = grouped_data.sort_values(
                        ['Stratum', 'PSU_Type'])
                    combined_view.to_excel(
                        writer,
                        sheet_name='Combined Primary-Replacement',
                        index=False
                    )

                    all_sheets.append(
                        ('Combined Primary-Replacement', 'Combined view of both primary and replacement PSUs'))

                # Add a sheet for primary PSUs as well
                primary_data = grouped_data[grouped_data['PSU_Type'] == 'Primary'].copy(
                )
                if not primary_data.empty:
                    # Write without timestamp
                    primary_data.to_excel(
                        writer,
                        sheet_name='Primary PSUs',
                        index=False
                    )

                    all_sheets.append(
                        ('Primary PSUs', 'Selected primary PSUs for data collection'))

            # Now add the sheet list to the Summary sheet
            if all_sheets and 'Summary' in writer.sheets:
                # Create a dataframe with sheet info
                sheet_info_df = pd.DataFrame({
                    'Sheet Name': [sheet[0] for sheet in all_sheets],
                    'Description': [sheet[1] for sheet in all_sheets]
                })

                # Get the current workbook
                workbook = writer.book
                summary_sheet = workbook['Summary']

                # Find the last row in the summary sheet
                last_row = 0
                for row in summary_sheet.iter_rows():
                    if row[0].value is not None:
                        last_row = row[0].row

                # Add a header for the sheets section
                summary_sheet.cell(row=last_row+2, column=1,
                                   value="Available Sheets")
                summary_sheet.cell(row=last_row+2, column=2,
                                   value="Description")

                # Add each sheet and its description
                for i, (sheet_name, description) in enumerate(all_sheets):
                    summary_sheet.cell(
                        row=last_row+3+i, column=1, value=sheet_name)
                    summary_sheet.cell(
                        row=last_row+3+i, column=2, value=description)

        return output

    except Exception as e:
        st.error(f"Error preparing download file: {str(e)}")
        st.exception(e)
        return None


def process_grouped_data(sampled_data, col_config):
    """
    Process grouped data with stratum information.

    Args:
        sampled_data (pd.DataFrame): The sampled data
        col_config (dict): Column configuration

    Returns:
        pd.DataFrame: Processed grouped data
    """
    try:
        # Make sure required columns exist
        required_columns = [
            col_config['master_data']['admin3'],
            col_config['master_data']['site_id'],
            'Stratum',
            'Selections',
            f"Interview_TARGET_{col_config['master_data']['households']}"
        ]

        for col in required_columns:
            if col not in sampled_data.columns:
                raise ValueError(
                    f"Required column '{col}' not found in sampled data")

        # Group the data
        grouped_data = sampled_data.groupby(
            [
                col_config['master_data']['admin3'],
                col_config['master_data']['site_id'],
                'Stratum'
            ],
            as_index=False
        ).agg({
            'Selections': 'sum',
            f"Interview_TARGET_{col_config['master_data']['households']}": 'sum'
        })

        return grouped_data

    except Exception as e:
        st.error(f"Error in process_grouped_data: {str(e)}")
        return pd.DataFrame()


def update_main_display(sampled_data, df_sample, col_config, sampling_params=None):
    """
    Update main display with stratum-specific information with improved error handling and formatting.
    Ensures UniqueID is preserved in grouped data and includes Households Population from original data.
    Applies capacity constraints if enabled.

    Args:
        sampled_data (pd.DataFrame): The sampled data
        df_sample (pd.DataFrame): Sample data
        col_config (dict): Column configuration
        sampling_params (dict, optional): Sampling parameters

    Returns:
        tuple: (grouped_data, sample_display)
    """
    try:
        # Check for required columns
        required_cols = ['Stratum', 'Selections']
        for col in required_cols:
            if col not in sampled_data.columns:
                raise ValueError(
                    f"Required column '{col}' not found in sampled data")

        # Add debug information
        st.session_state.setdefault('display_debug', {}).update({
            'sampled_data_columns': list(sampled_data.columns),
            'df_sample_columns': list(df_sample.columns)
        })

        # Process grouped data first with error handling
        try:
            admin_col = col_config['master_data']['admin3']
            site_id_col = col_config['master_data']['site_id']
            site_name_col = col_config['master_data']['site_name']
            households_col = col_config['master_data']['households']

            # Make sure the df_sample has 'Stratum' column
            if 'Stratum' not in df_sample.columns:
                raise ValueError("'Stratum' column not found in df_sample")

            # Make sure sampled_data has the required columns
            for col in [admin_col, site_id_col, 'Stratum', 'Selections']:
                if col not in sampled_data.columns:
                    if col == admin_col:
                        # Use 'Admin3' instead which might have been renamed
                        if 'Admin3' in sampled_data.columns:
                            sampled_data[admin_col] = sampled_data['Admin3']
                        else:
                            raise ValueError(
                                f"Column '{col}' not found in sampled_data")
                    else:
                        raise ValueError(
                            f"Column '{col}' not found in sampled_data")

            target_col = f"Interview_TARGET_{households_col}"
            if target_col not in sampled_data.columns:
                # Calculate it if missing
                # Default interviews per cluster
                sampled_data[target_col] = sampled_data['Selections'] * 5
                st.warning(
                    f"Column '{target_col}' not found; calculated using default 5 interviews per cluster")

            # Ensure we include the Households Population column in the result
            # First check if it's already in the data
            if households_col in sampled_data.columns:
                # It's already there, make sure we keep it
                households_data_present = True
            else:
                # We'll need to include it in the final result
                households_data_present = False

            # Group the data with more error handling
            # Include UniqueID in the group columns if it exists
            group_cols = [admin_col, site_id_col, 'Stratum']

            # Include PSU_Type in group columns if it exists
            has_psu_type = 'PSU_Type' in sampled_data.columns
            if has_psu_type:
                group_cols.append('PSU_Type')

            # Check if UniqueID exists in the sampled data
            if 'UniqueID' in sampled_data.columns:
                # Include UniqueID in the group columns
                group_cols.append('UniqueID')
                st.session_state.setdefault('debug_uniqueid', {}).update({
                    'uniqueid_present': True,
                    'uniqueid_sample': sampled_data['UniqueID'].head(5).tolist()
                })
            else:
                st.session_state.setdefault('debug_uniqueid', {}).update({
                    'uniqueid_present': False
                })

            # Ensure all grouping columns exist
            for col in group_cols:
                if col not in sampled_data.columns:
                    if col == 'UniqueID':
                        # If UniqueID is missing, remove it from group_cols
                        group_cols.remove('UniqueID')
                    elif col == 'PSU_Type':
                        # If PSU_Type is missing, remove it from group_cols
                        group_cols.remove('PSU_Type')
                    else:
                        raise ValueError(
                            f"Cannot group by '{col}' - column not found")

            # If households column is present, include it in the groupby agg
            agg_cols = {
                'Selections': 'sum',
                target_col: 'sum'
            }

            # If households column is present, keep the first value
            if households_data_present and households_col in sampled_data.columns:
                agg_cols[households_col] = 'first'

            # Group the data preserving UniqueID and potentially the households column
            grouped_data = sampled_data.groupby(
                group_cols, as_index=False).agg(agg_cols)

            # If we have PSU_Type in the original data but it was removed during grouping,
            # make sure it's added back to grouped_data
            if has_psu_type and 'PSU_Type' not in grouped_data.columns:
                # Attempt to recover PSU_Type by merging with original data
                if 'UniqueID' in grouped_data.columns and 'UniqueID' in sampled_data.columns:
                    psu_type_map = sampled_data[[
                        'UniqueID', 'PSU_Type']].drop_duplicates()
                    grouped_data = pd.merge(
                        grouped_data, psu_type_map, on='UniqueID', how='left')
                elif site_id_col in grouped_data.columns and site_id_col in sampled_data.columns:
                    psu_type_map = sampled_data[[
                        site_id_col, 'PSU_Type']].drop_duplicates()
                    grouped_data = pd.merge(
                        grouped_data, psu_type_map, on=site_id_col, how='left')

            # Check for interview targets exceeding household counts before applying constraints
            # This will help notify users if there are potential constraint situations
            if households_col in grouped_data.columns and target_col in grouped_data.columns:
                # Check if any interview targets exceed household counts
                exceeds_count = (
                    grouped_data[target_col] > grouped_data[households_col]).sum()
                if exceeds_count > 0:
                    # Store this information in session state for display later
                    st.session_state['has_excess_interviews'] = True
                    st.session_state['excess_interview_count'] = exceeds_count

                    # If capacity constraints are not enabled or set to "None", store for later display
                    capacity_enabled = sampling_params and sampling_params.get(
                        'use_capacity_constraints', False)
                    capacity_type_none = sampling_params and sampling_params.get(
                        'capacity_adjustment_type') == "None"

                    if not capacity_enabled or capacity_type_none:
                        st.session_state['capacity_warning_needed'] = True
                        # Create a filtered dataframe of clusters exceeding capacity for later display
                        st.session_state['excess_clusters'] = grouped_data[grouped_data[target_col]
                                                                           > grouped_data[households_col]].copy()
                else:
                    st.session_state['has_excess_interviews'] = False
                    st.session_state['excess_interview_count'] = 0
                    st.session_state['capacity_warning_needed'] = False

            # Apply capacity constraints if enabled in the sampling parameters
            if sampling_params and sampling_params.get('use_capacity_constraints', False) and sampling_params.get('capacity_adjustment_type') != "None":
                # Initialize storage for constraint statistics
                st.session_state['constraint_stats'] = {}
                st.session_state['cluster_constraints'] = {}
                total_constrained_clusters = 0

                # Calculate effective limit based on adjustment type
                if sampling_params.get('capacity_adjustment_type') == "Capped":
                    # Use exact household count as the limit
                    grouped_data['Effective_Limit'] = grouped_data[households_col]
                elif sampling_params.get('capacity_adjustment_type') == "Reduction Factor":
                    # Reduce to this percentage of household count
                    reduction_factor = sampling_params.get(
                        'reduction_factor', 0.7)
                    grouped_data['Effective_Limit'] = grouped_data[households_col] * \
                        reduction_factor
                    # Ensure we have at least 1 interview per selected cluster
                    grouped_data['Effective_Limit'] = np.maximum(
                        grouped_data['Effective_Limit'],
                        (grouped_data['Selections'] > 0).astype(int)
                    )
                else:
                    # Default to exact household count
                    grouped_data['Effective_Limit'] = grouped_data[households_col]

                # Process each stratum separately for constraints
                for stratum in grouped_data['Stratum'].unique():
                    stratum_df = grouped_data[grouped_data['Stratum'] == stratum].copy(
                    )

                    # Mark clusters as constrained if target interviews exceed effective limit
                    stratum_df['Is_Constrained'] = stratum_df[target_col] > stratum_df['Effective_Limit']

                    # Get the admin value for this stratum for record keeping
                    admin_val = stratum_df[admin_col].iloc[0] if not stratum_df.empty else "unknown"
                    stratum_key = f"{admin_val}_{stratum}"

                    # Only apply redistribution if there are any constrained clusters
                    if stratum_df['Is_Constrained'].any():
                        # Apply the redistribution function
                        updated_df, stats = redistribute_excess_interviews(
                            stratum_df,
                            'Effective_Limit',
                            target_col
                        )

                        # Store constraint statistics for this stratum
                        st.session_state['constraint_stats'][stratum_key] = stats
                        total_constrained_clusters += stats.get(
                            'clusters_constrained', 0)

                        # Store constraint indicators for each cluster
                        for idx, row in updated_df.iterrows():
                            cluster_id = row.get(
                                'UniqueID', row.get(site_id_col, str(idx)))
                            st.session_state['cluster_constraints'][cluster_id] = {
                                'is_constrained': row.get('Is_Constrained', False),
                                'received_redistribution': row.get('Received_Redistribution', False),
                                'original_target': row.get(target_col, 0),
                                # Will be different if redistributed
                                'final_target': row.get(target_col, 0)
                            }

                        # Update the original grouped data with the constrained version
                        # First make a copy to avoid SettingWithCopyWarning
                        temp_df = updated_df.copy()
                        # Ensure consistent types for numeric columns
                        for col in temp_df.columns:
                            if col in grouped_data.columns and pd.api.types.is_numeric_dtype(grouped_data[col]):
                                temp_df[col] = pd.to_numeric(
                                    temp_df[col], errors='coerce')
                                if pd.api.types.is_integer_dtype(grouped_data[col]):
                                    temp_df[col] = temp_df[col].fillna(
                                        0).astype(int)
                                elif pd.api.types.is_float_dtype(grouped_data[col]):
                                    temp_df[col] = temp_df[col].fillna(
                                        0.0).astype(float)

                        # Now update the original dataframe
                        grouped_data.loc[grouped_data['Stratum']
                                         == stratum] = temp_df

                # Store total constrained clusters count
                st.session_state['total_constrained_clusters'] = total_constrained_clusters
                st.session_state['total_clusters'] = len(grouped_data)

            # Rename columns to be more user-friendly
            grouped_data.rename(columns={
                'Selections': 'Selected Clusters',
                target_col: 'Target Interviews'
            }, inplace=True)

            # If we have households data in the original sampled_data, make sure it's carried through
            if households_data_present and households_col in sampled_data.columns and households_col not in grouped_data.columns:
                # Calculate average households per group
                grouped_data[households_col] = sampled_data.groupby(
                    group_cols)[households_col].first().reset_index()[households_col]

            # Handle potential errors after grouping
            if grouped_data.empty:
                raise ValueError("Grouping resulted in empty DataFrame")

        except Exception as e:
            st.error(f"Error in grouped data processing: {str(e)}")
            st.exception(e)  # This will show the full traceback in development

            # Create a minimal grouped data as fallback
            grouped_data = pd.DataFrame({
                'Error': ["Failed to create grouped data"],
                'Details': [str(e)]
            })

        # Prepare sample display data with error handling
        try:
            # Make sure df_sample has all required columns
            admin_col_name = col_config['master_data']['admin3']
            required_sample_cols = [
                admin_col_name, 'Sample', 'Sample_with_reserve', 'Stratum', 'Strata_name', 'Clusters visited']

            missing_cols = [
                col for col in required_sample_cols if col not in df_sample.columns]
            if missing_cols:
                raise ValueError(
                    f"Missing columns in sample data: {missing_cols}")

            sample_display = df_sample[required_sample_cols].copy()

        except Exception as e:
            st.error(f"Error in sample display preparation: {str(e)}")
            st.exception(e)

            # Create a minimal sample display as fallback
            sample_display = pd.DataFrame({
                'Error': ["Failed to create sample display"],
                'Details': [str(e)]
            })

        # Create tabs for display with better error handling
        st.write("")  # Spacing
        st.write("")  # Spacing
        st.text("")

        try:
            strata = df_sample['Stratum'].unique()

            # Check if we have replacement PSUs by safely checking the column existence
            has_replacements = False
            if 'PSU_Type' in sampled_data.columns:
                has_replacements = 'Replacement' in sampled_data['PSU_Type'].values
            elif 'PSU_Type' in grouped_data.columns:
                has_replacements = 'Replacement' in grouped_data['PSU_Type'].values

            # Create tabs based on whether we have replacements
            if has_replacements:
                tabs = st.tabs(['All Data', 'Primary PSUs', 'Replacement PSUs'] +
                               [f'Stratum: {stratum}' for stratum in strata])
            else:
                tabs = st.tabs(
                    ['All Data'] + [f'Stratum: {stratum}' for stratum in strata])

            # Display all data tab
            with tabs[0]:
                # Check if we need to display capacity warning (moved above the tables)
                if 'capacity_warning_needed' in st.session_state and st.session_state['capacity_warning_needed']:
                    excess_count = st.session_state.get(
                        'excess_interview_count', 0)

                    # Display warning above both columns
                    st.warning(
                        f"⚠️ **{excess_count} clusters** have interview targets exceeding household counts. Here are the clusters affected.")

                    # Create an expander to show the excess clusters, but keep it above the tables
                    with st.expander("View Clusters Exceeding Capacity", expanded=False):
                        if 'excess_clusters' in st.session_state:
                            excess_df = st.session_state['excess_clusters'].copy(
                            )
                            st.dataframe(excess_df, use_container_width=True)
                        else:
                            st.write("Details not available")

                # Display the two tables side by side
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Selected Sites")
                    if 'Selected Clusters' in grouped_data.columns:
                        # Sort by number of selections (descending)
                        display_df = grouped_data.sort_values(
                            'Selected Clusters', ascending=False)
                        # Highlight selected sites
                        display_df['Is_Selected'] = display_df['Selected Clusters'] > 0

                        # Add a column to show interview target vs household count
                        if households_col in display_df.columns and 'Target Interviews' in display_df.columns:
                            display_df['Target_vs_HH'] = display_df['Target Interviews'] - \
                                display_df[households_col]
                            display_df['Exceeds_Capacity'] = display_df['Target_vs_HH'] > 0

                        # Add constraint indicator to the display
                        if 'Is_Constrained' in display_df.columns:
                            # Count constrained clusters
                            constrained_count = display_df['Is_Constrained'].sum(
                            )
                            redistributed_count = display_df['Received_Redistribution'].sum(
                            ) if 'Received_Redistribution' in display_df.columns else 0

                            # Show constraint summary above both tables
                            if constrained_count > 0:
                                # We've moved this information to the capacity constraints expander in render_main_tab
                                pass

                        # Display the dataframe
                        st.dataframe(
                            display_df, use_container_width=True, height=300)
                    else:
                        st.dataframe(
                            grouped_data, use_container_width=True, height=300)

                with col2:
                    st.subheader("Sample Summary")
                    st.dataframe(sample_display,
                                 use_container_width=True, height=300)

                # Display primary and replacement PSUs in separate tabs if available
                if has_replacements and 'PSU_Type' in grouped_data.columns:
                    # Primary PSUs tab
                    with tabs[1]:
                        st.subheader("Primary PSUs")
                        primary_data = grouped_data[grouped_data['PSU_Type'] == 'Primary'].copy(
                        )
                        st.dataframe(
                            primary_data, use_container_width=True, height=300)

                    # Replacement PSUs tab
                    with tabs[2]:
                        st.subheader("Replacement/Backup PSUs")
                        replacement_data = grouped_data[grouped_data['PSU_Type'] == 'Replacement'].copy(
                        )
                        st.dataframe(replacement_data,
                                     use_container_width=True, height=300)

                    # Adjust stratum tab index to account for the new tabs
                    stratum_tab_offset = 3
                else:
                    # If PSU_Type doesn't exist or no replacements, fill the tabs with placeholder content
                    if has_replacements:  # This shouldn't happen if we fixed the code properly
                        with tabs[1]:
                            st.info("No primary PSUs data available.")
                        with tabs[2]:
                            st.info("No replacement PSUs data available.")
                    stratum_tab_offset = 1

            # Display stratum-specific tabs if we have meaningful data
            if not (grouped_data.empty or sample_display.empty or 'Error' in grouped_data.columns):
                for i, stratum in enumerate(strata):
                    with tabs[i + stratum_tab_offset]:
                        # Check if there are any capacity warnings for this stratum
                        if 'capacity_warning_needed' in st.session_state and st.session_state['capacity_warning_needed']:
                            if 'excess_clusters' in st.session_state:
                                stratum_excess = st.session_state['excess_clusters'][
                                    st.session_state['excess_clusters']['Stratum'] == stratum]
                                if not stratum_excess.empty:
                                    excess_count = len(stratum_excess)
                                    st.warning(
                                        f"⚠️ **{excess_count} clusters** in stratum '{stratum}' have interview targets exceeding household counts.")

                                    with st.expander(f"View Exceeding Clusters in {stratum}", expanded=False):
                                        st.dataframe(
                                            stratum_excess, use_container_width=True)

                        # Display the side-by-side tables
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader(f"Selected Sites - {stratum}")
                            # Use the actual column name for Stratum
                            if 'Stratum' in grouped_data.columns:
                                stratum_grouped = grouped_data[grouped_data['Stratum'] == stratum]
                                if 'Selected Clusters' in stratum_grouped.columns:
                                    # Sort by number of selections (descending)
                                    stratum_grouped = stratum_grouped.sort_values(
                                        'Selected Clusters', ascending=False)
                                    # Highlight selected sites
                                    stratum_grouped['Is_Selected'] = stratum_grouped['Selected Clusters'] > 0

                                st.dataframe(
                                    stratum_grouped, use_container_width=True, height=300)
                            else:
                                st.error(
                                    "'Stratum' column not found in grouped data")
                                st.dataframe(grouped_data.head(
                                    1), use_container_width=True)

                        with col2:
                            st.subheader(f"Sample Summary - {stratum}")
                            if 'Stratum' in sample_display.columns:
                                stratum_sample = sample_display[sample_display['Stratum'] == stratum]
                                st.dataframe(
                                    stratum_sample, use_container_width=True, height=300)
                            else:
                                st.error(
                                    "'Stratum' column not found in sample display")
                                st.dataframe(sample_display.head(
                                    1), use_container_width=True)
        except Exception as e:
            st.error(f"Error creating display tabs: {str(e)}")
            st.exception(e)

        # Return the original (unmodified) grouped_data for further processing
        # This is important because other functions expect these column names
        # We'll revert any display-only column name changes
        if 'Selected Clusters' in grouped_data.columns:
            grouped_data.rename(
                columns={'Selected Clusters': 'Selections'}, inplace=True)

        if 'Target Interviews' in grouped_data.columns:
            grouped_data.rename(
                columns={'Target Interviews': target_col}, inplace=True)

        return grouped_data, sample_display

    except Exception as e:
        st.error(f"Error in update_main_display: {str(e)}")
        st.exception(e)
        # Return empty DataFrames as a fallback
        return pd.DataFrame(), pd.DataFrame()


def summarize_replacement_issues(df_sample):
    """
    Summarize replacement PSU issues for clearer reporting.

    Args:
        df_sample (pd.DataFrame): The sample data frame containing strata information

    Returns:
        str: HTML formatted summary of replacement PSU issues
    """
    if 'replacement_issues' not in st.session_state:
        return ""

    issues = st.session_state['replacement_issues']
    if not issues:
        return ""

    # Group issues by admin and stratum
    grouped_issues = {}
    for issue in issues:
        admin = issue.get('admin', 'Unknown')
        stratum = issue.get('stratum', 'Unknown')
        key = f"{admin}_{stratum}"

        if key not in grouped_issues:
            grouped_issues[key] = {
                'admin': admin,
                'stratum': stratum,
                'count': 0,
                'details': issue.get('issue', 'no_details')
            }

        grouped_issues[key]['count'] += 1

    # Create a summary of the issues
    summary_html = "<div style='margin-bottom: 10px;'>"
    summary_html += "<h4>Summary of Replacement PSU Issues</h4>"

    if not grouped_issues:
        summary_html += "<p>No issues found with replacement PSUs.</p>"
    else:
        # Create a summary table
        summary_html += "<table style='width: 100%; border-collapse: collapse;'>"
        summary_html += "<tr style='background-color: #f2f2f2;'>"
        summary_html += "<th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Admin</th>"
        summary_html += "<th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Stratum</th>"
        summary_html += "<th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>PSUs Affected</th>"
        summary_html += "<th style='padding: 8px; text-align: left; border: 1px solid #ddd;'>Issue</th>"
        summary_html += "</tr>"

        # Sort issues by admin and stratum for better readability
        sorted_issues = sorted(grouped_issues.values(),
                               key=lambda x: (x['admin'], x['stratum']))

        # Add each issue to the table
        for issue in sorted_issues:
            issue_desc = "Insufficient data" if issue['details'] == 'no_available_psus' else issue['details']
            summary_html += f"<tr style='border: 1px solid #ddd;'>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{issue['admin']}</td>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{issue['stratum']}</td>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{issue['count']}</td>"
            summary_html += f"<td style='padding: 8px; border: 1px solid #ddd;'>{issue_desc}</td>"
            summary_html += "</tr>"

        summary_html += "</table>"

        # Add a note with recommendations
        summary_html += "<p style='margin-top: 10px;'><strong>Note:</strong> For strata with insufficient data for replacement PSUs, "
        summary_html += "consider adding more PSUs to your dataset, enabling cross-stratum replacements, "
        summary_html += "or adjusting your sampling parameters to reduce the number of replacements needed.</p>"

    summary_html += "</div>"
    return summary_html


def display_replacement_summary(df_sample):
    """
    Display a summary of replacement PSU issues in the UI.

    Args:
        df_sample (pd.DataFrame): The sample data frame
    """
    if 'replacement_issues' not in st.session_state or not st.session_state['replacement_issues']:
        return

    issues = st.session_state['replacement_issues']

    # Count issues by admin and stratum
    issue_counts = {}
    affected_admin_strata = set()
    for issue in issues:
        admin = issue.get('admin', 'Unknown')
        stratum = issue.get('stratum', 'Unknown')
        key = f"{admin}_{stratum}"
        affected_admin_strata.add(key)

        if key not in issue_counts:
            issue_counts[key] = 0
        issue_counts[key] += 1

    # Display a warning with the count of affected admin-strata combinations
    st.warning(
        f"⚠️ **{len(affected_admin_strata)}** admin-stratum combinations have insufficient data for replacement PSUs.")

    # Create an expander to show the details
    with st.expander("View Replacement PSU Issues", expanded=False):
        # Show the first 5 affected admin-strata
        if issue_counts:
            st.write("### Affected Admin-Stratum Combinations")

            # Convert to a list and sort
            issues_list = [(admin_stratum, count)
                           for admin_stratum, count in issue_counts.items()]
            issues_list.sort(key=lambda x: x[1], reverse=True)

            # Create a dataframe for display
            display_issues = []
            for i, (admin_stratum, count) in enumerate(issues_list):
                if i >= 5 and len(issues_list) > 5:
                    st.info(
                        f"... and {len(issues_list) - 5} more combinations.")
                    break

                admin, stratum = admin_stratum.split('_', 1)
                display_issues.append({
                    'Admin': admin,
                    'Stratum': stratum,
                    'PSUs Affected': count
                })

            # Display the dataframe
            if display_issues:
                st.dataframe(pd.DataFrame(display_issues),
                             use_container_width=True)

            # List all affected PSUs
            # List all affected PSUs in two columns
            st.write("### List of Affected PSUs")
            st.write(
                "The following admin-stratum combinations have issues with replacement PSUs:")

            # Split the list into two approximately equal parts
            middle_idx = len(issues_list) // 2
            left_column_issues = issues_list[:middle_idx]
            right_column_issues = issues_list[middle_idx:]

            # Create two columns
            col1, col2 = st.columns(2)

            # Display issues in the left column
            with col1:
                for admin_stratum, count in left_column_issues:
                    admin, stratum = admin_stratum.split('_', 1)
                    st.write(
                        f"- **Admin**: {admin}, **Stratum**: {stratum}, **Count**: {count}")

            # Display issues in the right column
            with col2:
                for admin_stratum, count in right_column_issues:
                    admin, stratum = admin_stratum.split('_', 1)
                    st.write(
                        f"- **Admin**: {admin}, **Stratum**: {stratum}, **Count**: {count}")

            # Add recommendation
            st.info(
                "**Recommendation:** To address these issues, consider:\n"
                "1. Adding more PSUs to your dataset for the affected strata\n"
                "2. Reducing the replacement percentage to require fewer replacement PSUs"
            )


# Update the process_sampling function to track replacement issues better
def update_process_sampling():
    """
    Add this code to process_sampling function to improve replacement issue tracking.
    This should be added just after the `df_for_replacement = df_for_replacement[...]` line.

    Example:
    ```python
    # Track which strata have limited available PSUs for replacements
    available_psu_counts = {}
    if not df_for_replacement.empty:
        # Count available PSUs by admin and stratum
        admin_col = col_config['master_data']['admin3']
        strata_col = col_config['master_data']['strata']

        for (admin, stratum), group in df_for_replacement.groupby([admin_col, strata_col]):
            available_psu_counts[(admin, stratum)] = len(group)

        # Compare with sample_data to identify potential issues
        for _, row in sample_data.iterrows():
            admin = row['Admin3']
            stratum = row['Stratum']
            required_replacements = math.ceil(row['Clusters visited'] * params['replacement_percentage'])

            if (admin, stratum) in available_psu_counts:
                if available_psu_counts[(admin, stratum)] < required_replacements:
                    # Add to replacement issues
                    if 'replacement_issues' not in st.session_state:
                        st.session_state['replacement_issues'] = []

                    st.session_state['replacement_issues'].append({
                        'admin': admin,
                        'stratum': stratum,
                        'issue': 'insufficient_psus',
                        'available': available_psu_counts[(admin, stratum)],
                        'required': required_replacements
                    })
            else:
                # No PSUs available at all for this combination
                if 'replacement_issues' not in st.session_state:
                    st.session_state['replacement_issues'] = []

                st.session_state['replacement_issues'].append({
                    'admin': admin,
                    'stratum': stratum,
                    'issue': 'no_available_psus'
                })
    ```
    """
    pass


# Update render_main_tab to include the replacement summary
def update_render_main_tab():
    """
    Add this code to render_main_tab after processing the data but before the download section

    Example:
    ```python
    # After grouped_data, sample_display = update_main_display(...) but before download section

    # Display replacement PSU issues summary if applicable
    if 'replacement_issues' in st.session_state and st.session_state['replacement_issues']:
        st.divider()
        st.subheader("Replacement PSUs Status")
        display_replacement_summary(df_sample)
    ```
    """
    pass


def redistribute_excess_interviews(stratum_df, limit_col, target_col):
    """
    Redistribute excess interviews from constrained clusters to unconstrained ones.

    Args:
        stratum_df(pd.DataFrame): DataFrame containing clusters for a single stratum
        limit_col(str): Name of column containing household count limits(may be adjusted by cap or reduction factor)
        target_col(str): Name of column containing target interview counts

    Returns:
        pd.DataFrame: Updated DataFrame with redistributed interviews
        dict: Statistics about the redistribution process
    """
    # Create a copy to avoid modifying the original
    df = stratum_df.copy()

    # Sort by UniqueID for reproducibility if available
    if 'UniqueID' in df.columns:
        df = df.sort_values('UniqueID')

    # Ensure numeric values for the calculation columns
    df[limit_col] = pd.to_numeric(df[limit_col], errors='coerce').fillna(0)
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)

    # Identify constrained clusters and calculate excess interviews
    df['Is_Constrained'] = df[target_col] > df[limit_col]
    df['Excess_Interviews'] = np.where(
        df['Is_Constrained'],
        df[target_col] - df[limit_col],
        0
    )

    # Round excess interviews to whole numbers
    df['Excess_Interviews'] = np.ceil(df['Excess_Interviews']).astype(int)

    # Calculate total excess interviews that need redistribution
    total_excess = df['Excess_Interviews'].sum()

    # If no excess, return the original dataframe with added flags
    if total_excess == 0:
        return df, {'total_excess': 0, 'clusters_constrained': 0}

    # Cap interviews at available capacity for constrained clusters
    # df.loc[df['Is_Constrained'],
    #        target_col] = df.loc[df['Is_Constrained'], limit_col]

    df.loc[df['Is_Constrained'],
           target_col] = df.loc[df['Is_Constrained'], limit_col].astype(int)

    # Flag for tracking if interviews were redistributed
    df['Received_Redistribution'] = False

    # Only redistribute if there are clusters with selections
    # This ensures we only redistribute to clusters that were already selected
    recipient_clusters = df[(~df['Is_Constrained']) &
                            (df['Selections'] > 0)].copy()

    if recipient_clusters.empty:
        # No selected unconstrained clusters available for redistribution
        # Try using any unconstrained cluster, even if it wasn't originally selected
        recipient_clusters = df[~df['Is_Constrained']].copy()

        if recipient_clusters.empty:
            # No capacity for redistribution at all
            return df, {
                'total_excess': total_excess,
                'clusters_constrained': df['Is_Constrained'].sum(),
                'interviews_lost': total_excess,
                'insufficient_capacity': True
            }

    # Calculate remaining capacity in recipient clusters
    recipient_clusters['Remaining_Capacity'] = recipient_clusters[limit_col] - \
        recipient_clusters[target_col]

    # Remove any clusters with zero or negative remaining capacity
    recipient_clusters = recipient_clusters[recipient_clusters['Remaining_Capacity'] > 0]

    if recipient_clusters.empty:
        # No capacity for redistribution
        return df, {
            'total_excess': total_excess,
            'clusters_constrained': df['Is_Constrained'].sum(),
            'interviews_lost': total_excess,
            'insufficient_capacity': True
        }

    # Calculate total remaining capacity
    total_capacity = recipient_clusters['Remaining_Capacity'].sum()

    # Calculate how many interviews we can actually redistribute
    redistributable_interviews = min(total_excess, total_capacity)

    # Calculate weight for each recipient cluster based on remaining capacity
    recipient_clusters['Redistribution_Weight'] = recipient_clusters['Remaining_Capacity'] / total_capacity

    # Calculate how many interviews to add to each recipient cluster
    recipient_clusters['Interviews_To_Add'] = np.floor(
        recipient_clusters['Redistribution_Weight'] *
        redistributable_interviews
    ).astype(int)

    # Distribution may leave some interviews unassigned due to floor rounding
    # Distribute remaining interviews to clusters with highest capacity
    remaining_interviews = int(
        redistributable_interviews - recipient_clusters['Interviews_To_Add'].sum())

    if remaining_interviews > 0:
        # Sort by remaining capacity (highest first) to distribute remaining interviews
        sorted_recipients = recipient_clusters.sort_values(
            'Remaining_Capacity', ascending=False)

        # Add one interview to each cluster with highest capacity until all distributed
        for i in range(min(remaining_interviews, len(sorted_recipients))):
            idx = sorted_recipients.index[i]
            recipient_clusters.loc[idx, 'Interviews_To_Add'] += 1

    # Update the original dataframe with the redistributed interviews
    for idx, row in recipient_clusters.iterrows():
        if row['Interviews_To_Add'] > 0:
            df.loc[idx, target_col] += row['Interviews_To_Add']
            df.loc[idx, 'Received_Redistribution'] = True

    # Calculate how many interviews were actually redistributed
    interviews_redistributed = recipient_clusters['Interviews_To_Add'].sum()
    interviews_lost = total_excess - interviews_redistributed

    # Create statistics about the redistribution process
    stats = {
        'total_excess': total_excess,
        'clusters_constrained': df['Is_Constrained'].sum(),
        'clusters_receiving': df['Received_Redistribution'].sum(),
        'interviews_redistributed': interviews_redistributed,
        'interviews_lost': interviews_lost,
        'insufficient_capacity': interviews_lost > 0
    }

    return df, stats


def validate_sampling_parameters(params):
    """Validate sampling parameters."""
    try:
        # Check value ranges
        if not (0 < params['confidence_level'] < 1):
            raise ValueError("Confidence level must be between 0 and 1")
        if not (0 < params['margin_of_error'] < 1):
            raise ValueError("Margin of error must be between 0 and 1")
        if params['design_effect'] < 1:
            raise ValueError(
                "Design effect must be greater than or equal to 1")
        if params['interviews_per_cluster'] < 1:
            raise ValueError("Interviews per cluster must be greater than 0")
        if not (0 <= params['reserve_percentage'] <= 1):
            raise ValueError("Reserve percentage must be between 0 and 1")
        if not (0 < params['probability'] < 1):
            raise ValueError("Probability must be between 0 and 1")

        return True
    except Exception as e:
        st.error(f"Invalid sampling parameters: {str(e)}")
        return False


def calculate_summary_statistics(df_sample, df_master, col_config):
    """Calculate summary statistics for the sampling."""
    try:
        stats = {
            'total_sample': int(df_sample['Sample'].sum()),
            'total_with_reserve': int(df_sample['Sample_with_reserve'].sum()),
            'total_clusters': int(df_sample['Clusters visited'].sum()),
            'coverage_percentage': (df_sample['Sample'].sum() /
                                    df_sample['Population (HH)'].sum()) * 100,
            'total_sites': len(df_master),
            'total_population': df_master[col_config['master_data']['households']].sum(),
            'total_admin3': len(df_master[col_config['master_data']['admin3']].unique()),
            'total_strata': len(df_master[col_config['master_data']['strata']].unique())
        }
        return stats
    except Exception as e:
        st.error(f"Error calculating summary statistics: {str(e)}")
        return None
