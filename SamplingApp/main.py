from utils import (
    calculate_sample,
    create_sample_data,
    process_sampling,
    prepare_download_file,
    process_grouped_data,
    update_main_display,
    update_render_main_tab,
    load_master_data_with_uid,
    display_replacement_summary  # Add this import
)

from config import PAGE_CONFIG, DEFAULT_SAMPLING_PARAMS, inject_custom_css
import pandas as pd
import streamlit as st
import math
from datetime import datetime, timedelta
import io

# Set page config
st.set_page_config(**PAGE_CONFIG)


def render_about_tab():
    """Render the about tab content."""
    st.title("About PPS Sampling Calculator")
    st.markdown("""
    ### Overview
    The PPS (Probability Proportional to Size) Sampling Calculator is a tool designed to help field teams calculate appropriate sample sizes for surveys and assessments.
    ### Features
    - Automated sample size calculation
    - Support for stratified sampling
    - Reserve sample calculation
    - Cluster-based sampling approach
    - Excel file export functionality
    ### How to Use
    1. Upload your Excel file containing population data
    2. Configure your columns to match required fields
    3. Set your sampling parameters
    4. Click calculate to generate your sample
    ### Contact
    For support or questions, please contact [dtmoperationsupport@iom.int]
    ### Version
    Current Version: 1.1.0
    """)


def render_help_tab(sampling_params=None):
    """Render the help tab content."""
    st.title("Help & Documentation")

    # Initialize sampling_params as an empty dict if it's None
    if sampling_params is None:
        sampling_params = {}

    # Documentation Links Section
    # st.markdown("""
    # ### Quick Links
    # - [📘 Official Documentation](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp)
    # - [📊 Example Datasets](https://github.com/Otomisin/PortFScripts/raw/main/SamplingApp/assets/EA_Sampling_Demo_Data.xlsx)
    # - [🔧 Report Issues](https://github.com/Otomisin/PortFScripts/issues)
    # - [📧 Contact Support](mailto:dtmoperationsupport@iom.int)
    # """)

    with st.expander("Column Configuration Help", expanded=True):
        st.markdown("""
        # Column Configuration Guide

        - **Site Name Column**: Select the column containing the Primary Sampling Unit (PSU) names.
          This is typically the village or site name where sampling will occur.

        - **PSU ID Column**: Select the column containing unique identifiers for each Primary
          Sampling Unit (PSU) or Enumeration Area. This ID must be unique for each sampling location.

        - **Households Population**: Select the column containing the number of households in each location.
          This is your population size for sampling calculations.

        - **Admin Column**: Select the column containing administrative boundaries above the PSU level
          (e.g., district, county). This is used for stratification and geographical distribution of samples.

        - **Strata Column**: Select the column used for stratification. This defines how the population
          is divided into distinct groups for sampling purposes. e.g IDP, Non-IDPs or Returnees
        """)

    with st.expander("Sampling Parameters Help", expanded=False):
        st.markdown("""
        ### Sampling Parameters Guide

        - **Confidence Level**: The probability that the sample accurately represents the population
          (typically 0.90 or 0.95)

        - **Margin of Error**: The maximum expected difference between the true population value and
          the sample estimate (typically 0.05 or 0.10)

        - **Design Effect**: Adjustment factor that accounts for the complexity of the sampling design
          (typically 1.5-2.0)

        - **Interviews per Cluster**: Number of interviews to be conducted in each selected cluster

        - **Reserve Percentage**: Additional sample size to account for non-response or invalid data
          (typically 10-20%)

        - **Probability**: The expected proportion of the characteristic being measured
          (use 0.5 if unknown)
        """)

    with st.expander("Results Interpretation", expanded=False):
        st.markdown("""
            ### Understanding Your Results

            #### Sampling Summary Metrics
            - **Total Sample Size**: Number of households to be sampled before adding reserve samples
            - **Sample with Reserve**: Total sample size including additional reserve samples to account
              for non-response
            - **Total Clusters**: Number of distinct locations where sampling will take place
            - **Sample Coverage**: Percentage of the total population included in the sample

            #### Output Data
            - **Seelcted Sites**: Shows the final selection of clusters and their corresponding
              sample sizes
            - **Sample Data**: Displays the breakdown of samples by strata and administrative areas
            """)

    # Remove the duplicate "Replacement PSUs" expander from here
    # This is now handled in the render_sidebar function

    with st.expander("Capacity Constraints Feature", expanded=False):
        st.markdown("""
        #### What are Capacity Constraints?

        Capacity constraints are a safeguard in the sampling process that prevents assigning more interviews to a location than is logically possible based on the number of households available. Without capacity constraints, some sampling locations might be assigned more interviews than there are households to interview, which can create practical problems for field teams.

        #### When to Use Capacity Constraints
        You should enable capacity constraints when:
        - You're working with small settlements or clusters that have limited households
        - Your data contains locations with highly variable population sizes
        - You want to ensure your sampling plan is practically implementable in the field
        - You need to avoid over-sampling in any specific location

        #### Constraint Options

        **1. No Constraints (None)**
        - No adjustments to interview targets are made
        - Interview targets may exceed the number of households in some locations
        - Useful only when you're confident that household counts are significantly underestimated

        **2. Capped**
        - Interview targets are strictly capped at the exact household count
        - Ensures you never assign more interviews than available households
        - Excess interviews are redistributed to other locations within the same stratum
        - Best for accurate household data where you want strict adherence to household limits

        **3. Reduction Factor**
        - Caps interview targets at a percentage of the household count (e.g., 70%)
        - Creates a buffer to account for non-response, ineligibility, or unavailability
        - More conservative approach that prevents exhausting all households in a location
        - Recommended for most field situations to maintain sampling integrity

        #### How Redistribution Works
        When interview targets exceed capacity constraints:
        1. The system identifies affected clusters ("constrained clusters")
        2. Excess interviews are removed from constrained clusters
        3. These interviews are redistributed proportionally to other clusters within the same stratum
        4. The distribution maintains the overall sample size while respecting household capacity limits
        5. If redistribution isn't possible within a stratum, you'll receive a notification

        #### Example
        If a cluster has 20 households and your interview target is 25:
        - With **No Constraints**: Target remains 25 (potential field implementation issues)
        - With **Capped**: Target reduced to 20, with 5 interviews redistributed
        - With **Reduction Factor (70%)**: Target reduced to 14, with 11 interviews redistributed

        #### Best Practices
        - Always enable capacity constraints for field implementation
        - Use "Capped" when household data is highly accurate
        - Use "Reduction Factor" when household data might have inaccuracies or for conservative sampling
        - Start with a 70% reduction factor for most situations
        - Review the sampling output carefully to ensure the redistribution meets your needs
        """)

    with st.expander("Additional Resources", expanded=False):
        st.markdown("""
        ### Additional Resources and Templates

        #### Sample Templates
        - [📝 Download Sample Master List Template](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp/assets)
        - [📊 View Sample Results](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp/others)

        #### Training Materials
        - [📚 PPS Sampling Methodology Guide](https://github.com/Otomisin/PortFScripts/blob/main/SamplingApp/README.md)
        - [🎥 Video Tutorial](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp)

        #### Support
        Need help? Contact our support team:
        - Email: [dtmoperationsupport@iom.int](mailto:dtmoperationsupport@iom.int)
        - GitHub: [Report an Issue](https://github.com/Otomisin/PortFScripts/issues)
        """)


def render_sidebar():
    """Render the sidebar components with sheet-based column selection."""
    st.sidebar.image(
        'https://raw.githubusercontent.com/Otomisin/c-practise/main/DTM-Dash/IOMlogo.png', width=200)

    # Upload section
    st.sidebar.header("⬆️ 1. Upload Data")
    uploaded_file = st.sidebar.file_uploader(
        "Choose an Excel file", type=['xlsx'])

    # Initialize return values
    column_config = None
    sampling_params = None

    if uploaded_file is not None:
        try:
            # Get all sheet names
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names

            # Store sheet names in session state
            st.session_state.sheet_names = sheet_names

            # Select the sheet
            st.sidebar.header("📑 Sheet Selection")
            selected_sheet = st.sidebar.selectbox(
                "Select Sheet",
                options=sheet_names,
                index=sheet_names.index(
                    "Master List") if "Master List" in sheet_names else 0,
                key="selected_sheet"
            )

            # Only after sheet selection, read the data and get columns
            df_master = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            columns = df_master.columns.tolist()

            # Store in session state
            st.session_state.current_columns = columns

            # Column configuration
            st.sidebar.header("⚙️ 2. Column Configuration")
            with st.sidebar.expander("Expand to see needed variables"):
                # Column selection dropdowns - only using columns from the selected sheet
                site_name_col = st.selectbox(
                    "Site Name Column",
                    help="This Primary Sampling Unit name...",
                    options=columns,
                    index=0
                )

                site_id_col = st.selectbox(
                    "PSU ID Column",
                    help="This is the unique Primary Sampling Unit ID, Enumeration Area ID...",
                    options=columns,
                    # Default to second column if it exists
                    index=min(1, len(columns)-1)
                )

                households_col = st.selectbox(
                    "Households Population",
                    help="This is the population figure...",
                    options=columns,
                    # Default to third column if it exists
                    index=min(2, len(columns)-1)
                )

                admin3_col = st.selectbox(
                    "Admin Column",
                    help="This is admin for representation ...",
                    options=columns,
                    # Default to fourth column if it exists
                    index=min(3, len(columns)-1)
                )

                strata_col = st.selectbox(
                    "Strata Column",
                    options=columns,
                    # Default to fifth column if it exists
                    index=min(4, len(columns)-1)
                )

                # Store the column configuration
                column_config = {
                    'master_data': {
                        'site_name': site_name_col,
                        'site_id': site_id_col,
                        'households': households_col,
                        'admin3': admin3_col,
                        'strata': strata_col
                    }
                }

                # Basic validation check - just make sure we don't have duplicates
                selected_columns = [site_name_col, site_id_col,
                                    households_col, admin3_col, strata_col]
                if len(selected_columns) != len(set(selected_columns)):
                    st.warning(
                        "Warning: You have selected the same column for multiple fields")

        except Exception as e:
            st.sidebar.error(f"Error loading sheet data: {str(e)}")
            return uploaded_file, None, None

        # Sampling parameters
        st.sidebar.header("🔍 3. Sampling Parameters",
                          help="Define the Sampling parameters")
        with st.sidebar.expander("Sampling Configuration", expanded=True):
            sampling_params = {
                'confidence_level': st.slider(
                    "Confidence Level",
                    min_value=0.8,
                    max_value=0.99,
                    value=DEFAULT_SAMPLING_PARAMS['confidence_level'],
                    step=0.01,
                    help="Select the confidence level for your sample"
                ),
                'margin_of_error': st.slider(
                    "Margin of Error",
                    min_value=0.01,
                    max_value=0.20,
                    value=DEFAULT_SAMPLING_PARAMS['margin_of_error'],
                    step=0.01,
                    help="Select the acceptable margin of error"
                ),
                'design_effect': st.number_input(
                    "Design Effect",
                    min_value=1.0,
                    max_value=5.0,
                    value=DEFAULT_SAMPLING_PARAMS['design_effect'],
                    step=0.1
                ),
                'interviews_per_cluster': st.number_input(
                    "Interviews per Cluster",
                    min_value=1,
                    max_value=50,
                    value=DEFAULT_SAMPLING_PARAMS['interviews_per_cluster'],
                    help="Enter the number of interviews to conduct per cluster"
                ),
                'reserve_percentage': st.slider(
                    "Reserve Percentage",
                    min_value=0.0,
                    max_value=0.5,
                    value=DEFAULT_SAMPLING_PARAMS['reserve_percentage'],
                    step=0.01,
                    help="Select the percentage of reserve samples"
                ),
                'probability': st.slider(
                    "Probability",
                    min_value=0.0,
                    max_value=1.0,
                    value=DEFAULT_SAMPLING_PARAMS['probability'],
                    step=0.01,
                    help="Select the probability threshold"
                )
            }

            # Random seed configuration
            use_random_seed = st.checkbox("Set Random Seed")
            if use_random_seed:
                sampling_params['random_seed'] = st.number_input(
                    "Random Seed Value",
                    min_value=0,
                    value=42
                )

        with st.sidebar.expander("Capacity Constraints", expanded=True):
            use_capacity_constraints = st.checkbox(
                "Enable Capacity Constraints",
                value=True,
                help="Ensure interviews don't exceed household population in any cluster"
            )

            # Replace the adjustment type radio with a more straightforward selection
            if use_capacity_constraints:
                capacity_adjustment_type = st.radio(
                    "Capacity Constraint Type",
                    options=["None", "Capped", "Reduction Factor"],
                    index=1,  # Default to "Capped"
                    help="Choose how to handle cases where interview targets exceed household counts"
                )

                # Show description based on selected option
                if capacity_adjustment_type == "None":
                    st.info(
                        "No adjustments will be made. Sampling will proceed even if interview targets exceed household counts.")
                elif capacity_adjustment_type == "Capped":
                    st.info(
                        "Interview targets will be strictly capped at the household count for each cluster.")
                elif capacity_adjustment_type == "Reduction Factor":
                    reduction_factor = st.slider(
                        "Reduction Factor (%)",
                        min_value=5,
                        max_value=95,
                        value=70,
                        step=5,
                        help="Set maximum percentage of households to sample in a cluster (e.g., 70% means sample at most 70% of households)"
                    )

                    # Example calculation to show the user
                    example_households = 20
                    example_reduced = math.floor(
                        example_households * (reduction_factor / 100))
                    st.info(
                        f"Example: For a cluster with {example_households} households, a maximum of {example_reduced} interviews would be allocated.")

                    # Add to sampling_params
                    sampling_params['reduction_factor'] = reduction_factor / 100.0

            # Add to sampling_params
            sampling_params['use_capacity_constraints'] = use_capacity_constraints
            sampling_params['capacity_adjustment_type'] = capacity_adjustment_type if use_capacity_constraints else "None"

        # Add the Replacement PSUs expander here, right after Capacity Constraints
        with st.sidebar.expander("Replacement PSUs", expanded=True):
            use_replacement_psus = st.checkbox(
                "Generate Replacement PSUs",
                value=False,
                help="Generate backup PSUs in case primary ones are inaccessible"
            )

            if use_replacement_psus:
                replacement_percentage = st.slider(
                    "Replacement Percentage",
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=5,
                    help="Percentage of primary PSUs to generate as replacements"
                )

                st.info(
                    f"The system will generate approximately {replacement_percentage}% additional PSUs as backups."
                )

                # Add to sampling_params
                sampling_params['use_replacement_psus'] = use_replacement_psus
                sampling_params['replacement_percentage'] = replacement_percentage / 100.0

        # Calculate button
        st.sidebar.header("🔢 4. Calculate")
        # The real button is in the main_tab function

    return uploaded_file, column_config, sampling_params


def render_main_tab(uploaded_file, column_config, sampling_params):
    """
    Render the main tab content with minimal initial calculations.
    """
    st.title("PPS Sampling Calculator")

    if uploaded_file is None:
        st.info("Please upload an Excel file to begin.")
        return

    try:
        # Check if sheet is selected
        if 'selected_sheet' not in st.session_state:
            st.info("Please select a sheet in the sidebar.")
            return

        selected_sheet = st.session_state.selected_sheet

        # Read the data based on selected sheet and add UniqueID column
        df_master = load_master_data_with_uid(uploaded_file, selected_sheet)

        if df_master is None:
            st.error("Failed to load data. Please check your file and try again.")
            return

        # Always show the total rows metric since it doesn't depend on column configuration
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", len(df_master))

        # Display data preview
        with st.expander("Preview Selected Sheet", expanded=True):
            st.subheader(f"Data Preview: {selected_sheet}")
            preview_df = df_master.copy()
            st.dataframe(preview_df, use_container_width=True, height=300)

        # Only show additional metrics if column configuration is complete
        if column_config is None:
            st.info("Please configure the columns in the sidebar.")
            return

        # Validate that selected columns exist in the dataframe
        missing_columns = [
            f"{col_key} ({col_name})" for col_key, col_name in column_config['master_data'].items()
            if col_name not in df_master.columns
        ]

        if missing_columns:
            st.warning(
                f"The following configured columns are missing from your data: {', '.join(missing_columns)}")
            st.info(
                "Please correct your column configuration before calculating samples.")
            return

        # Now that we know the column configuration is valid, display additional metrics
        with col2:
            site_id_col = column_config['master_data']['site_id']
            try:
                psu_count = df_master[site_id_col].nunique()
                st.metric("Total PSU", psu_count)
            except Exception as e:
                st.metric("Total PSU", "Error")
                st.warning(f"Error counting unique PSU IDs: {str(e)}")

        with col3:
            households_col = column_config['master_data']['households']
            try:
                household_values = pd.to_numeric(
                    df_master[households_col], errors='coerce')
                total_pop = household_values.sum()
                st.metric("Total Population (HH)", f"{total_pop:,}")
            except Exception as e:
                st.metric("Total Population (HH)", "Error")
                st.warning(f"Error calculating total population: {str(e)}")

        with col4:
            strata_col = column_config['master_data']['strata']
            try:
                strata_count = df_master[strata_col].nunique()
                st.metric("Total Strata", strata_count)
            except Exception as e:
                st.metric("Total Strata", "Error")
                st.warning(f"Error counting strata: {str(e)}")

        # Create a placeholder for the summary anchor
        summary_anchor = st.empty()

        # Process sampling if calculate button is clicked
        if st.sidebar.button("Calculate Random Sampling", type="primary", use_container_width=True):
            numeric_data = pd.to_numeric(
                df_master[households_col], errors='coerce')

            if numeric_data.isna().all():
                st.error(
                    f"Households column '{households_col}' contains no numeric data. Please select a different column.")
                return

            if numeric_data.isna().any():
                non_numeric_count = numeric_data.isna().sum()
                st.warning(
                    f"Found {non_numeric_count} non-numeric values in '{households_col}' column. These will be treated as 0.")
                df_master[households_col] = numeric_data.fillna(0)

            with st.spinner("Calculating samples..."):
                df_sample = create_sample_data(df_master, column_config)

                if df_sample is not None and not df_sample.empty:
                    df_sample['Sample'] = df_sample['Population (HH)'].apply(
                        lambda pop: calculate_sample(pop, sampling_params)
                    )
                    df_sample['Sample_with_reserve'] = df_sample['Sample'].apply(
                        lambda x: math.ceil(
                            x * (1 + sampling_params['reserve_percentage']))
                    )
                    df_sample['Clusters visited'] = df_sample['Sample_with_reserve'].apply(
                        lambda x: math.ceil(
                            x / sampling_params['interviews_per_cluster'])
                    )

                    st.divider()
                    with summary_anchor:
                        st.subheader("Overall Sampling Summary")

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Samples without Reserve",
                                      f"{int(df_sample['Sample'].sum()):,}")
                        with col2:
                            st.metric(
                                "Sample with Reserve", f"{int(df_sample['Sample_with_reserve'].sum()):,}")
                        with col3:
                            st.metric(
                                "Total Clusters", f"{int(df_sample['Clusters visited'].sum()):,}")
                        with col4:
                            coverage = (df_sample['Sample'].sum(
                            ) / df_sample['Population (HH)'].sum()) * 100
                            st.metric("Overall Coverage", f"{coverage:.1f}%")

                    sampled_data = process_sampling(
                        df_master, df_sample, sampling_params, column_config)

                    # Calculate actual interview totals for primary and replacement PSUs
                    primary_interviews = 0
                    replacement_interviews = 0

                    if 'PSU_Type' in sampled_data.columns:
                        # Find the target column dynamically
                        target_col = next((col for col in sampled_data.columns if col.startswith(
                            'Interview_TARGET_')), None)

                        if target_col:
                            primary_data = sampled_data[sampled_data['PSU_Type']
                                                        == 'Primary']
                            replacement_data = sampled_data[sampled_data['PSU_Type']
                                                            == 'Replacement']

                            if not primary_data.empty:
                                primary_interviews = int(
                                    primary_data[target_col].sum())

                            if not replacement_data.empty:
                                replacement_interviews = int(
                                    replacement_data[target_col].sum())

                            # Display these values if we have replacement PSUs
                            if not replacement_data.empty:
                                total_interviews = primary_interviews + replacement_interviews

                                # Add new row of metrics if we have replacement PSUs
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Primary PSU Interviews",
                                              f"{primary_interviews:,}")
                                with col2:
                                    st.metric("Replacement PSU Interviews",
                                              f"{replacement_interviews:,}")
                                with col3:
                                    st.metric("Total Interviews",
                                              f"{total_interviews:,}")
                                # Leave the 4th column empty for alignment

                    # Display replacement PSU issues summary if applicable
                    if sampling_params.get('use_replacement_psus', False) and 'replacement_issues' in st.session_state and st.session_state['replacement_issues']:
                        st.divider()
                        st.subheader("Replacement PSUs Status")
                        display_replacement_summary(df_sample)

                    # IMPROVED DETAILED RESULTS SECTION
                    st.subheader("Detailed Results")

                    # Display capacity constraint information in a container to keep it separate
                    constraint_container = st.container()
                    with constraint_container:
                        # Display capacity constraint settings if enabled
                        if sampling_params.get('use_capacity_constraints', False):
                            with st.expander("Capacity Constraint Settings", expanded=True):
                                st.write("**Capacity Constraints:** Enabled")

                                # Show appropriate adjustment type based on selection
                                adjustment_type = sampling_params.get(
                                    'capacity_adjustment_type', "None")
                                st.write(
                                    f"**Adjustment Type:** {adjustment_type}")

                                if adjustment_type == "Reduction Factor":
                                    reduction_factor = sampling_params.get(
                                        'reduction_factor', 0.7) * 100
                                    st.write(
                                        f"**Reduction Factor:** {reduction_factor:.0f}%")
                                    st.write(
                                        f"*Maximum interviews limited to {reduction_factor:.0f}% of household count*")
                                elif adjustment_type == "Capped":
                                    st.write(
                                        "**Strict Limit:** Interviews cannot exceed household count")
                                elif adjustment_type == "None":
                                    st.write(
                                        "**No Constraints:** No adjustments will be made to interview targets")

                                # After sampling is complete, show constraint summary
                                if 'has_excess_interviews' in st.session_state and st.session_state['has_excess_interviews']:
                                    excess_count = st.session_state.get(
                                        'excess_interview_count', 0)

                                    if excess_count > 0:
                                        if adjustment_type == "None":
                                            st.warning(
                                                f"⚠️ **{excess_count}** clusters have interview targets exceeding household counts. No constraints were applied.")
                                        else:
                                            total_constrained = st.session_state.get(
                                                'total_constrained_clusters', 0)
                                            total_clusters = st.session_state.get(
                                                'total_clusters', 0)

                                            if total_constrained > 0:
                                                st.info(
                                                    f"**{total_constrained}** out of **{total_clusters}** selected clusters were constrained due to household capacity limits.")

                                                # Display additional redistribution stats if available
                                                if 'constraint_stats' in st.session_state:
                                                    total_excess = sum(
                                                        stats.get(
                                                            'total_excess', 0)
                                                        for stats in st.session_state.get('constraint_stats', {}).values()
                                                    )

                                                    total_redistributed = sum(
                                                        stats.get(
                                                            'interviews_redistributed', 0)
                                                        for stats in st.session_state.get('constraint_stats', {}).values()
                                                    )

                                                    total_lost = sum(
                                                        stats.get(
                                                            'interviews_lost', 0)
                                                        for stats in st.session_state.get('constraint_stats', {}).values()
                                                    )

                                                    st.write(
                                                        f"**Total excess interviews:** {total_excess}")
                                                    st.write(
                                                        f"**Successfully redistributed:** {total_redistributed} interviews")

                                                    if total_lost > 0:
                                                        st.error(
                                                            f"**Unable to redistribute:** {total_lost} interviews due to insufficient capacity")
                        elif 'capacity_warning_needed' in st.session_state and st.session_state['capacity_warning_needed']:
                            # This handles the case where constraints are disabled but there are clusters exceeding capacity
                            excess_count = st.session_state.get(
                                'excess_interview_count', 0)
                            # if excess_count > 0:
                            #     st.warning(f"⚠️ **{excess_count} clusters** have interview targets exceeding household counts. Consider enabling capacity constraints to address this.")

                    # Stratum-specific summaries in a more compact format
                    with st.expander("📊 Stratum-Specific Summaries", expanded=True):
                        summary_data = [
                            {
                                'Stratum': stratum,
                                'Population': f"{int(df_sample[df_sample['Stratum'] == stratum]['Population (HH)'].sum()):,}",
                                'Sample Size': f"{int(df_sample[df_sample['Stratum'] == stratum]['Sample'].sum()):,}",
                                'With Reserve': f"{int(df_sample[df_sample['Stratum'] == stratum]['Sample_with_reserve'].sum()):,}",
                                'Clusters': f"{int(df_sample[df_sample['Stratum'] == stratum]['Clusters visited'].sum()):,}",
                                'Coverage (%)': f"{(df_sample[df_sample['Stratum'] == stratum]['Sample'].sum() / df_sample[df_sample['Stratum'] == stratum]['Population (HH)'].sum()) * 100:.1f}%",
                                'Interviews/Cluster': sampling_params['interviews_per_cluster']
                            } for stratum in df_sample['Stratum'].unique()
                        ]

                        # Convert to DataFrame for display
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(
                            summary_df,
                            use_container_width=True,
                            # Adjust height based on number of strata
                            height=80 + (len(summary_data) * 35)
                        )

                    if not sampled_data.empty:
                        try:
                            # Use the modified update_main_display function to show the results
                            # This now places capacity warnings above the tables
                            grouped_data, sample_display = update_main_display(
                                sampled_data, df_sample, column_config, sampling_params)

                            # Add a divider before download section
                            st.divider()

                            # Download section
                            st.subheader("Download Results")
                            output = prepare_download_file(
                                grouped_data, sample_display, df_master, column_config, sampling_params)
                            if output:
                                col1, col2, col3 = st.columns([1, 2, 1])
                                with col2:
                                    st.download_button(
                                        label="📥 Download Complete Results (Excel)",
                                        data=output.getvalue(),
                                        file_name=f"sampling_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                        except Exception as e:
                            st.error(f"Error displaying results: {str(e)}")
                            # Show the full traceback for better debugging
                            st.exception(e)
                    else:
                        st.error("No data was generated after sampling.")
                else:
                    st.error(
                        "Failed to create sample data. Please check your input data and column configuration.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)  # Show the full traceback for better debugging


def main():
    inject_custom_css()

    if 'column_names' not in st.session_state:
        st.session_state.column_names = []
    if 'sheet_names' not in st.session_state:
        st.session_state.sheet_names = []
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Main"

    about_tab, main_tab, help_tab = st.tabs(["About", "Main", "Help"])

    uploaded_file, column_config, sampling_params = render_sidebar()

    if column_config and 'is_valid' in column_config:
        is_valid = column_config.pop('is_valid')
        if not is_valid:
            st.warning(
                "Please fix column configuration issues before proceeding")

    with about_tab:
        render_about_tab()
    with main_tab:
        render_main_tab(uploaded_file, column_config, sampling_params)
    with help_tab:
        render_help_tab(sampling_params)  # Pass sampling_params here


if __name__ == "__main__":
    main()
