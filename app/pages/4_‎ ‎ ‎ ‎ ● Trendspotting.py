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
Trendspotting: 
- Identify emerging trends in the market by analyzing Google Trends data 
  on a Looker Dashboard 
- Summarizing news related to top search terms. 
- Generate a social media post for tweeter using summarized information.
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import vertexai

from datetime import date, timedelta, datetime
from google.cloud import bigquery
from utils_campaign import generate_names_uuid_dict
from utils_config import GLOBAL_CFG, MODEL_CFG, PAGES_CFG
from utils_trendspotting import GDELTRetriever
from utils_trendspotting import GoogleTrends
from utils_trendspotting import summarize_news_article
from utils_trendspotting import DMA_MAJOR_CITIES
from vertexai.preview.language_models import TextGenerationModel


page_cfg = PAGES_CFG["4_trendspotting"]

st.set_page_config(
    page_title=page_cfg["page_title"], 
    page_icon=page_cfg["page_icon"],
    layout='wide')

import utils_styles
utils_styles.sidebar_apply_style(
    style=utils_styles.style_sidebar,
    image_path=page_cfg["sidebar_image_path"]
)

# Set project parameters
PROJECT_ID = GLOBAL_CFG["project_id"]
LOCATION = GLOBAL_CFG["location"]
CAMPAIGNS_KEY = PAGES_CFG["campaigns"]["campaigns_key"]

bq_client = bigquery.Client(project=PROJECT_ID)
vertexai.init(project=PROJECT_ID, location=LOCATION)
llm = TextGenerationModel.from_pretrained(
    MODEL_CFG["text"]["text_model_name"])

default_date_value = date.today() - timedelta(2)
max_date_value = date.today() - timedelta(2)
min_date_value = date.today() - timedelta(26)

interest_max_date_value = date.today() - timedelta(2)
interest_min_date_value = date.today() - timedelta(92)

# State variables for news summarization
PAGE_KEY_PREFIX = "Trendspotting"
SUMMARIZATION_PREFIX = f"{PAGE_KEY_PREFIX}_Summarization"
TOP_SEARCH_TERM_DATE_KEY = f"{PAGE_KEY_PREFIX}_Top_Search_Term_Date"
TOP_SEARCH_TERM_KEY = f"{PAGE_KEY_PREFIX}_Top_Search_Term"
SUMMARIZATION_TERM_KEY = f"{SUMMARIZATION_PREFIX}_Term"
SUMMARIZATION_SUMMARIES_KEY = f"{SUMMARIZATION_PREFIX}_Summaries"


cols_page = st.columns([14,72,14])

with cols_page[1]:
    cols = st.columns([15, 85])
    with cols[0]:
        st.image(page_cfg["page_title_image"])
    with cols[1]:
        st.title(page_cfg["page_title"])

    st.write(
        "This page demonstrates how to use Google Trends " 
        "to stay up-to-date on current events " 
        "and trends by tracking popular search terms " 
        "and summarizing news articles about them."
    )


    #st.subheader('Google Trends dataset')
    #st.write(
    #    "The following dashboard demonstrates "
    #    "the top search terms in the US for "
    #    "the latest available data. "
    #    "This query looks at the latest data available to "
    #    "return the top 25 search terms in the US for "
    #    "the most recent week available."
    #)

# Renders the Google trends dashboard
#components.iframe(
#    src='https://datasignals.looker.com/embed/dashboards/11?theme=GoogleWhite',
#    height=800, 
#    scrolling=False
#)

cols_page = st.columns([14,72,14])
with cols_page[1]:
    # Google Trends retrieval tool ###########
    st.subheader('Google Trends')
    st.write(
        "Using the form below, select a date " 
        "to retrieve the top 1 search term(s) in the US."
    )
    with st.form('form_google_trends'):
        st.write("**Google Trends top search terms**")

        selected_date = st.date_input(
            'Select a date to retrive the top search terms from Google Trends',
            default_date_value,
            min_value=min_date_value,
            max_value=max_date_value)
        assert isinstance(selected_date, date)
        trends_date = date.strftime(selected_date, '%Y-%m-%d')
        button_trend = st.form_submit_button('Get top search terms')

    if button_trend:
        with st.spinner("Querying..."):
            google_trends_tool = GoogleTrends(
                project_id=PROJECT_ID, bq_client=bq_client)
            st.session_state[TOP_SEARCH_TERM_DATE_KEY] = trends_date
            st.session_state[TOP_SEARCH_TERM_KEY] = google_trends_tool.run(
                trends_date)

    if (TOP_SEARCH_TERM_KEY in st.session_state and 
        TOP_SEARCH_TERM_DATE_KEY in st.session_state):
        st.write(
            'Top search term for date '
            f'{st.session_state[TOP_SEARCH_TERM_DATE_KEY]} is: '
            f'{" ".join(st.session_state[TOP_SEARCH_TERM_KEY])}')
    ##########################################
       
cols_page = st.columns([14,72,14])
with cols_page[1]:
    # Google Trends Search #####################
    st.write(
        "Using the form below, type a Search term, select a US city "
        "and select a date interval " 
        "to retrieve Google Trends data."
    )
    with st.form('form_google_trends_interest'):
        st.write("**Google Trends Search Interest in US**")
        interest_keyword = st.text_input('Search term', 'Coat')

        #Getting DMA_MAJOR_CITIES selection
        select_box_options = [f"{item['city']} - {item['region']}" for item in DMA_MAJOR_CITIES]
        question_option = st.selectbox(
            label=("Select a City/State"),
            options=select_box_options,
            index=select_box_options.index("Austin - TX"),
            #key=f"{state_key}_question_prompt_text_area"
            )

        #Selecting the dates intervals
        min_selected_date = st.date_input(
            'Select a starting date for Google Trends',
            interest_min_date_value,
            min_value=interest_min_date_value,
            max_value=interest_max_date_value)
        assert isinstance(min_selected_date, date)
        min_trends_date = date.strftime(min_selected_date, '%Y-%m-%d')
        
        max_selected_date = st.date_input(
            'Select a ending date for Google Trends',
            interest_max_date_value,
            min_value=interest_min_date_value,
            max_value=interest_max_date_value)
        assert isinstance(max_selected_date, date)
        max_trends_date = date.strftime(max_selected_date, '%Y-%m-%d')

        trend_button_trend = st.form_submit_button('Get Interest and Related Queries')

    if trend_button_trend or (f"{PAGE_KEY_PREFIX}_Trends_Search_Interest" in st.session_state
                              and f"{PAGE_KEY_PREFIX}_Trends_Search_Queries" in st.session_state
                              and f"{PAGE_KEY_PREFIX}_Trends_Search_URL" in st.session_state):
        with st.spinner("Querying..."):
            google_trends_tool = GoogleTrends(
                project_id=PROJECT_ID, bq_client=bq_client)
            google_trends_tool.get_search_interests_queries(
                interest_keyword=interest_keyword,
                min_trends_date=min_trends_date,
                max_trends_date=max_trends_date,
                state_key_interests=f"{PAGE_KEY_PREFIX}_Trends_Search_Interest",
                state_key_queries=f"{PAGE_KEY_PREFIX}_Trends_Search_Queries")
            google_trends_tool.get_url(
                interest_keyword=interest_keyword,
                min_trends_date=min_trends_date,
                max_trends_date=max_trends_date,
                state_key_url=f"{PAGE_KEY_PREFIX}_Trends_Search_URL")

if (f"{PAGE_KEY_PREFIX}_Trends_Search_Interest" in st.session_state) and \
   (f"{PAGE_KEY_PREFIX}_Trends_Search_Queries" in st.session_state) and \
   (f"{PAGE_KEY_PREFIX}_Trends_Search_URL" in st.session_state):
    
    cols_page = st.columns([14,72,14])
    with cols_page[1]:
        default_url = "https://trends.google.com/trends/explore?date=2023-09-04%202023-12-04&geo=US-TX-635&q=%2Fm%2F01xygc"
        
        if st.session_state[f"{PAGE_KEY_PREFIX}_Trends_Search_URL"]:
            url = st.session_state[f"{PAGE_KEY_PREFIX}_Trends_Search_URL"]
        else:
            url = default_url

        st.write('')
        st.write("If the charts below ask you to try in again in a bit. Check out this [link](%s)" % url)
        st.write('')

    cols_page = st.columns([14,36,36,14])
    with cols_page[1]:
        components.html("""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        .myDiv {
        border: 1px outset lightblue;
        background-color: lightgray;
        text-align: left;
        }
        </style>
        </head>
        <body>
        <script type="text/javascript" src="https://ssl.gstatic.com/trends_nrtr/3523_RC02/embed_loader.js"></script> 
        <script type="text/javascript"> trends.embed.renderExploreWidget("TIMESERIES", {"comparisonItem":[{"keyword":"/m/01xygc","geo":"US-TX-635","time":"2023-09-04 2023-12-04"}],"category":0,"property":""}, {"exploreQuery":"date=2023-09-04%202023-12-04&geo=US-TX-635&q=zcxzvxcv","guestPath":"https://trends.google.com:443/trends/embed/"}); </script>
        <script type="text/javascript">
        document.getElementsByTagName("iframe")[0].addEventListener( "load", function(e) {
            this.setAttribute('height','450px')
        } );
        </script>
        </body>
        </html>""",
        height=450,
        width=350
        )

    with cols_page[2]:
        components.html("""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        .myDiv {
        border: 1px outset lightblue;
        background-color: lightgray;
        text-align: left;
        }
        </style>
        </head>
        <body>
        <script type="text/javascript" src="https://ssl.gstatic.com/trends_nrtr/3523_RC02/embed_loader.js"></script>
        <script type="text/javascript"> trends.embed.renderExploreWidget("RELATED_QUERIES", {"comparisonItem":[{"keyword":"/m/01xygc","geo":"US-TX-635","time":"2023-09-04 2023-12-04"}],"category":0,"property":""}, {"exploreQuery":"date=2023-09-04%202023-12-04&geo=US-TX-635&q=%2Fm%2F01xygc","guestPath":"https://trends.google.com:443/trends/embed/"}); </script>
        <script type="text/javascript">
        document.getElementsByTagName("iframe")[0].addEventListener( "load", function(e) {
            this.setAttribute('height','450px')
        } );
        </script>
        </body>
        </html>""",
            height=450,
            width=350)
    ##########################################

# News Summarization #####################
cols_page = st.columns([14,72,14])
with cols_page[1]:
    st.subheader('News Summarization')
    st.write(
        "Provide keywords to retrive summaries " 
        "of news articles related to them."
    )
    with st.form(key='form_summarize'):
        st.write('**Summarize News**')
        col1, col2, col3 = st.columns([50,50,50])

        with col1:
            max_records = st.number_input(
                'Maximum number of news articles to return', 
                min_value=1,
                max_value=20,
                value=5, step=1)

        col_keyword_1, col_keyword_2, col_keyword_3 = st.columns([33, 33, 33])
        with col_keyword_1:
            keyword_1 = st.text_input('Keyword 1', 'fashion')

        with col_keyword_2:
            keyword_2 = st.text_input('Keyword 2', '')

        with col_keyword_3:
            keyword_3 = st.text_input('Keyword 3', '')

        submit_button = st.form_submit_button(label='Summarize News')

    if submit_button:
        if not any([keyword_1, keyword_2, keyword_3]):
            st.info('Provide at least one keyword')

        st.session_state[SUMMARIZATION_TERM_KEY] = [keyword_1,
                                                    keyword_2,
                                                    keyword_3]

        with st.spinner('Summarizing news...'):        
            retriever = GDELTRetriever(max_records=int(max_records))
            today_date = datetime.now()
            start_date = today_date - timedelta(5)

            try:
                documents = retriever.get_relevant_documents(
                    query={
                        'keywords': st.session_state[SUMMARIZATION_TERM_KEY], 
                        'startdate': start_date.strftime('%Y%m%d%H%M%S'),
                        'enddate': today_date.strftime('%Y%m%d%H%M%S')}
                )
            except:
                st.info('No articles found. Try different keywords.')
            else:
                summaries = []
                for i, doc in enumerate(documents):
                    summary = summarize_news_article(doc, llm)['summary']
                    summaries.append({
                        "original_headline": doc["title"],
                        "summary":summary,
                        "url": doc["url"]
                    })
                st.session_state[SUMMARIZATION_SUMMARIES_KEY] = summaries
        
    if SUMMARIZATION_SUMMARIES_KEY in st.session_state:
        st.write(
            f"**Summaries of news articles with the keyword(s)**: "
            f"{st.session_state[SUMMARIZATION_TERM_KEY][0]} "
            f"{st.session_state[SUMMARIZATION_TERM_KEY][1]} " 
            f"{st.session_state[SUMMARIZATION_TERM_KEY][2]}")
        for summary in st.session_state[SUMMARIZATION_SUMMARIES_KEY]:
            st.divider()
            st.write(f"""
                        **Original Headline**: {summary["original_headline"]}.\n
                        **Summary**: {summary["summary"]}""")
    ##########################################

    if (SUMMARIZATION_SUMMARIES_KEY in st.session_state and
        CAMPAIGNS_KEY in st.session_state):
        campaigns_names = generate_names_uuid_dict().keys()
        with st.form(PAGE_KEY_PREFIX+"_Link_To_Campaign_Upload"):
            st.write("**Choose a Campaign to save the news summaries**")
            selected_name = st.selectbox("List of Campaigns", campaigns_names)
            link_to_campaign_button = st.form_submit_button(
                label="Save to Campaign")

        if link_to_campaign_button:
            selected_uuid = generate_names_uuid_dict()[selected_name]
            st.session_state[CAMPAIGNS_KEY][
                selected_uuid].trendspotting_summaries = pd.DataFrame(
                    st.session_state[SUMMARIZATION_SUMMARIES_KEY])
            st.success(f"Saved to campaign {selected_name}")
