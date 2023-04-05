import streamlit as st
from google_auth_oauthlib.flow import Flow
from streamlit_elements import Elements
import requests
from datetime import datetime, timedelta
import json
import functions
import base64
import pandas as pd
import toml

config = toml.load(".streamlit/secrets.toml")

clientId = config["google_auth"]["clientId"]
clientSecret = config["google_auth"]["clientSecret"]
redirectUri = config["google_auth"]["redirectUri"]

def main():
    st.set_page_config(page_title="Google AdWords API", page_icon=":mag_right:")
    st.image("https://www.434marketing.com/wp-content/themes/434-new-brand/assets/images/logo.png")
    st.title("Local Service Ads Report Generator")
    st.write("")

    with st.form(key="my_form"):
        st.markdown("")
        st.subheader("Step 1: Sign-in with Google")
        mt = Elements()

        mt.button(
            "Sign-in with Google",
            target="_blank",
            size="large",
            variant="contained",
            start_icon=mt.icons.exit_to_app,
            onclick="none",
            style={"color": "#FFFFFF", "background": "#FF4B4B"},
            href="https://accounts.google.com/o/oauth2/auth?response_type=code&client_id="
                 + clientId
                 + "&redirect_uri="
                 + redirectUri
                 + "&scope=https://www.googleapis.com/auth/adwords&access_type=offline&prompt=consent",
        )

        mt.show(key="687")

        query_params = st.experimental_get_query_params()
        code = query_params["code"] if "code" in query_params else None

        st.subheader("Step 2: Request Access Token")

        submit_account = st.form_submit_button(
            label="Request Access Token",
            on_click=functions.form_callback,
            args=(code,),
        )

    st.subheader("Step 3: Enter Days to Fetch")

    start_days_ago = st.number_input('Enter the number of days:', min_value=1, max_value=365, value=2)

    # Move the st.button() outside the st.form() block

    st.subheader("Step 4: Fetch Data")

    if st.button("Fetch Local Service Data"):
        auth_header = {"Authorization": f"Bearer {st.session_state.access_token}"}
        start_date = datetime.today() - timedelta(days=start_days_ago)
        end_date = datetime.today()
        dates = pd.date_range(start_date, end_date, freq="D").tolist()
        data = functions.get_local_service_data(dates, auth_header)
        df = pd.DataFrame(data)
        st.write(df)

        # Add a Streamlit option to download the dataframe as a CSV file
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # Encode the CSV data
        href = f'<a href="data:file/csv;base64,{b64}" download="LSA_report.csv">Download CSV</a>'  # Create a download link
        st.markdown(href, unsafe_allow_html=True)  # Display the download link as a button


if __name__ == "__main__":
    main()
