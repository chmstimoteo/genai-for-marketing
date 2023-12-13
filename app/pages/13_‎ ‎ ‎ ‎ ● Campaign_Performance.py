# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Marketing Insights demonstration: 
- Render Looker Dashboards with marketing data
- Create personalized headlines and images for marketing campaigns
- Translate content
"""


import streamlit as st
import streamlit.components.v1 as components
from utils_config import GLOBAL_CFG, MODEL_CFG, PAGES_CFG


page_cfg = PAGES_CFG["13_campaign_performance"]

st.set_page_config(
    page_title=page_cfg["page_title"], 
    page_icon=page_cfg["page_icon"],
    layout='wide'
)

import utils_styles
utils_styles.sidebar_apply_style(
    style=utils_styles.style_sidebar,
    image_path=page_cfg["sidebar_image_path"]
)

# Set project parameters 
PROJECT_ID = GLOBAL_CFG["project_id"]
LOCATION = GLOBAL_CFG["location"]
TEXT_MODEL_NAME = MODEL_CFG["text"]["text_model_name"]
IMAGE_MODEL_NAME = MODEL_CFG["image"]["image_model_name"]

# State variables for image and text generation
DASHBOARDS = page_cfg["dashboards"]
INFOBOT = page_cfg["infobot"]

# State variables
PAGE_KEY_PREFIX = "CampaignPerformance"
DASHBOARD_KEY = f"{PAGE_KEY_PREFIX}_Dashboard"

cols = st.columns([15,70,15])
with cols[1]:
    cols = st.columns([10, 90])
    with cols[0]:
        st.image('../app/images/opt_icon.png')
    with cols[1]:
        st.title('Campaign Performance')

    st.write("This page presents visualizations of marketing data "
             "in the form of Looker Dashboards.")

    if DASHBOARDS:
        with st.form(key='generate_marketing_dashboard'):
            placeholder_for_selectbox = st.empty()
            submit_button = st.form_submit_button(label='Generate Dashboard')
        
        with placeholder_for_selectbox:
            # Initialize and set default value
            if f"{DASHBOARD_KEY}_option_selectbox_temp" in st.session_state:
                # Copy from placeholder to widget key
                st.session_state[f"{DASHBOARD_KEY}_option_selectbox"] = st.session_state[f"{DASHBOARD_KEY}_option_selectbox_temp"]

            def _option_keeper():
                # Copy from widget key to placeholder
                st.session_state[f"{DASHBOARD_KEY}_option_selectbox_temp"] = st.session_state[f"{DASHBOARD_KEY}_option_selectbox"]
            
            option = st.selectbox(
                label = 'Select a dashboard to be displayed',
                options = [i.replace("_", " ") for i in DASHBOARDS.keys()],
                key=f"{DASHBOARD_KEY}_option_selectbox",
                on_change=_option_keeper)

        if submit_button:
            st.session_state[DASHBOARD_KEY] = option.replace(" ", "_")
    else:
        st.info('Dashboards not available.')

if DASHBOARD_KEY in st.session_state:
    components.iframe(
        src=DASHBOARDS.get(st.session_state[DASHBOARD_KEY]), 
        height=800, 
        scrolling=False
    )
else:
    components.iframe(
        src=DASHBOARDS['Overview'],
        height=800, 
        scrolling=False
    )
