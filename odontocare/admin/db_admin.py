from db_init import db

class User(db.Model):
    """
    User model for the application
    """
    __tablename__ = "users"

    usr_id = db.Column(db.Integer, primary_key=True)
    usr_name = db.Column(db.String(100), nullable=False, unique=True)
    usr_pwd = db.Column(db.String(100), nullable=False, unique=False)
    usr_role = db.Column(db.String(100), nullable=False)

    usr_doctors = db.relationship("Doctor", back_populates="doc_users")
    usr_patients = db.relationship("Patient", backref="pat_users")
    usr_appointments = db.relationship("Appointment", back_populates="apm_users")

    def to_dict(self):
        return {"usr_id": self.usr_id, "usr_name": self.usr_name, "usr_role": self.usr_role, "doctor": [doc.to_dict() for doc in self.usr_doctors], "patient": [pat.to_dict() for pat in self.usr_patients], "appointments": [apm.to_dict() for apm in self.usr_appointments]}


class Doctor(db.Model):
    """
    Doctor model for the application
    """
    __tablename__ = "doctors"

    doc_id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.usr_id'), nullable=False)
    doc_name = db.Column(db.String(100), nullable=False, unique=True)
    doc_specialty = db.Column(db.String(100), nullable=False, unique=False)

    doc_users = db.relationship("User", back_populates="usr_doctors")
    doc_appointments = db.relationship("Appointment", back_populates="apm_doctor")

    def to_dict(self):
        return {"doc_id": self.doc_id, "usr_id": self.usr_id, "doc_name": self.doc_name, "doc_specialty": self.doc_specialty}

class Patient(db.Model):
    """
    Patient model for the application
    """
    __tablename__ = "patients"

    pat_id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.usr_id'), nullable=False)
    pat_name = db.Column(db.String(100), nullable=False, unique=True)
    pat_phone = db.Column(db.String(100), nullable=False, unique=False)
    pat_active = db.Column(db.Boolean, nullable=False, unique=False)

    pat_appointments = db.relationship("Appointment", back_populates="apm_patient")

    def to_dict(self):
        return {"pat_id": self.pat_id, "usr_id": self.usr_id, "pat_name": self.pat_name, "pat_phone": self.pat_phone, "pat_active": self.pat_active}

class MedicalCentre(db.Model):
    """
    Medical Centre model for the application
    """
    __tablename__ = "medical_centres"

    mdc_id = db.Column(db.Integer, primary_key=True)
    mdc_alias = db.Column(db.String(100), nullable=False, unique=True)
    mdc_name = db.Column(db.String(100), nullable=False, unique=True)
    mdc_address = db.Column(db.String(200), nullable=False, unique=False)

    mdc_appointments = db.relationship("Appointment", back_populates="apm_medical_centre")

    def to_dict(self):
        return {"mdc_id": self.mdc_id, "mdc_alias": self.mdc_alias, "mdc_name": self.mdc_name, "mdc_address": self.mdc_address}
