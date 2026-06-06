import jwt
import os

from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from functools import wraps
from logging import info
from sqlalchemy.exc import IntegrityError

from db_init import db
from odontocare.admin.db_admin import User, Doctor, Patient, MedicalCentre
from odontocare.admin.auth import jwt_required

bp_users = Blueprint("admin", __name__, url_prefix="/admin/")


@bp_users.get("/users")
@jwt_required()
def list_users(payload) -> tuple[jsonify, int]:
    usr_list = User.query.all()
    return jsonify([usr.to_dict() for usr in usr_list]), 200

@bp_users.post("/users")
@jwt_required(roles=["admin"])
def create_user(payload):
    usr_json = request.get_json()

    usr_db = User(usr_name=usr_json.get("usr_name"), usr_pwd=usr_json.get("usr_pwd"), usr_role=usr_json.get("usr_role"))

    try:
        db.session.add(usr_db)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Duplicate user"}), 409

    return jsonify(usr_db.to_dict()), 201

@bp_users.get("/users/<usr_id>")
@jwt_required()
def get_user_by_id(payload, usr_id):
    usr_db = User.query.get_or_404(usr_id)
    return jsonify(usr_db.to_dict()), 200

@bp_users.get("/users/<usr_name>")
@jwt_required()
def get_user_by_username(payload, usr_name):
    usr_db = User.query.filter_by(usr_name=usr_name).first_or_404()
    return jsonify(usr_db.to_dict()), 200

@bp_users.put("/users/<usr_id>")
@jwt_required()
def update_user(payload, usr_id):
    usr_db = User.query.get(usr_id)
    
    if not usr_db:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    usr_db.usr_name = data.get("usr_name", usr_db.usr_name)
    usr_db.usr_pwd = data.get("usr_pwd", usr_db.usr_pwd)
    usr_db.usr_role = data.get("usr_role", usr_db.usr_role)

    db.session.commit()

    return jsonify(usr_db.to_dict()), 200

@bp_users.delete("/users/<usr_id>")
@jwt_required()
def delete_user(payload, usr_id):
    usr_db = User.query.get(usr_id)

    if not usr_db:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(usr_db)
    db.session.commit()

    return jsonify({"message": "User deleted"}), 200


#####################################
########## DOCTORS ##########
#####################################
@bp_users.get("/doctors/<doc_id>")
@jwt_required()
def get_doctor(payload, doc_id):
    doc_db = Doctor.query.get_or_404(doc_id)
    return jsonify(doc_db.to_dict()), 200

@bp_users.post("/doctors")
@jwt_required(roles=["admin"])
def create_doctor(payload):
    doc_json = request.get_json()

    try:
        with db.session.begin():
            usr_db = User(usr_name=doc_json.get("usr_name"), usr_pwd=doc_json.get("usr_pwd"), usr_role="doctor")
            db.session.add(usr_db)
            db.session.flush()
        
            doc_db = Doctor(usr_id=usr_db.usr_id, doc_name=doc_json.get("doc_name"), doc_specialty=doc_json.get("doc_specialty"))
            db.session.add(doc_db)
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Duplicate doctor"}), 409

    return jsonify(doc_db.to_dict()), 201

@bp_users.get("/doctors")
@jwt_required()
def list_doctors(payload) -> tuple[jsonify, int]:
    doc_list = Doctor.query.all()
    return jsonify([doc.to_dict() for doc in doc_list]), 200


#####################################
########## PATIENTS ##########
#####################################
@bp_users.get("/patients")
@jwt_required()
def list_patients(payload) -> tuple[jsonify, int]:
    pat_list = Patient.query.all()
    return jsonify([pat.to_dict() for pat in pat_list]), 200

@bp_users.post("/patients")
@jwt_required(roles=["admin"])
def create_patient(payload):
    pat_json = request.get_json()

    try:
        with db.session.begin():
            usr_db = User(usr_name=pat_json.get("usr_name"), usr_pwd=pat_json.get("usr_pwd"), usr_role="patient")
            db.session.add(usr_db)
            db.session.flush()  # Ensure usr_db.usr_id is populated before using it in the Patient record

            pat_db = Patient(usr_id=usr_db.usr_id, pat_name=pat_json.get("pat_name"), pat_phone=pat_json.get("pat_phone"), pat_status=pat_json.get("pat_status"))
            db.session.add(pat_db)
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Duplicate patient"}), 409

    return jsonify(pat_db.to_dict()), 201

@bp_users.get("/patients/<pat_id>")
@jwt_required()
def get_patient(payload, pat_id):
    pat_db = Patient.query.get_or_404(pat_id)
    return jsonify(pat_db.to_dict()), 200


#####################################
########## MEDICAL CENTRES ##########
#####################################
@bp_users.get("/medical-centres")
@jwt_required()
def list_medical_centres(payload) -> tuple[jsonify, int]:
    mdc_list = MedicalCentre.query.all()
    return jsonify([mdc.to_dict() for mdc in mdc_list]), 200

@bp_users.post("/medical-centres")
@jwt_required(roles=["admin"])
def create_medical_centre(payload):
    mdc_json = request.get_json()
    
    try:
        mdc_db = MedicalCentre(mdc_alias=mdc_json.get("mdc_alias"), mdc_name=mdc_json.get("mdc_name"), mdc_address=mdc_json.get("mdc_address"))
    
        db.session.add(mdc_db)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Duplicate medical centre"}), 409

    return jsonify(mdc_db.to_dict()), 201

@bp_users.get("/medical-centres/<mdc_id>")
@jwt_required()
def get_medical_centre(payload, mdc_id):
    mdc_db = MedicalCentre.query.get_or_404(mdc_id)
    return jsonify(mdc_db.to_dict()), 200
