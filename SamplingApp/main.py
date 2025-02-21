from utils import (
    calculate_sample,
    create_sample_data,
    process_sampling,
    prepare_download_file,
    process_grouped_data,
    update_main_display

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
    Current Version: 1.0.0
    """)


def render_help_tab():
    """Render the help tab content."""
    st.title("Help & Documentation")

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
            - **Combined Grouped Data**: Shows the final selection of clusters and their corresponding 
              sample sizes
            - **Sample Data**: Displays the breakdown of samples by strata and administrative areas
            """)


def render_help_tab():
    """Render the help tab content."""
    st.title("Help & Documentation")

    # Documentation Links Section
    st.markdown("""
    ### Quick Links
    - [📘 Official Documentation](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp)
    - [📊 Example Datasets](https://github.com/Otomisin/PortFScripts/tree/main/SamplingApp/assets)
    - [🔧 Report Issues](https://github.com/Otomisin/PortFScripts/issues)
    - [📧 Contact Support](mailto:dtmoperationsupport@iom.int)
    """)

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
            - **Combined Grouped Data**: Shows the final selection of clusters and their corresponding 
              sample sizes
            - **Sample Data**: Displays the breakdown of samples by strata and administrative areas
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
    """Render the sidebar components and return user inputs."""
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
        # Column configuration
        st.sidebar.header("⚙️ 2. Column Configuration")
        with st.sidebar.expander("Expand to see needed variables"):
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                selected_sheet = st.selectbox(
                    "Select Sheet",
                    options=sheet_names,
                    index=sheet_names.index(
                        "Master List") if "Master List" in sheet_names else 0
                )

                df_master = pd.read_excel(
                    uploaded_file, sheet_name=selected_sheet)
                columns = df_master.columns.tolist()

                # Column selection dropdowns
                site_name_col = st.selectbox(
                    "Site Name Column",
                    help="This Primary Sampling Unit name...",
                    options=columns,
                    index=columns.index(
                        "village") if "village" in columns else 0
                )
                site_id_col = st.selectbox(
                    "PSU ID Column", help="This is the unique Primary Sampling Unit ID, Enumeration Area ID...",
                    options=columns,
                    index=columns.index("ssid") if "ssid" in columns else 0
                )
                households_col = st.selectbox(
                    "Households Population", help="This is the population figure...",
                    options=columns,
                    index=columns.index("idp_hh") if "idp_hh" in columns else 0
                )
                admin3_col = st.selectbox(
                    "Admin Column",
                    help="This is admin for representation ...",
                    options=columns,
                    index=columns.index("Admin3") if "Admin3" in columns else 0
                )
                strata_col = st.selectbox(
                    "Strata Column",
                    options=columns,
                    index=columns.index("strata") if "strata" in columns else 0
                )

                column_config = {
                    'master_data': {
                        'site_name': site_name_col,
                        'site_id': site_id_col,
                        'households': households_col,
                        'admin3': admin3_col,
                        'strata': strata_col
                    }
                }
            except Exception as e:
                st.error(f"Error in column configuration: {str(e)}")
                return None, None, None

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

        # # Calculate button
        # st.sidebar.header("🔢 4. Calculate")
        # calculate_button = st.sidebar.button(
        #     "Calculate Random Sampling",
        #     type="primary",
        #     use_container_width=True
        # )

    return uploaded_file, column_config, sampling_params


def render_main_tab(uploaded_file, column_config, sampling_params):
    """
    Render the main tab content with auto-focus on results and compact summaries.
    """
    st.title("PPS Sampling Calculator")

    if uploaded_file is None:
        st.info("Please upload an Excel file to begin.")
        return

    if column_config is None:
        st.error("Please configure the columns in the sidebar first.")
        return

    try:
        # Read the data
        df_master = pd.read_excel(uploaded_file)

        # Display initial metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sites", len(df_master))
        with col2:
            st.metric(
                "Total Population (HH)",
                f"{df_master[column_config['master_data']['households']].sum():,}"
            )
        with col3:
            st.metric(
                "Total Admin3 Areas",
                len(df_master[column_config['master_data']['admin3']].unique())
            )
        with col4:
            st.metric(
                "Total Strata",
                len(df_master[column_config['master_data']['strata']].unique())
            )

        # Display data preview with stratum information
        with st.expander("Preview Loaded Table"):
            st.subheader("Loaded Data Preview")
            preview_df = df_master.copy()
            st.dataframe(preview_df, use_container_width=True, height=300)

        # Create a placeholder for the summary anchor
        summary_anchor = st.empty()

        # Process sampling if calculate button is clicked
        if st.sidebar.button("Calculate Random Sampling", type="primary"):
            # Set active tab to Main
            st.session_state.active_tab = "Main"

            with st.spinner("Calculating samples..."):
                # Create sample data
                df_sample = create_sample_data(df_master, column_config)

                if df_sample is not None:
                    # Calculate samples for each stratum
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

                    # Display sampling summary with stratum breakdown
                    st.divider()

                    # Overall Summary with anchor
                    with summary_anchor:
                        st.markdown('<div id="summary-section"></div>',
                                    unsafe_allow_html=True)
                        st.subheader("Overall Sampling Summary")

                        # Add JavaScript to scroll to summary section
                        st.markdown("""
                            <script>
                                window.location.hash = "#summary-section";
                            </script>
                        """, unsafe_allow_html=True)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric(
                                "Total Sample Size",
                                f"{int(df_sample['Sample'].sum()):,}"
                            )
                        with col2:
                            st.metric(
                                "Sample with Reserve",
                                f"{int(df_sample['Sample_with_reserve'].sum()):,}"
                            )
                        with col3:
                            st.metric(
                                "Total Clusters",
                                f"{int(df_sample['Clusters visited'].sum()):,}"
                            )
                        with col4:
                            coverage = (df_sample['Sample'].sum() /
                                        df_sample['Population (HH)'].sum()) * 100
                            st.metric("Overall Coverage", f"{coverage:.1f}%")

                    # st.divider()
                    st.subheader("Detailed Results")
                    st.write("")  # Spacing
                    st.write("")  # Spacing

                    # Stratum-specific summaries in a more compact format
                    with st.expander("📊 Stratum-Specific Summaries", expanded=True):
                        # Create a summary DataFrame for clean display
                        summary_data = []
                        for stratum in df_sample['Stratum'].unique():
                            stratum_data = df_sample[df_sample['Stratum'] == stratum]
                            coverage = (stratum_data['Sample'].sum() /
                                        stratum_data['Population (HH)'].sum()) * 100

                            summary_data.append({
                                'Stratum': stratum,
                                'Population': f"{int(stratum_data['Population (HH)'].sum()):,}",
                                'Sample Size': f"{int(stratum_data['Sample'].sum()):,}",
                                'With Reserve': f"{int(stratum_data['Sample_with_reserve'].sum()):,}",
                                'Clusters': f"{int(stratum_data['Clusters visited'].sum()):,}",
                                'Coverage (%)': f"{coverage:.1f}%",
                                'Interviews/Cluster': sampling_params['interviews_per_cluster']
                            })

                        # Convert to DataFrame for display
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(
                            summary_df,
                            use_container_width=True,
                            # Adjust height based on number of strata
                            height=80 + (len(summary_data) * 35)
                        )

                    # Process the sampling
                    sampled_data = process_sampling(
                        df_master,
                        df_sample,
                        sampling_params,
                        column_config
                    )

                    st.divider()
                    # st.subheader("Detailed Results")
                    st.write("")  # Spacing
                    st.write("")  # Spacing

                    if not sampled_data.empty:
                        st.write("")  # Spacing
                        # st.divider()
                        # st.subheader("Detailed Results")

                        # Use the display function with proper parameters
                        grouped_data, sample_display = update_main_display(
                            sampled_data,
                            df_sample,
                            column_config
                        )

                        # Prepare and offer download
                        if not grouped_data.empty and not sample_display.empty:
                            # Add a divider before download button
                            st.divider()
                            st.subheader("Download Results")

                            output = prepare_download_file(
                                grouped_data, sample_display)
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
                        else:
                            st.error("Error processing sampling results.")
                    else:
                        st.error(
                            "No data was generated after sampling. Please check your parameters and data.")
                else:
                    st.error(
                        "Error creating sample data. Please check your input file and configuration.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)  # This will show the full traceback in development


def main():
    """Main application entry point."""

    inject_custom_css()

    # Initialize session state
    if 'column_names' not in st.session_state:
        st.session_state.column_names = []
    if 'sheet_names' not in st.session_state:
        st.session_state.sheet_names = []

    # Create tabs
    about_tab, main_tab, help_tab = st.tabs(["About", "Main", "Help"])

    # Get inputs from sidebar
    uploaded_file, column_config, sampling_params = render_sidebar()

    # Render tab content
    with about_tab:
        render_about_tab()

    with main_tab:
        render_main_tab(uploaded_file, column_config, sampling_params)

    with help_tab:
        render_help_tab()


if __name__ == "__main__":
    main()
