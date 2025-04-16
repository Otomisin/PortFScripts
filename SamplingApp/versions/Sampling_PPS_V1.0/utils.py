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


def create_sample_data(df, col_config):
    """
    Create sample data from master list with improved strata handling.
    """
    try:
        # Create strata name combining strata and admin3
        df['Strata_name'] = df[col_config['master_data']['strata']].astype(str) + '_' + \
            df[col_config['master_data']['admin3']].astype(str)

        # Group data by admin3, strata, and strata_name
        sample_data = df.groupby([
            col_config['master_data']['admin3'],
            col_config['master_data']['strata'],
            'Strata_name'
        ]).agg({
            col_config['master_data']['households']: 'sum'
        }).reset_index()

        # Rename columns for clarity
        sample_data.columns = [
            col_config['master_data']['admin3'],
            'Stratum',
            'Strata_name',
            'Population (HH)'
        ]

        # Sort by admin3 and stratum for consistency
        sample_data = sample_data.sort_values(
            [col_config['master_data']['admin3'], 'Stratum'])

        return sample_data

    except Exception as e:
        st.error(f"Error creating sample data: {str(e)}")
        return None


def process_sampling(df, sample_data, params, col_config):
    """
    Process sampling logic for each stratum with proper handling of multiple strata.

    Args:
        df (pd.DataFrame): Master data frame
        sample_data (pd.DataFrame): Prepared sample data with strata information
        params (dict): Sampling parameters
        col_config (dict): Column configuration

    Returns:
        pd.DataFrame: Processed sampling results
    """
    result = []
    dynamic_target_col = f"Interview_TARGET_{col_config['master_data']['households']}"

    try:
        # Set random seed if provided
        if 'random_seed' in params and params['random_seed'] is not None:
            np.random.seed(params['random_seed'])

        # Group by both admin3 and strata
        for _, strata_row in sample_data.iterrows():
            admin_col = col_config['master_data']['admin3']
            strata_col = col_config['master_data']['strata']

            # Filter by both admin3 and strata
            filtered_df = df[
                (df[admin_col] == strata_row[admin_col]) &
                (df[strata_col] == strata_row['Stratum'])
            ].copy()

            if filtered_df.empty:
                st.warning(
                    f"No data found for cluster '{strata_row[admin_col]}' and stratum '{strata_row['Stratum']}'. Skipping..."
                )
                continue

            # Calculate cumulative households within the stratum
            households_col = col_config['master_data']['households']
            filtered_df = filtered_df.sort_values(
                households_col, ascending=True)
            filtered_df['Cumulative_HH'] = filtered_df[households_col].cumsum()
            filtered_df['Lower_bound'] = filtered_df['Cumulative_HH'] - \
                filtered_df[households_col] + 1
            filtered_df['Selections'] = 0

            # Calculate number of draws needed for this stratum
            num_draws = int(math.ceil(
                float(strata_row['Sample_with_reserve']) /
                params['interviews_per_cluster']
            ))

            try:
                # Generate random numbers within stratum bounds
                lower_bound = int(filtered_df['Lower_bound'].min())
                upper_bound = int(filtered_df['Cumulative_HH'].max() + 1)

                if lower_bound >= upper_bound:
                    st.warning(
                        f"Invalid bounds for stratum '{strata_row['Stratum']}' in cluster '{strata_row[admin_col]}'. Skipping..."
                    )
                    continue

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
                filtered_df['Stratum'] = strata_row['Stratum']
                filtered_df['Strata_name'] = strata_row['Strata_name']

                result.append(filtered_df)

            except ValueError as e:
                st.error(
                    f"Error generating random numbers for stratum '{strata_row['Stratum']}' in cluster '{strata_row[admin_col]}': {str(e)}"
                )
                continue

        # Combine all results
        final_df = pd.concat(
            result, ignore_index=True) if result else pd.DataFrame()

        # Add summary columns
        if not final_df.empty:
            final_df['Total_Selected'] = final_df['Selections'].sum()
            final_df['Stratum_Selected'] = final_df.groupby(
                'Stratum')['Selections'].transform('sum')

        return final_df

    except Exception as e:
        st.error(f"Error processing sampling: {str(e)}")
        return pd.DataFrame()


def prepare_download_file(grouped_data, sample_display):
    """
    Prepare Excel file for download with separate sheets per stratum.

    Args:
        grouped_data (pd.DataFrame): Combined grouped data
        sample_display (pd.DataFrame): Sample data display

    Returns:
        BytesIO: Excel file buffer
    """
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get unique strata
            strata = sample_display['Stratum'].unique()

            for stratum in strata:
                # Filter data for current stratum
                stratum_grouped = grouped_data[grouped_data['Stratum'] == stratum].copy(
                )
                stratum_sample = sample_display[sample_display['Stratum'] == stratum].copy(
                )

                # Add metadata
                stratum_grouped.loc[-1] = ['Generated on:',
                                           timestamp, '', '', '']
                stratum_sample.loc[-1] = ['Generated on:',
                                          timestamp, '', '', '', '']

                # Write to separate sheets with stratum-specific names
                sheet_name_grouped = f'Grouped Data_{stratum}'[
                    :31]  # Excel sheet name limit
                sheet_name_sample = f'Sample Data_{stratum}'[
                    :31]    # Excel sheet name limit

                stratum_grouped.to_excel(
                    writer,
                    sheet_name=sheet_name_grouped,
                    index=False
                )

                stratum_sample.to_excel(
                    writer,
                    sheet_name=sheet_name_sample,
                    index=False
                )

            # Also include combined sheets for overview
            all_grouped = grouped_data.copy()
            all_sample = sample_display.copy()

            all_grouped.loc[-1] = ['Generated on:', timestamp, '', '', '']
            all_sample.loc[-1] = ['Generated on:', timestamp, '', '', '', '']

            all_grouped.to_excel(
                writer,
                sheet_name='Combined Grouped Data',
                index=False
            )

            all_sample.to_excel(
                writer,
                sheet_name='Combined Sample Data',
                index=False
            )

        return output

    except Exception as e:
        st.error(f"Error preparing download file: {str(e)}")
        return None
# New


# def process_grouped_data(sampled_data, col_config):
#     """
#     Process grouped data with stratum information.

#     Args:
#         sampled_data (pd.DataFrame): The sampled data
#         col_config (dict): Column configuration

#     Returns:
#         pd.DataFrame: Processed grouped data
#     """
#     grouped_data = sampled_data.groupby(
#         [
#             col_config['master_data']['admin3'],
#             col_config['master_data']['site_id'],
#             'Stratum'  # Add stratum to grouping
#         ],
#         as_index=False
#     ).agg({
#         'Selections': 'sum',
#         f"Interview_TARGET_{col_config['master_data']['households']}": 'sum'
#     })

#     return grouped_data
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


# New
def update_main_display(sampled_data, df_sample, col_config):
    """
    Update main display with stratum-specific information.

    Args:
        sampled_data (pd.DataFrame): The sampled data
        df_sample (pd.DataFrame): Sample data
        col_config (dict): Column configuration

    Returns:
        tuple: (grouped_data, sample_display)
    """
    try:
        # Process grouped data first
        grouped_data = process_grouped_data(sampled_data, col_config)

        if grouped_data.empty:
            st.error("No grouped data available to display")
            return pd.DataFrame(), pd.DataFrame()

        # Prepare sample display data
        admin_col_name = col_config['master_data']['admin3']
        sample_display = df_sample[[
            admin_col_name,
            'Sample',
            'Sample_with_reserve',
            'Stratum',
            'Strata_name',
            'Clusters visited'
        ]].copy()

        # Create tabs for display
        strata = df_sample['Stratum'].unique()
        tabs = st.tabs(
            ['All Data'] + [f'Stratum: {stratum}' for stratum in strata])

        # Display all data tab
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Combined Grouped Data")
                st.dataframe(
                    grouped_data, use_container_width=True, height=300)
            with col2:
                st.subheader("Combined Sample Data")
                st.dataframe(sample_display,
                             use_container_width=True, height=300)

        # Display stratum-specific tabs
        for i, stratum in enumerate(strata, 1):
            with tabs[i]:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(f"Grouped Data - {stratum}")
                    stratum_grouped = grouped_data[grouped_data['Stratum'] == stratum]
                    st.dataframe(stratum_grouped,
                                 use_container_width=True, height=300)
                with col2:
                    st.subheader(f"Sample Data - {stratum}")
                    stratum_sample = sample_display[sample_display['Stratum'] == stratum]
                    st.dataframe(stratum_sample,
                                 use_container_width=True, height=300)

        return grouped_data, sample_display

    except Exception as e:
        st.error(f"Error in update_main_display: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


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
