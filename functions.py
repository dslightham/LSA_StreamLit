import streamlit as st
from google_auth_oauthlib.flow import Flow
import toml

config = toml.load(".streamlit/secrets.toml")

clientId = config["google_auth"]["clientId"]
clientSecret = config["google_auth"]["clientSecret"]
redirectUri = config["google_auth"]["redirectUri"]

# Define flow as a global variable
credentials = {
    "installed": {
        "client_id": clientId,
        "client_secret": clientSecret,
        "redirect_uris": [],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://accounts.google.com/o/oauth2/token",
    }
}

flow = Flow.from_client_config(
    credentials,
    scopes=["https://www.googleapis.com/auth/adwords"],
    redirect_uri=redirectUri,
)

import requests
import json
from datetime import datetime, timedelta
import pandas as pd


def get_local_service_data(dates, auth_header):
    data = []
    start_date = dates[0]  # initialize start_date with the first date in the list
    end_date = dates[-1]  # initialize end_date with the last date in the list

    # Loop through each day from start_date to end_date
    while start_date <= end_date:
        start_day = str(start_date.day)
        start_month = str(start_date.month)
        start_year = str(start_date.year)

        end_day = str(start_date.day)
        end_month = str(start_date.month)
        end_year = str(start_date.year)

        # Build the API request URL
        url = "https://localservices.googleapis.com/v1/accountReports:search?query=manager_customer_id:5868136301&startDate.day={0}&startDate.month={1}&startDate.year={2}&endDate.day={3}&endDate.month={4}&endDate.year={5}&alt=json".format(
            start_day, start_month, start_year, end_day, end_month, end_year)

        response = requests.request("GET", url, headers=auth_header)

        if not response.ok:
            continue

        json_response = json.loads(response.text)

        # Extract the required items from the JSON response
        for account_report in json_response.get('accountReports', []):
            date_pulled = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Set date_pulled to the current date and time
            account_id = account_report.get('accountId')
            business_name = account_report.get('businessName')
            avg_weekly_budget = account_report.get('averageWeeklyBudget')
            avg_five_star_rating = account_report.get('averageFiveStarRating')
            total_review = account_report.get('totalReview')
            phone_lead_responsiveness = account_report.get('phoneLeadResponsiveness')
            current_period_charged_leads = account_report.get('currentPeriodChargedLeads')
            current_period_total_cost = account_report.get('currentPeriodTotalCost')
            current_period_phone_calls = account_report.get('currentPeriodPhoneCalls')
            current_period_connected_phone_calls = account_report.get('currentPeriodConnectedPhoneCalls')

            # Add the extracted information to the list
            data.append({'date_pulled': date_pulled,
                         'accountID': account_id,
                         'businessName': business_name,
                         'averageWeeklyBudget': avg_weekly_budget,
                         'averageFiveStarRating': avg_five_star_rating,
                         'totalReview': total_review,
                         'phoneLeadResponsiveness': phone_lead_responsiveness,
                         'currentPeriodChargedLeads': current_period_charged_leads,
                         'currentPeriodTotalCost': current_period_total_cost,
                         'currentPeriodPhoneCalls': current_period_phone_calls,
                         'currentPeriodConnectedPhoneCalls': current_period_connected_phone_calls,
                         'start_date': start_date.strftime('%Y-%m-%d'),
                         'end_date': start_date.strftime('%Y-%m-%d')})

        # Increment the start_date by one day
        start_date += timedelta(days=1)

    # Create a Pandas Dataframe with the extracted information
    df = pd.DataFrame(data)
    return data


def form_callback(authorization_response):
    with st.spinner("Accessing Google Local Service/AdWords API..."):
        code = authorization_response[0]
        flow.fetch_token(code=code)
        credentials = flow.credentials
        st.write("Access granted! 🎉")
        st.session_state.access_token = credentials.token
        st.session_state.refresh_token = credentials.refresh_token

        # New lines added to print the bearer and authorization token
        bearer_token = f"Bearer {credentials.token}"
        auth_header = {"Authorization": bearer_token}

import pandas_gbq
import logging

def write_to_bigquery(df, project_id, dataset_id, table_name):
    try:
        # Set up the BigQuery credentials
        credentials = flow.credentials
        pandas_gbq.context.credentials = credentials

        # Write the DataFrame to BigQuery
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        pandas_gbq.to_gbq(df, table_ref, if_exists="append")

        logging.info(f"Data pushed to table {table_ref}")
    except Exception as e:
        logging.error(f"Error pushing data to BigQuery: {e}")
