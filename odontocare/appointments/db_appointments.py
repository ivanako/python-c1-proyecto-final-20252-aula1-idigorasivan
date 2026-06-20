from db_init import db

class Appointment(db.Model):
    """
    Appointment model for the application
    """

    __tablename__ = "appointments"

    __table_args__ = (
        db.UniqueConstraint('doc_id', 'apm_date', name='ix_apm_doc_date'),
    )

    apm_id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('users.usr_id'), nullable=False)
    pat_id = db.Column(db.Integer, db.ForeignKey('patients.pat_id'), nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey('doctors.doc_id'), nullable=False)
    mdc_id = db.Column(db.Integer, db.ForeignKey('medical_centres.mdc_id'), nullable=False)
    apm_reason = db.Column(db.String(200), nullable=False)
    apm_date = db.Column(db.DateTime, nullable=False)
    apm_status = db.Column(db.String(200), nullable=False)

    apm_users = db.relationship("User", back_populates="usr_appointments")
    apm_doctor = db.relationship("Doctor", back_populates="doc_appointments")
    apm_patient = db.relationship("Patient", back_populates="pat_appointments")
    apm_medical_centre = db.relationship("MedicalCentre", back_populates="mdc_appointments")

    def to_dict(self):
        return {"apm_id": self.apm_id, "usr_id": self.usr_id, "apm_date": self.apm_date, "apm_reason": self.apm_reason, "apm_status": self.apm_status, "doctor": self.apm_doctor.to_dict() if self.apm_doctor else None, "patient": self.apm_patient.to_dict() if self.apm_patient else None, "medical_centre": self.apm_medical_centre.to_dict() if self.apm_medical_centre else None}
