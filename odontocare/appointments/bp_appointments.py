from datetime import datetime
from logging import info
import os
from flask import Blueprint, jsonify, request
import requests
from sqlalchemy.exc import IntegrityError

from db_init import db
from odontocare.admin.bp_admin import jwt_required
from odontocare.admin.db_admin import Doctor, MedicalCentre, Patient, User
from odontocare.appointments.db_appointments import Appointment

bp_appointments = Blueprint("appointments", __name__, url_prefix="/appointments/")

@bp_appointments.get("")
@jwt_required()
def list_appointments(payload) -> tuple[jsonify, int]:
    apm_list = Appointment.query.all()
    return jsonify([apm.to_dict() for apm in apm_list]), 200

@bp_appointments.get("/<int:apm_id>")
@jwt_required()
def get_appointment_by_id(payload, apm_id):
    apm_db = Appointment.query.get_or_404(apm_id)
    return jsonify(apm_db.to_dict()), 200

@bp_appointments.get("/doctor/<int:doc_id>")
@jwt_required()
def get_appointment_by_doctor(payload, doc_id):
    apm_db = Appointment.query.filter_by(doc_id=doc_id).all()
    return jsonify([apm.to_dict() for apm in apm_db]), 200

@bp_appointments.get("/search")
@jwt_required()
def list_appointments_by_date(payload) -> tuple[jsonify, int]:
    
    request_auth = request.headers.get("Authorization", "")
    jwt_token = request_auth.split(" ")[1]


    p_from = request.args.get("from", default=None)
    p_to = request.args.get("to", default=None)
    p_doc = request.args.get("doc_username", default=None)
    p_mdc = request.args.get("mdc_alias", default=None)



    try:
        if p_from:
            date_from = datetime.strptime(p_from, "%Y-%m-%d")
            date_from = datetime.combine(date_from, datetime.min.time())
        
        if p_to:
            date_to = datetime.strptime(p_to, "%Y-%m-%d")
            date_to = datetime.combine(date_to, datetime.max.time())

    except ValueError as ex_value:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if p_from and p_to:
        if date_from > date_to:
            return jsonify({"error": "The 'from' date must be earlier than the 'to' date"}), 400
        
        apm_qry = Appointment.query.filter(Appointment.apm_date >= date_from, Appointment.apm_date <= date_to)
    elif p_from:
        apm_qry = Appointment.query.filter(Appointment.apm_date >= date_from)
    elif p_to:
        apm_qry = Appointment.query.filter(Appointment.apm_date <= date_to)
    else:
        apm_qry = Appointment.query

    
    if payload["rol"] == "doctor":
        doc_id = fetch_doctor_by_id(jwt_token, p_usr_id=payload["sub"])

        if doc_id > 0:
            apm_list = Appointment.query.filter_by(doc_id=doc_id).all()
    
    if payload["rol"] == "reception":
        apm_list = apm_qry.all()
        
    if payload["rol"] == "admin":
        if p_doc:
            doc_id = fetch_doctor_by_name(jwt_token, p_doc_name=p_doc)
            apm_qry = apm_qry.filter_by(doc_id=doc_id)
        
        if p_mdc:
            mdc_id = fetch_medical_centre_by_alias(jwt_token, p_mdc_alias=p_mdc)
            apm_qry = apm_qry.filter_by(mdc_id=mdc_id)
        
        apm_list = apm_qry.all()
  

    return jsonify([apm.to_dict() for apm in apm_list]), 200

@bp_appointments.post("")
@jwt_required(roles=["admin", "patient", "doctor"])
def schedule_appointment(payload):
    apm_json = request.get_json()

    try:
        usr_id = payload.get("sub")
        doc_id = apm_json.get("doc_id")
        pat_id = apm_json.get("pat_id")
        mdc_id = apm_json.get("mdc_id")

        # Doctor and Patient users must exist before creating an appointment, so we can link them in the appointment record. If they don't exist, the query will return a 404 error.
        
        # apm_date = datetime.strptime(apm_json.get("apm_date"), "%Y-%m-%d %H:%M")
        apm_date = check_appointment_date(apm_json.get("apm_date"))

        apm_db = Appointment(
            usr_id=usr_id, 
            pat_id=pat_id, 
            doc_id=doc_id, 
            mdc_id=mdc_id, 
            apm_reason=apm_json.get("apm_reason"), 
            apm_date=apm_date, 
            apm_status=apm_json.get("apm_status")
        )

        db.session.add(apm_db)
        db.session.commit()
    except IntegrityError as ex_integrity:
        db.session.rollback()

        if hasattr(ex_integrity, "orig"):
            return jsonify({"error": ex_integrity.orig.args[0]}), 409
        else:
            return jsonify({"error": str(ex_integrity)}), 409

    except ValueError as ex_value:
        db.session.rollback()
        return jsonify({"error": str(ex_value)}), 400
    
    return jsonify(apm_db.to_dict()), 201


@bp_appointments.put("/<int:apm_id>")
@jwt_required(roles=["admin", "reception"])
def cancel_appointment(payload, apm_id):

    apm_db = Appointment.query.filter_by(apm_id=apm_id).first()

    if not apm_db:
        return jsonify({"error": f"Appointment with identifier {apm_id} does not exist"}), 404

    if apm_db.apm_status == "Cancelada":
        return jsonify({"message": "Appointment is already cancelled"}), 403

    apm_db.apm_status = "Cancelada"
    db.session.commit()

    return jsonify({"message": f"Appointment with identifier {apm_id} cancelled"}), 200


    

def check_appointment_date(date_aux: str) -> datetime:
    """
        Check the appointment date entered by the user and verify it is later than the current date
        
        parameters:
            date_aux (str): The appointment date string
        returns:
            datetime: The chosen appointment date
    """

    try:
        apm_date = datetime.strptime(date_aux, "%Y-%m-%d %H:%M")
        
        if apm_date <= datetime.now():
            raise ValueError("Please enter a date later than today")
        
    except ValueError as ex_value:
        raise ValueError(str(ex_value))

    return apm_date

def fetch_doctor_by_name(jwt_token: str, p_doc_name: str) -> int:
    """
        Fetch doctor identifier out of its name

        parameters:
            jwt_token (str): JWT to launch API endpoints
            p_doc_name (str): Doctor user name
        returns:
            int: Doctor identifier
    """

    doc_id = None

    req_session = requests.Session()

    req_headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    req_url = os.getenv("API_URL") + os.getenv("API_USERS_NAME").replace("<usr_name>", str(p_doc_name))

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        usr_db = req_response.json()

        if usr_db:
            doc_id = usr_db.get("doctor")[0].get("doc_id")

    except requests.exceptions.HTTPError as ex_http:
        doc_id = 0
    
    return doc_id

def fetch_doctor_by_id(jwt_token: str, p_usr_id: str) -> int:
    """
        Fetch doctor identifier out of its user identifier

        parameters:
            jwt_token (str): JWT to launch API endpoints
            p_usr_id (str): Doctor user identifier
        returns:
            int: Doctor identifier
    """

    doc_id = None

    req_session = requests.Session()

    req_headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    req_url = os.getenv("API_URL") + os.getenv("API_USERS_ID").replace("<usr_id>", p_usr_id)

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        usr_db = req_response.json()

        if usr_db:
            doc_id = usr_db.get("doctor")[0].get("doc_id")

    except requests.exceptions.HTTPError as ex_http:
        doc_id = 0
    
    return doc_id

def fetch_medical_centre_by_alias(jwt_token: str, p_mdc_alias: str) -> int:
    """
        Fetch Medical Centre identifier out of its alias

        parameters:
            jwt_token (str): JWT to launch API endpoints
            p_mdc_alias (str): Medical Centre alias
        returns:
            int: Medical Centre identifier
    """

    mdc_id = None

    req_session = requests.Session()

    req_headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    req_url = os.getenv("API_URL") + os.getenv("API_MEDICAL_CENTRE_ALIAS").replace("<mdc_alias>", p_mdc_alias)

    try:
        req_response = req_session.get(req_url, headers=req_headers)
        req_response.raise_for_status()

        mdc_db = req_response.json()

        if mdc_db:
            mdc_id = mdc_db.get("mdc_id")

    except requests.exceptions.HTTPError as ex_http:
        mdc_id = 0
    
    return mdc_id


