
from datetime import datetime
from logging import info
from sqlite3 import IntegrityError
from flask import Blueprint, jsonify, request

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

@bp_appointments.get("/<apm_id>")
@jwt_required()
def get_appointment(payload, apm_id):
    apm_db = Appointment.query.get_or_404(apm_id)
    return jsonify(apm_db.to_dict()), 200

@bp_appointments.post("")
@jwt_required(["admin", "patient"])
def create_appointment(payload):
    apm_json = request.get_json()

    try:
        usr_id = payload.get("sub")
        usr_doc_db = User.query.filter_by(usr_name=apm_json.get("doc_username")).first()
        usr_pat_db = User.query.filter_by(usr_name=apm_json.get("pat_username")).first()
        mdc_db = MedicalCentre.query.filter_by(mdc_alias=apm_json.get("mdc_alias")).first()

        # Doctor and Patient users must exist before creating an appointment, so we can link them in the appointment record. If they don't exist, the query will return a 404 error.

        doc_id = Doctor.query.filter_by(usr_id=usr_doc_db.usr_id).first().doc_id
        pat_id = Patient.query.filter_by(usr_id=usr_pat_db.usr_id).first().pat_id
        
        apm_date = datetime.strptime(apm_json.get("apm_date"), "%Y-%m-%d %H:%M")

        apm_db = Appointment(usr_id=usr_id, pat_id=pat_id, doc_id=doc_id, mdc_id=mdc_db.mdc_id, apm_reason=apm_json.get("apm_reason"), apm_date=apm_date, apm_status=apm_json.get("apm_status"))

        db.session.add(apm_db)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        info(f"Duplicate medical centre record: {e}")
        return jsonify({"error": "Cannot create appointments with the same doctor at the same time"}), 409
    
    return jsonify(apm_db.to_dict()), 201
