import streamlit as st
import pandas as pd
import numpy as np
import math
from scipy.stats import chi2
import io
from datetime import datetime, timedelta
import pathlib

st.set_page_config(page_title="Sampling Calculator", layout="wide")

# UI Layout


def render_about_and_help():
    # Create tabs for main content, about, and help
    about_tab, main_tab, help_tab = st.tabs(["About", "Main", "Help"])

    #### ABOUT TAB ##############################
    with about_tab:
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
        Current Version: 1.0.0
        """)

    #### MAIN TAB ##############################
    with main_tab:
        st.title("PPS Sampling Calculator")

    @st.cache_data()  # Updated to use the built-in Streamlit caching
    # Function to load CSS from the 'assets' folder
    def load_css(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Load the external CSS
    css_path = pathlib.Path("assets/dtmstyle.css")
    load_css(css_path)

    # st.title("PPS Sampling Calculator")

    # Initialize session state for column names if not exists
    if 'column_names' not in st.session_state:
        st.session_state.column_names = []
    if 'sheet_names' not in st.session_state:
        st.session_state.sheet_names = []

    def calculate_sample(population, params):
        """Calculate sample size based on parameters."""
        chinv = chi2.ppf(params['confidence_level'], df=1)
        return math.ceil(
            (chinv * population * params['probability'] * (1 - params['probability'])) /
            (((params['margin_of_error'] ** 2) * (population - 1)) +
             (chinv * params['probability'] * (1 - params['probability']))) *
            params['design_effect']
        )

    def create_sample_data(df, col_config):
        """Create sample data from master list by aggregating required information."""
        df['Strata_name'] = df[col_config['master_data']['strata']] + \
            '_' + df[col_config['master_data']['admin3']]
        sample_data = df.groupby([
            col_config['master_data']['admin3'],
            col_config['master_data']['strata'],
            'Strata_name'
        ]).agg({
            col_config['master_data']['households']: 'sum'
        }).reset_index()
        sample_data.columns = ['Admin3', 'Stratum',
                               'Strata_name', 'Population (HH)']
        return sample_data

    def process_sampling(df, sample_data, params, col_config):
        """Process sampling logic for each stratum."""
        result = []
        dynamic_target_col = f"Interview_TARGET_{col_config['master_data']['households']}"

        for _, strata_row in sample_data.iterrows():
            cluster_name = strata_row['Admin3']
            filtered_df = df[df[col_config['master_data']
                                ['admin3']] == cluster_name].copy()

            if filtered_df.empty:
                st.warning(
                    f"No data found for cluster '{cluster_name}' in the master list. Skipping...")
                continue

            filtered_df['Cumulative_HH'] = filtered_df[col_config['master_data']
                                                       ['households']].cumsum()
            filtered_df['Lower bound'] = filtered_df['Cumulative_HH'] - \
                filtered_df[col_config['master_data']['households']] + 1
            filtered_df['Selections'] = 0

            num_draws = int(math.ceil(
                float(strata_row['Sample_with_reserve']) / params['interviews_per_cluster']))

            try:
                lower_bound = int(filtered_df['Lower bound'].min())
                upper_bound = int(filtered_df['Cumulative_HH'].max() + 1)

                random_numbers = np.random.randint(
                    lower_bound,
                    upper_bound,
                    size=num_draws
                )
            except ValueError as e:
                st.error(
                    f"Error generating random numbers for cluster '{cluster_name}': {e}")
                continue

            for rand in random_numbers:
                filtered_df.loc[
                    (filtered_df['Lower bound'] <= rand) &
                    (filtered_df['Cumulative_HH'] >= rand),
                    'Selections'
                ] += 1

            filtered_df[dynamic_target_col] = filtered_df['Selections'] * \
                params['interviews_per_cluster']
            result.append(filtered_df)

        return pd.concat(result, ignore_index=True) if result else pd.DataFrame()

    # Sidebar file upload first
    st.sidebar.image(
        'https://raw.githubusercontent.com/Otomisin/c-practise/main/DTM-Dash/IOMlogo.png', width=200)
    st.sidebar.header("1. Upload Data")
    with st.sidebar.expander("Expand to see needed variables"):
        st.markdown(
            """
            <style>
                .sidebar-text {
                    font-size: small;
                    color: gray;
                }
            </style>
            <div class="sidebar-text">
                Upload your Excel file containing the survey data. The file should include:
                <ul>
                    <li>Site/location information</li>
                    <li>Population data (households)</li>
                    <li>Administrative boundaries</li>
                    <li>Stratification variables</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    uploaded_file = st.sidebar.file_uploader(
        "Choose an Excel file", type=['xlsx'])

    if uploaded_file is not None:
        try:
            # Get all sheet names from the Excel file
            xls = pd.ExcelFile(uploaded_file)
            st.session_state.sheet_names = xls.sheet_names

            # Add sheet selection dropdown
            selected_sheet = st.sidebar.selectbox(
                "Select Sheet",
                options=st.session_state.sheet_names,
                index=st.session_state.sheet_names.index(
                    "Master List") if "Master List" in st.session_state.sheet_names else 0
            )

            # Read the selected sheet
            df_master = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.session_state.column_names = df_master.columns.tolist()

            # Sidebar for column configuration
            st.sidebar.header("2. Column Configuration",
                              help="This section allows you to customize how your columns are displayed")
            st.sidebar.markdown("""
            <div style='font-size: small; color: gray;'>
            Select the respective colums:
            </div>
            """, unsafe_allow_html=True)

            # Dropdown selections for columns
            site_name_col = st.sidebar.selectbox("Site Name Column", help="This Primary Sampling Unit name...",
                                                 options=st.session_state.column_names,
                                                 index=st.session_state.column_names.index("village") if "village" in st.session_state.column_names else 0)

            site_id_col = st.sidebar.selectbox("PSU ID Column", help="This is the unique Primary Sampling Unit ID, Enumeration Area ID...",
                                               options=st.session_state.column_names,
                                               index=st.session_state.column_names.index("ssid") if "ssid" in st.session_state.column_names else 0)

            households_col = st.sidebar.selectbox("Households Column", help="This should be the column with the population figure...",
                                                  options=st.session_state.column_names,
                                                  index=st.session_state.column_names.index("idp_hh") if "idp_hh" in st.session_state.column_names else 0)

            admin3_col = st.sidebar.selectbox("Admin Column", help="This is the next higher level from the PSU Level...",
                                              options=st.session_state.column_names,
                                              index=st.session_state.column_names.index("Admin3") if "Admin3" in st.session_state.column_names else 0)

            strata_col = st.sidebar.selectbox("Strata Column", help="This is the column with the strata category.",
                                              options=st.session_state.column_names,
                                              index=st.session_state.column_names.index("strata") if "strata" in st.session_state.column_names else 0)

            # Column configuration dictionary
            COLUMN_CONFIG = {
                'master_data': {
                    'site_name': site_name_col,
                    'site_id': site_id_col,
                    'households': households_col,
                    'admin3': admin3_col,
                    'strata': strata_col
                }
            }

            # Sampling parameters in sidebar
            st.sidebar.header("3. Sampling Parameters",
                              help=" Define the Sampling paramters ")

            # Parameter inputs with preloaded values
            confidence_level = st.sidebar.slider(
                "Confidence Level", 0.8, 0.99, 0.9, 0.01)
            margin_of_error = st.sidebar.slider(
                "Margin of Error", 0.01, 0.20, 0.10, 0.01)
            design_effect = st.sidebar.number_input(
                "Design Effect", min_value=1.0, max_value=5.0, value=2.0, step=0.1)
            interviews_per_cluster = st.sidebar.number_input(
                "Interviews per Cluster", min_value=1, max_value=50, value=5)
            reserve_percentage = st.sidebar.slider(
                "Reserve Percentage", 0.0, 0.5, 0.1, 0.01)
            probability = st.sidebar.slider("Probability", 0.0, 1.0, 0.5, 0.01)

            # Random seed configuration
            use_random_seed = st.sidebar.checkbox(
                "Set Random Seed", help="Check if you want to make sampling reproduceable.")
            random_seed = None
            if use_random_seed:
                random_seed = st.sidebar.number_input(
                    "Random Seed Value", min_value=0, value=42, help="Pick a number to seed")

            # Calculate button in sidebar
            st.sidebar.header("4. Calculate")
            calculate_button = st.sidebar.button(
                "Calculate Random Sampling", type="primary", use_container_width=True)

            # Display summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Total Sites",
                    len(df_master),
                    help="Total number of sites in the dataset"
                )
            with col2:
                st.metric(
                    "Total Population (HH)",
                    f"{df_master[households_col].sum():,}",
                    help="Total number of households across all sites"
                )
            with col3:
                st.metric(
                    "Total Admin3 Areas",
                    len(df_master[admin3_col].unique()),
                    help="Number of unique Admin3 areas"
                )
            with col4:
                st.metric(
                    "Total Strata",
                    len(df_master[strata_col].unique()),
                    help="Number of unique strata"
                )

            # Display data info with wider layout
            st.subheader("Loaded Data Preview")
            st.text(
                "Here is a snippet of your data ===========================================================")
            st.dataframe(df_master, use_container_width=True, height=300)
            st.text(
                "Your Calculated table will be appear under here. ==========================================")

            if calculate_button:
                sampling_params = {
                    'confidence_level': confidence_level,
                    'margin_of_error': margin_of_error,
                    'design_effect': design_effect,
                    'interviews_per_cluster': interviews_per_cluster,
                    'reserve_percentage': reserve_percentage,
                    'probability': probability,
                    'random_seed': random_seed
                }

                # Set random seed if provided
                if random_seed is not None:
                    np.random.seed(random_seed)
                    st.info(f"Using random seed: {random_seed}")

                # Create sample data
                df_sample = create_sample_data(df_master, COLUMN_CONFIG)
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

                # Display sampling summary statistics
                st.subheader("Sampling Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Total Sample Size",
                        f"{int(df_sample['Sample'].sum()):,}",
                        help="Total number of households to be sampled (before reserve)"
                    )
                with col2:
                    st.metric(
                        "Sample with Reserve",
                        f"{int(df_sample['Sample_with_reserve'].sum()):,}",
                        help="Total sample size including reserve"
                    )
                with col3:
                    st.metric(
                        "Total Clusters",
                        f"{int(df_sample['Clusters visited'].sum()):,}",
                        help="Total number of clusters to be visited"
                    )
                with col4:
                    coverage = (df_sample['Sample'].sum() /
                                df_sample['Population (HH)'].sum()) * 100
                    st.metric(
                        "Sample Coverage",
                        f"{coverage:.1f}%",
                        help="Percentage of total population covered by sample"
                    )

                # Process data
                df_master = df_master[df_master[COLUMN_CONFIG['master_data']
                                                ['households']] > 0].copy()
                df_master['random'] = np.random.rand(len(df_master))
                df_master = df_master.sort_values(
                    by='random').reset_index(drop=True)

                # Process sampling
                sampled_data = process_sampling(
                    df_master, df_sample, sampling_params, COLUMN_CONFIG)

                if not sampled_data.empty:
                    # Group data
                    grouped_data = sampled_data.groupby(
                        [COLUMN_CONFIG['master_data']['admin3'],
                            COLUMN_CONFIG['master_data']['site_id']],
                        as_index=False
                    ).agg(
                        Selections=('Selections', 'sum'),
                        **{f"Interview_TARGET_{COLUMN_CONFIG['master_data']['households']}":
                           (f"Interview_TARGET_{COLUMN_CONFIG['master_data']['households']}", 'sum')}
                    )

                    # Display results with wider layout
                    st.subheader("Results")

                    tab1, tab2 = st.tabs(["Grouped Data", "Sample Data"])

                    with tab1:
                        st.write("Combined Grouped Data")
                        st.dataframe(
                            grouped_data, use_container_width=True, height=400)

                    with tab2:
                        st.write("Sample Data")
                        sample_display = df_sample[['Admin3', 'Sample', 'Sample_with_reserve',
                                                    'Stratum', 'Strata_name', 'Clusters visited']]
                        st.dataframe(sample_display,
                                     use_container_width=True, height=400)

                    # Download buttons
                    st.subheader("Download Results")

                    # Create Excel file in memory
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        grouped_data.to_excel(
                            writer, sheet_name='Combined Grouped Data', index=False)
                        sample_display.to_excel(
                            writer, sheet_name='Sample Data', index=False)

                    # Download button
                    st.download_button(
                        label="Download Excel file",
                        data=output.getvalue(),
                        file_name="sampling_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error(
                        "No data was generated after sampling. Please check your parameters and data.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please upload an Excel file to begin.")

    # Help and Documentation ############################
    with help_tab:
        st.title("Help & Documentation")

        with st.expander("Column Configuration Help", expanded=True):
            st.markdown("""
            ### Column Configuration Guide
            
            - **Site Name Column**: Select the column containing the Primary Sampling Unit (PSU) names. 
              This is typically the village or site name where sampling will occur.
            
            - **PSU ID Column**: Select the column containing unique identifiers for each Primary 
              Sampling Unit (PSU) or Enumeration Area. This ID must be unique for each sampling location.
            
            - **Households Column**: Select the column containing the number of households in each location. 
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
            - **Combined Grouped Data**: Shows the final selection of clusters and their corresponding 
              sample sizes
            - **Sample Data**: Displays the breakdown of samples by strata and administrative areas
            """)

        with st.expander("Troubleshooting", expanded=False):
            st.markdown("""
            ### Common Issues and Solutions
            
            1. **File Upload Issues**
               - Ensure your Excel file is in .xlsx format
               - Check that your file is not corrupted
               - Verify that required columns are present
            
            2. **Calculation Errors**
               - Verify that your population numbers are greater than zero
               - Check that your sampling parameters are within valid ranges
               - Ensure strata categories are correctly defined
            
            3. **Output Problems**
               - Make sure all required columns are properly mapped
               - Verify that your data contains no missing values in key fields
               - Check that your Excel file is not open in another program
            """)

    return main_tab


render_about_and_help()
