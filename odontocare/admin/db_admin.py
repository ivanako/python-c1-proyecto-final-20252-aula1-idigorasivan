from db_init import db

class User(db.Model):
    __tablename__ = "users"

    usr_id = db.Column(db.Integer, primary_key=True)
    usr_name = db.Column(db.String(100), nullable=False, unique=True)
    usr_pwd = db.Column(db.String(100), nullable=False, unique=False)
    usr_role = db.Column(db.String(100), nullable=False)

    usr_doctors = db.relationship("Doctor", back_populates="doc_users", uselist=False)
    usr_patients = db.relationship("Patient", backref="pat_users", uselist=False)
    usr_appointments = db.relationship("Appointment", back_populates="apm_users", uselist=True)

    def to_dict(self):
        return {"usr_id": self.usr_id, "usr_name": self.usr_name, "usr_role": self.usr_role}

class Doctor(db.Model):
    __tablename__ = "doctors"

    doc_id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.usr_id'), nullable=False)
    doc_name = db.Column(db.String(100), nullable=False, unique=True)
    doc_specialty = db.Column(db.String(100), nullable=False, unique=False)

    doc_users = db.relationship("User", back_populates="usr_doctors", uselist=False)
    doc_appointments = db.relationship("Appointment", back_populates="apm_doctors", uselist=True)

    def to_dict(self):
        return {"doc_id": self.doc_id, "usr_id": self.usr_id, "doc_name": self.doc_name, "doc_specialty": self.doc_specialty}

class Patient(db.Model):
    __tablename__ = "patients"

    pat_id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.usr_id'), nullable=False)
    pat_name = db.Column(db.String(100), nullable=False, unique=True)
    pat_phone = db.Column(db.String(100), nullable=False, unique=False)
    pat_status = db.Column(db.String(50), nullable=False, unique=False)

    pat_appointments = db.relationship("Appointment", backref="apm_patients", uselist=True)

    def to_dict(self):
        return {"pat_id": self.pat_id, "usr_id": self.usr_id, "pat_name": self.pat_name, "pat_phone": self.pat_phone, "pat_status": self.pat_status}

class MedicalCentre(db.Model):
    __tablename__ = "medical_centres"

    mdc_id = db.Column(db.Integer, primary_key=True)
    mdc_alias = db.Column(db.String(100), nullable=False, unique=True)
    mdc_name = db.Column(db.String(100), nullable=False, unique=True)
    mdc_address = db.Column(db.String(200), nullable=False, unique=False)

    mdc_appointments = db.relationship("Appointment", backref="apm_medical_centres", uselist=True)

    def to_dict(self):
        return {"mdc_id": self.mdc_id, "mdc_alias": self.mdc_alias, "mdc_name": self.mdc_name, "mdc_address": self.mdc_address}