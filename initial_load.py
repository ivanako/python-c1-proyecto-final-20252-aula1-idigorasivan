from datetime import datetime
import json
import logging
import os
import sys
import pandas as pd
from pybikes import data
from pyparsing import line
import requests
from io import StringIO

from odontocare.admin.bp_admin import list_doctors

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

            # logging.info(f"Data loaded successfully for '{section}': {df_row.to_dict()}")

        except requests.exceptions.HTTPError as ex_http:
            logging.error(f"Error loading data for section '{section}': {ex_http}")


def select_doctor(jwt:str) -> tuple[str | None, str | None]:
    """
        Fetch the list of doctors from the database
        
        parameters:
            jwt (str): The JWT for authentication
        returns:
            tuple[str | None, str | None]: The selected doctor ID and name or None for both
    """
    doc_id = None
    doc_name = None

    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_DOCTORS")

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        list_doctors = req_response.json()

        if len(list_doctors) == 0:
            logging.warning("No doctors found")
        else:
            print("ID  Name      Specialty")
            
            for doc in list_doctors:
                print(doc["doc_id"], doc["doc_name"], doc["doc_specialty"])
    
            doc_id = check_doctor(list_doctors)

            print(f"Selected doctor ID: {doc_id}")

            doc_name = next((doc["doc_name"] for doc in list_doctors if doc["doc_id"] == doc_id), None)

    except requests.exceptions.HTTPError as ex_http:
        logging.error(f"Error fetching doctor list: {ex_http}")

    return doc_id, doc_name

def check_doctor(list_doctors: list[dict]) -> int:
    """
        Ask the user for a doctor ID and verifies it is on the list from the database
        
        parameters:
            list_doctors (list[dict]): List of doctors
        returns:
            int: The chosen doctor ID
    """

    is_valid_doctor_id = False

    for i in range(3):
        try:
            doc_id = int(input("Select a doctor ID from the list above and press Enter : "))
        except ValueError:
            logging.warning("Invalid input, please enter a valid doctor ID")
            continue
        
        if any(doc["doc_id"] == doc_id for doc in list_doctors):
            is_valid_doctor_id = True
            break
        else:
            logging.warning("Doctor ID {} not found".format(doc_id))
            continue

    if not is_valid_doctor_id:
        logging.error("No valid doctor ID selected after 3 attempts. Please, restart application and try again")
        sys.exit()
        
    return doc_id


def select_patient(jwt: str) -> tuple[int | None, str | None]:
    """
        Fetch the list of patients from the database
        
        parameters:
            jwt (str): The JWT for authentication
        returns:
            tuple[int | None, str | None]: The selected patient ID and name or (None, None)
    """
    pat_id = None
    pat_name = None

    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_PATIENTS")

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        list_patients = req_response.json()

        if len(list_patients) == 0:
            logging.warning("No patients found")
        else:
            print("ID  Name")
            
            for pat in list_patients:
                print(pat["pat_id"], pat["pat_name"])
    
            pat_id = check_patient(list_patients)

            print(f"Selected patient ID: {pat_id}")

            pat_name = next((pat["pat_name"] for pat in list_patients if pat["pat_id"] == pat_id), None)


    except requests.exceptions.HTTPError as ex_http:
        logging.error(f"Error fetching patient list: {ex_http}")

    return pat_id, pat_name

def check_patient(list_patients: list[dict]) -> int:
    """
        Ask the user for a patient ID and verifies it is on the list from the database
        
        parameters:
            list_patients (list[dict]): List of patients
        returns:
            int: The chosen patient ID
    """
    
    is_valid_patient_id = False

    for i in range(3):
        try:
            pat_id = int(input("Select a patient ID from the list above and press Enter : "))
        except ValueError:
            logging.warning("Invalid input, please enter a valid patient ID")
            continue
        
        if any(pat["pat_id"] == pat_id for pat in list_patients):
            is_valid_patient_id = True
            break
        else:
            logging.warning("Patient ID {} not found".format(pat_id))
            continue

    if not is_valid_patient_id:
        logging.error("No valid patient ID selected after 3 attempts. Please, restart application and try again")
        sys.exit()

    return pat_id


def select_medical_centre(jwt: str) -> tuple[str | None, str | None]:
    """
        Fetch the list of Medical Centres from the database
        
        parameters:
            jwt (str): The JWT for authentication
        returns:
            tuple[str | None, str | None]: The selected Medical Centre ID and name or None for both
    """
    mdc_id = None
    mdc_name = None

    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_MEDICAL_CENTRES")

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        list_medical_centres = req_response.json()

        if len(list_medical_centres) == 0:
            logging.warning("No Medical Centres found")
        else:
            print("ID  Name")
            
            for mdc in list_medical_centres:
                print(mdc["mdc_id"], mdc["mdc_name"])
    
            mdc_id = check_medical_centre(list_medical_centres)

            print(f"Selected Medical Centre ID: {mdc_id}")

            mdc_name = next((mdc["mdc_name"] for mdc in list_medical_centres if mdc["mdc_id"] == mdc_id), None)

    except requests.exceptions.HTTPError as ex_http:
        logging.error(f"Error fetching Medical Centre list: {ex_http}")

    return mdc_id, mdc_name

def check_medical_centre(list_medical_centres: list[dict]) -> int:
    """
        Ask the user for a Medical Centre ID and verifies it is on the list from the database
        
        parameters:
            list_medical_centres (list[dict]): List of Medical Centres
        returns:
            int: The chosen Medical Centre ID
    """
    is_valid_mdc_id = False

    for i in range(3):
        try:
            mdc_id = int(input("Select a Medical Centre ID from the list above and press Enter : "))
        except ValueError:
            logging.warning("Please, enter a valid Medical Centre ID")
            continue
        
        if isinstance(mdc_id, int):
            if any(mdc["mdc_id"] == int(mdc_id) for mdc in list_medical_centres):
                is_valid_mdc_id = True
                break
            else:
                logging.warning("Medical centre ID {} not found".format(mdc_id))
                continue
        else:
            logging.warning("Please, enter a valid Medical Centre ID")

    if not is_valid_mdc_id:
        logging.error("No valid Medical Centre ID selected after 3 attempts. Please, restart application and try again")
        sys.exit()

    return int(mdc_id)


def schedule_appointment(jwt: str):
    input("Press Enter to schedule an appointment...")

    doc_id, doc_name = select_doctor(jwt)
    pat_id, pat_name = select_patient(jwt)
    mdc_id, mdc_name = select_medical_centre(jwt)

    apm_date = check_appointment_date()

    apm_reason = input("Set a reason for the appointment and press Enter : ")
    apm_status = "Pendiente"

    
    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_APPOINTMENTS")

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    req_body = {
        "doc_id": doc_id,
        "pat_id": pat_id,
        "mdc_id": mdc_id,
        "apm_reason": apm_reason,
        "apm_date": apm_date.strftime("%Y-%m-%d %H:%M"),
        "apm_status": apm_status
    }

    try:
        req_response = req_session.post(url=req_url, json=req_body, headers=req_headers)
        req_response.raise_for_status()

        logging.info("Appointment scheduled!!")

        print("========================================")
        print("Appointment details:")
        print("========================================")
        print(f"Doctor: {doc_name}")
        print(f"Patient: {pat_name}")
        print(f"Medical Centre: {mdc_name}")
        print(f"Reason: {apm_reason}")
        print(f"Date: {apm_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Status: {apm_status}")

    except requests.exceptions.HTTPError as ex_http:
        logging.error(req_response.json()["error"])

    
def check_appointment_date() -> datetime:
    """
        Ask the user for an appointment date and verifies it is later than current one
        
        parameters:
            None
        returns:
            datetime: The chosen appointment date
    """

    is_valid_date = False

    for _ in range(3):
        try:
            aux_date = input("Set a date later than the current one and press Enter (<YYYY-mm-DD HH:MM>): ")
            apm_date = datetime.strptime(aux_date, "%Y-%m-%d %H:%M")
            
            if apm_date <= datetime.now():
                logging.warning("Please enter a date later than the current one.")
                continue
            
            is_valid_date = True

            break
        except ValueError:
            logging.warning("Invalid date format. Please use the format <YYYY-mm-DD HH:MM>")
            continue
    
    if not is_valid_date:
        logging.error("No valid date selected after 3 attempts. Please, restart application and try again")
        sys.exit()

    return apm_date

def check_appointment_date_by_doctor(jwt: str, doc_id: int, apm_date: datetime) -> datetime:
    
    is_valid_date_doctor = False

    req_session = requests.Session()

    req_url = os.getenv("API_URL") + os.getenv("API_APPOINTMENTS_BY_DOCTOR").replace("<doc_id>", str(doc_id))

    req_headers = {
        "Authorization": f"Bearer {jwt}"
    }

    for _ in range(3):
        try:
            req_response = req_session.get(req_url, headers=req_headers)
            req_response.raise_for_status()

            list_appointments_by_doctor = req_response.json()

            if list_appointments_by_doctor:
                if any(apm_doc["apm_date"] == apm_date for apm_doc in list_appointments_by_doctor):
                    logging.warning("The selected doctor has already an appointment at the selected date and time")
                    continue
            
            is_valid_date_doctor = True

            break
        except requests.exceptions.HTTPError as ex_http:
            logging.error(f"Error fetching Medical Centre list: {ex_http}")

    if not is_valid_date_doctor:
        logging.error("The selected doctor has already an appointment at the selected date and time after 3 attempts. Please, restart application and try again")
        sys.exit()

    return apm_date


if __name__ == "__main__":
    
    app_jwt = login_app()

    if app_jwt:
        csv_sections = read_csv("data/data.csv")

        for name, df in csv_sections.items():
            print(f"Section: {name}")
            print(df)
            print("\n")

            load_data(name, df, app_jwt)

        schedule_appointment(app_jwt)

    else:
        logging.error("No JWT, no party!!")
    
