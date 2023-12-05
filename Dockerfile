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


FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Install python packages
RUN pip3 install google-cloud-datacatalog
RUN pip3 install db-dtypes
RUN pip3 install -U google-cloud-aiplatform 
RUN pip3 install pandas 
RUN pip3 install google-api-python-client 
RUN pip3 install python-dateutil 
RUN pip3 install newspaper3k 
RUN pip3 install google-cloud-bigquery
RUN pip3 install -U streamlit
RUN pip3 install pillow
RUN pip3 install streamlit-drawable-canvas==0.9.1
RUN pip3 install streamlit-image-select==0.6.0
RUN pip3 install google-cloud-discoveryengine
RUN pip3 install google-cloud-translate
RUN pip3 install cloudpickle

# Copy local code to the container image.
WORKDIR /app
COPY ./app ./

# Run the web service on container startup
CMD ["streamlit", "run", "Home.py"]
