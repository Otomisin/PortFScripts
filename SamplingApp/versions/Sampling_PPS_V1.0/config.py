# config.py
"""
Application configuration, settings and styles.
"""
import streamlit as st
import os
from streamlit.components.v1 import html

# Page configuration
PAGE_CONFIG = {
    'page_title': "Sampling Calculator",
    'page_icon': "🧊",
    'layout': "wide",
    'menu_items': {
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': 'https://github.com/streamlit/streamlit/issues',
        'About': "This is an example app."
    }
}

# Default sampling parameters
DEFAULT_SAMPLING_PARAMS = {
    'confidence_level': 0.9,
    'margin_of_error': 0.10,
    'design_effect': 2.0,
    'interviews_per_cluster': 5,
    'reserve_percentage': 0.1,
    'probability': 0.5
}


# Define CSS directly in the script
CUSTOM_CSS = """
    /* Reset default margins and padding */
    .main > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove space above tabs */
    .stTabs {
        margin-top: -4rem !important;
        padding-top: 0 !important;
    }
    
    #####################
    /* Remove extra padding from main container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Dropdown and input styling */
    [data-testid="stSelectbox"] select {
        color: #2c3338 !important;
    }
    
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: white !important;
    }
    
    [data-testid="stSelectbox"] div[data-baseweb="select"] div {
        color: #2c3338 !important;
    }
    
    /* Selectbox label styling */
    [data-testid="stSelectbox"] label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] section {
        border: 2px dashed rgba(255, 255, 255, 0.4) !important;
        border-radius: 4px !important;
        padding: 1rem !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    
    [data-testid="stFileUploader"] section p,
    [data-testid="stFileUploader"] section span {
        color: white !important;
    }
    
    [data-testid="stFileUploader"] small {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Expander text color */
    [data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stSidebar"] .streamlit-expanderContent p {
        color: white !important;
    }
    
    /* Help text in sidebar */
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Base sidebar styles */
    [data-testid="stSidebar"] {
        background-color: #084a88 !important;
    }
    
    /* Labels and headers in sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Dropdown option hover state */
    .stSelectbox div[role="option"]:hover {
        background-color: rgba(8, 74, 136, 0.1) !important;
    }
    
    /* Tab styles with reduced spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 32px;
        background-color: transparent;
        padding: 0 24px;
        margin-top: 0;
        margin-bottom: 16px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px;
        color: #084a88;
        font-weight: 400;
        padding: 0 24px;
        margin: 0 8px;
    }
    
    """


def inject_custom_css():
    # Use the CSS string directly instead of reading from file
    st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

    # Add theme toggle component
    st.markdown('<div class="theme-toggle">', unsafe_allow_html=True)
    html("""
        <div id="theme-toggle-wrapper"></div>
        <script>
            const documentRoot = document.documentElement;
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (prefersDark) {
                documentRoot.classList.add('dark');
            }
            
            const mountNode = document.getElementById('theme-toggle-wrapper');
            if (window.ReactDOM && window.React && window.components) {
                const root = ReactDOM.createRoot(mountNode);
                root.render(React.createElement(window.components['theme-toggle'].default));
            }
        </script>
    """, height=50)
    st.markdown('</div>', unsafe_allow_html=True)


# # Inject the custom CSS
# inject_custom_css()
