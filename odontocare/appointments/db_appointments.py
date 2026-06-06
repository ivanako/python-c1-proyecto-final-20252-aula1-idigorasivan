from db_init import db

class Appointment(db.Model):
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

    apm_users = db.relationship("User", back_populates="usr_appointments", uselist=False)
    apm_doctors = db.relationship("Doctor", back_populates="doc_appointments", uselist=False)

    def to_dict(self):
        return {"apm_id": self.apm_id, "usr_id": self.usr_id, "pat_id": self.pat_id, "doc_id": self.doc_id, "mdc_id": self.mdc_id, "apm_date": self.apm_date, "apm_reason": self.apm_reason, "apm_status": self.apm_status}