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
Utility module for Codey releated demo.
"""

import pandas as pd
import streamlit as st
from io import StringIO

from google.cloud import bigquery
from google.cloud import datacatalog_v1
from pandas import DataFrame
from typing import Optional
from utils_campaign import generate_names_uuid_dict
from utils_config import GLOBAL_CFG, MODEL_CFG, PAGES_CFG
from utils_streamlit import reset_page_state
from vertexai.preview.language_models import TextGenerationModel


TEXT_MODEL_NAME = MODEL_CFG["text"]["text_model_name"]

PROMPT = PAGES_CFG["3_audiences"]["prompt_nl_sql"]
PROMPT_PROJECT_ID = [GLOBAL_CFG['project_id']]*130
CAMPAIGNS_KEY = PAGES_CFG["campaigns"]["campaigns_key"]


def upload_read_personas_csv_file(
        state_key: str,
):
    uploaded_file = st.file_uploader("Choose a CSV personas file")
    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()

        # To convert to a string based IO:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))

        # To read file as string:
        string_data = stringio.read()

        # Can be used wherever a "file-like" object is accepted:
        dataframe = pd.read_csv(uploaded_file, comment='#', skiprows=12)
        dataframe.drop(columns=['Area.1', 'Relevance', \
                           'Details', 'Channel name', \
                           'Channel videos', 'Channel subscribers',\
                           'Video views', 'URL', 'Comment'], inplace=True)
        st.session_state[state_key] = dataframe


def get_segment_insights(
        text_prompt_segments_insights_template: str, 
        personas: pd.DataFrame, 
        state_key: str):
    
    from json import loads, dumps
    result = personas.to_json(orient="records")
    parsed = loads(result)
    personas = dumps(parsed, indent=4)

    text_prompt_segments_insights = f"{text_prompt_segments_insights_template}".format(personas=personas)

    st.session_state[state_key] = text_prompt_segments_insights


def generate_text_prompt(
        question: str,
        metadata: list,
        examples: str,
        state_key: str,
):
    """Generates a prompt for a GoogleSQL query compatible with BigQuery.

    Args:
        question: 
            The question to answer.
        metadata: 
            A list of dictionaries, where each dictionary describes a BigQuery 
            table. 
            The dictionaries should have the following keys:
            - name: The name of the table.
            - schema: The schema of the table.
            - description: A description of the table.
        state_key: 
            The key to use to store the prompt in the session state.

    Returns:
        The prompt.
    """
    context = ''
    for i in metadata:
        context += i

    st.session_state[state_key] = f"""
{context}
{examples}
{question}
Answer:
"""


def generate_llm_audience_segment_insights(
        state_key: str,
        title: str,
        query: str,
        project_id: str,
        dataset_id: str,
        tag_template_name: str,
        bqclient: bigquery.Client,
        default_query: str="") -> Optional[DataFrame]:
    """Generates a GoogleSQL query and executes it against a BigQuery dataset.

    Args:
        state_key: 
            A unique identifier for the current session.
        title: 
            The title of the UI page.
        query: 
            The initial query text.
        project_id: 
            The ID of the BigQuery project.
        dataset_id: 
            The ID of the BigQuery dataset.
        tag_template_name: 
            The name of the tag template to use for the query.
        bqclient: 
            A BigQuery client object.

    Returns:
        A DataFrame containing the results of the query.

    Raises:
        NotFoundError: If the dataset or table is not found.
        BadRequestError: If the query is invalid.
    """
    with st.form(f"{state_key}_form"):
        st.write(f"**{title}**")
        placeholder_for_file_upload = st.empty()
        personas_expander = st.empty()
        placeholder_for_textarea = st.empty()
        submit_button = st.form_submit_button("Submit")
    
    with placeholder_for_file_upload:
        upload_read_personas_csv_file(f"{state_key}_Personas_File")
    
    if f"{state_key}_Personas_File" in st.session_state:
        with personas_expander:
            st.dataframe(st.session_state[f"{state_key}_Personas_File"])
    
    with placeholder_for_textarea:
        question_option = st.text_area(
            label=("Write your question to ask PaLM API "
                   "and generate your audience segment insight"),
            value=f"Describe each persona by their gender, age range, interests and affinity, parental status and estimated household income.",
            key=f"{state_key}_question_prompt_text_area")

    if submit_button:
        question = ""
        #reset_page_state(state_key)
        
        if question_option:
            question = question_option

            with st.spinner('Retrieving the Text to GoogleSQL examples'):
                get_segment_insights(
                    text_prompt_segments_insights_template=PAGES_CFG["3_audiences"]["text_prompt_segments_insights_template"], 
                    personas=st.session_state[f"{state_key}_Personas_File"], 
                    state_key=f"{state_key}_Context_Prompt")

            with st.spinner('Creating a prompt'):
                generate_text_prompt(
                    metadata=[st.session_state[f"{state_key}_Context_Prompt"]],
                    question=question,
                    examples="",
                    state_key=f"{state_key}_Text_Prompt")

            with st.expander('Prompt'):
                st.text(st.session_state[f"{state_key}_Text_Prompt"])
            
            with st.spinner('Generating the answer with PaLM'):
                client_code_model = TextGenerationModel.from_pretrained(
                    TEXT_MODEL_NAME)
                try:
                    gen_text = client_code_model.predict(
                        prompt = st.session_state[f"{state_key}_Text_Prompt"],
                        max_output_tokens = 1024,
                        temperature=0.2
                    ).text
                except Exception as e:
                    print("Error")
                    print(str(e))
                    gen_text = ""

                if gen_text:
                    st.session_state[f"{state_key}_Gen_Text"] = gen_text
                    
                st.write('Audience segment insight generated by PaLM 2')
                st.write(f"""{st.session_state[f"{state_key}_Gen_Text"]}""")
        else:
            st.write('Audience segment insight generated by PaLM 2')
            st.write(f"""{st.session_state[f"{state_key}_Gen_Text"]}""")
            
    else:

        if f"{state_key}_Text_Prompt" in st.session_state:
            with st.expander('Prompt'):
                st.text(st.session_state[f"{state_key}_Text_Prompt"])

        if f"{state_key}_Gen_Text" in st.session_state:
            st.write('Audience segment insight generated by PaLM 2')
            st.write(st.session_state[f"{state_key}_Gen_Text"])
