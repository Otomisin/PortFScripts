import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
import json
from streamlit_folium import st_folium
from datetime import datetime
from io import StringIO
import time

@st.cache_data
def today():
    return datetime.now().strftime("%Y-%m-%d")

def display_ssd_facts(ssd_mt_admin_point, ssd_mt_admin_point_yes):
    total_assessment = ssd_mt_admin_point['A3_Supervisor_Name'].value_counts().sum()
    total_points_out = ssd_mt_admin_point_yes['A7_payam'].value_counts().sum()
    total_points_out_per = total_points_out / total_assessment * 100
    total_payams = ssd_mt_admin_point['A7_payam'].unique()
    
    return total_assessment, total_points_out, total_points_out_per, total_payams
  
  
def main():
    st.set_page_config(page_title='GeoPoint Checker', page_icon='🌍', layout="wide")
    st.title('GeoPoint Checker')
    st.caption(f'Checking for points not in designated area. Assessed today: {today()}')
    
    st.sidebar.markdown("<h1 style='text-align: left;'>ABOUT</h1>", unsafe_allow_html=True)
    st.sidebar.markdown('*GeoPoint Checker is a Streamlit-based web application designed for efficient geographic data assessment. It focuses on verifying the accuracy of geographical data points against designated areas, using spatial analysis. This tool is particularly useful for field data verification, offering valuable insights to researchers, GIS professionals, and data analysts. Upload the csv and geojson files used in the distributing enumerators.*')
    st.sidebar.divider()
    
    #Remove the St Style
    hideStStyle = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(hideStStyle, unsafe_allow_html=True)
    
    with st.spinner('Wait for it...'):
        time.sleep(5)
    # st.success('Done!')

    # File upload for the CSV and GeoJSON files
    st.sidebar.markdown("<h1 style='text-align: left;'>DATA UPLOAD</h1>", unsafe_allow_html=True)
    st.sidebar.markdown('*Ensure you upload the geojson and csv file used in the original assessment*')
    csv_file = st.sidebar.file_uploader("Upload CSV File", type=['csv'])
    geojson_file = st.sidebar.file_uploader("Upload GeoJSON File", type=['geojson'])

    if csv_file and geojson_file:
        ssd_points = pd.read_csv(csv_file, low_memory=False) 

        # Load and convert SSD_Admin JSON data to GeoDataFrame
        SSD_Admin_data = json.load(geojson_file)
        SSD_Admin = gpd.GeoDataFrame.from_features(SSD_Admin_data['features'])

        # Ensure that SSD_Admin has a defined CRS, if not, set it
        if SSD_Admin.crs is None:
            SSD_Admin.set_crs('EPSG:4326', inplace=True)

        # Convert ssd_points to GeoDataFrame and perform spatial join
        ssd_ra_p2_20230807_v3 = gpd.GeoDataFrame(
            ssd_points,
            geometry=gpd.points_from_xy(ssd_points['_location_gps_longitude'], ssd_points['_location_gps_latitude']),
            crs='EPSG:4326'
        )

        # Ensure both GeoDataFrames have the same CRS
        if ssd_ra_p2_20230807_v3.crs != SSD_Admin.crs:
            ssd_ra_p2_20230807_v3.to_crs(SSD_Admin.crs, inplace=True)

        # Spatial join between the questionnaire and admin data
        ssd_mt_admin_point = gpd.sjoin(ssd_ra_p2_20230807_v3, SSD_Admin, how='inner', predicate='intersects')

        ssd_mt_admin_point = ssd_mt_admin_point.assign(Point_outside_payam=lambda x: ['Yes' if a != b and a != 'other' and b != 'other' else 'No' for a, b in zip(x['A7_payam'], x['Payam_MT_P'])])

        ssd_mt_admin_point_yes = ssd_mt_admin_point[ssd_mt_admin_point['Point_outside_payam'] == 'Yes']
        ssd_mt_admin_point_no = ssd_mt_admin_point[ssd_mt_admin_point['Point_outside_payam'] == 'No']

        ssdPoint = ssd_mt_admin_point_no[['A3_Supervisor_Name', 'A7_payam', 'A2_Interviewer_Name', '_location_gps_latitude', '_location_gps_longitude', 'Point_outside_payam']]
        ssdPoint_yes = ssd_mt_admin_point_yes[['_uuid','A3_Supervisor_Name', 'A7_payam', 'A2_Interviewer_Name', '_location_gps_latitude', '_location_gps_longitude','Point_outside_payam']]

        # Calculate the average latitude and longitude for centering the map
        average_latitude = ssdPoint['_location_gps_latitude'].mean()
        average_longitude = ssdPoint['_location_gps_longitude'].mean()

        # Create a map centered at the average latitude and longitude
        m = folium.Map(location=[average_latitude, average_longitude], zoom_start=6, scrollwheelZoom=False, tiles='CartoDB Positron')

        # Add polygons from SSD_Admin GeoDataFrame
        for _, row in SSD_Admin.iterrows():
            geom = row['geometry']
            if geom and not geom.is_empty and geom.is_valid:
                geom = geom.simplify(tolerance=0.001, preserve_topology=True)
                geojson = gpd.GeoSeries([geom]).__geo_interface__
                folium.GeoJson(
                    geojson,
                    style_function=lambda x: {
                        'fillColor': 'grey', 
                        'color': 'grey', 
                        'weight': 0.5, 
                        'lineOpacity': 0.4 
                    },
                    highlight_function=lambda x: {'weight': 3, 'color': 'blue'},
                    tooltip=row['Payam_MT_P']
                ).add_to(m)

        # Add correct points
        for idx, row in ssdPoint.iterrows():
            folium.CircleMarker(
                location=[row['_location_gps_latitude'], row['_location_gps_longitude']],
                radius=5,
                color='blue',
                fill=True,
                fill_color='blue',
                popup=row['A7_payam'],
            ).add_to(m)

        # Function to generate popup for incorrect points
        def generate_popup(row):
            return f"""
                <b> INTERVIEWER: </b>
                {row['A2_Interviewer_Name']} <br>
                <b>PCODE:</b> {row['A7_payam']}

                """

        # Add incorrect points
        for idxy, row in ssdPoint_yes.iterrows():
            popup_html = generate_popup(row)
            folium.CircleMarker(
                location=[row['_location_gps_latitude'], row['_location_gps_longitude']],
                radius=5,
                color='red',
                fill=True,
                fill_color='red',
                popup=popup_html,
            ).add_to(m)

        # Metrics Display
        total_assessment, total_points_out, total_points_out_per, total_payams = display_ssd_facts(ssd_mt_admin_point, ssd_mt_admin_point_yes)
        
        # st.subheader('The Mini Facts')
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="Total Assessment", value=('{:,}'.format(total_assessment)))
        with col2:
            st.metric(label="# Wrong Locations", value=f"{total_points_out} ({total_points_out_per:.2f}%)")
        # with col3:
            # st.metric(label="Total Payams", value=('{:,}'.format(len(total_payams))))

        st.markdown("""---""")
        
        # Display the map
        st.markdown("""
        <div style='display: flex; justify-content: space-between;'>
            <span style='color: red'>Red: Points in wrong location</span>
            <span style='color: blue'>Blue: Points in right locations</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("This map displays the spatial data with interactive markers.") 
        st_folium(m,width= 2900, height=700)    


        # Convert the DataFrame to a CSV string
        csv = ssdPoint_yes.to_csv(index=False).encode('utf-8')

        # Create a download button and a link to download DataFrame as CSV
        st.sidebar.divider()
        st.sidebar.markdown("<h1 style='text-align: left;'> DOWNLOAD  DATA</h1>", unsafe_allow_html=True)
        st.sidebar.download_button(
            label="Download points out of designated areas as CSV",
            data=csv,
            file_name='ssdPoint_yes.csv',
            mime='text/csv',
        )       
      

        # Display the DataFrame in the app
        st.subheader('The Top 50 rows')
        st.write(ssdPoint_yes.head(50))
        st.sidebar.divider()
        
    st.sidebar.markdown("<h1 style='text-align: left;'>Help & Documentation</h1>", unsafe_allow_html=True) 
    st.sidebar.info("This section can contain additional help or documentation.")
    # st.sidebar.image('IOMlogo.png', width=150)
    # Create columns
    col1, col2, col3 = st.sidebar.columns([2,1,1])
    with col3:
        st.image('IOMlogo.png', width=70)
    with col1:
      st.markdown(" Made by ***Oluwatosin Orenaike***")


if __name__ == "__main__":
    main()
