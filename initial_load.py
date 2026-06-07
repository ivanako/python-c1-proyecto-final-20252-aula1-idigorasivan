import logging
import os
import pandas as pd
from pyparsing import line
import requests
from io import StringIO

# from shapely import buffer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def login_app() -> str:
    """
        Log in to the application using the credentials from the .env file and returns a JWT
    """

    req_jwt = None

    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_LOGIN")

    req_body = {
        "usr_name": os.getenv("ADMIN_USR"),
        "usr_pwd": os.getenv("ADMIN_PWD")
    }
    
    try:
        req_response = req_session.post(req_url, json=req_body)

        req_response.raise_for_status()

        req_jwt = req_response.json()["access_token"]

        logging.info("Login successful!!")

    except requests.exceptions.HTTPError as ex_http:
        logging.error(req_response.json()["error"])

    return req_jwt


def read_csv(path:str) -> dict[str, pd.DataFrame]:
    """
        Read a CSV file and returns a dictionary of DataFrames, where:
            - the keys are the section names (lines enclosed in square brackets) 
            - the values are the corresponding DataFrames
        parameters:
            path (str): The path to the CSV file
    """
    dic_sections = dict()
    csv_section = None
    lst_items = list()

    with open(file=path, mode="r", encoding="utf-8") as csv_file:
        for csv_file_item in csv_file:
            csv_line = csv_file_item.strip()

            if csv_line.startswith("[") and csv_line.endswith("]"):
                if lst_items:
                    dic_sections[csv_section] = pd.read_csv(StringIO("\n".join(lst_items)))
                
                lst_items = list()

                csv_section = csv_line[1:-1].strip().lower()

                continue

            lst_items.append(csv_line)
            

        if csv_section and lst_items:
            dic_sections[csv_section] = pd.read_csv(StringIO("\n".join(lst_items)))

    return dic_sections


def load_data(section:str, df:pd.DataFrame, jwt:str):
    """
        Loads data into the application using the corresponding API endpoint for each section. The JWT is used for authentication.
    """
    dic_sections={
        "doctors": os.getenv("API_DOCTORS"),
        "patients": os.getenv("API_PATIENTS"),
        "medical-centres": os.getenv("API_MEDICAL_CENTRES"),
        "appointments": os.getenv("API_APPOINTMENTS")
    }
    
    req_session = requests.Session()

    req_url = os.getenv("API_URL") + dic_sections[section]

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    for _, df_row in df.iterrows():
        try:
            req_response = req_session.post(req_url, json=df_row.to_dict(), headers=req_headers)
            req_response.raise_for_status()

            logging.info(f"Data loaded successfully for '{section}': {df_row.to_dict()}")

        except requests.exceptions.HTTPError as ex_http:
            logging.error(f"Error loading data for section '{section}': {ex_http}")

    pass


def create_appointment():
    pass


if __name__ == "__main__":
    
    app_jwt = login_app()

    if app_jwt:
        csv_sections = read_csv("data/data.csv")

        for name, df in csv_sections.items():
            print(f"Section: {name}")
            print(df)
            print("\n")

            load_data(name, df, app_jwt)
    else:
        logging.error("No JWT, no party!!")
    
