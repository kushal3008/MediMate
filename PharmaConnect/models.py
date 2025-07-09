from app import db
from flask_login import UserMixin

class Chemist(db.Model,UserMixin):
    __tablename__ = 'chemist'

    chemistId = db.Column(db.Integer,primary_key=True)
    shopname = db.Column(db.String,nullable=False)
    chemistName = db.Column(db.String,nullable=False)
    chemistEmail = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.String,nullable=False)

    def __repr__(self):
            return ""
    
    def get_id(self):
          return self.chemistId
    
class Doctor(db.Model,UserMixin):
    __tablename__ = 'doctor'

    doctorId = db.Column(db.Integer,primary_key=True)
    hospitalname = db.Column(db.String,nullable=False)
    doctorName = db.Column(db.String,nullable=False)
    doctorEmail = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.String,nullable=False)

    def __repr__(self):
            return ""
    
    def get_id(self):
          return self.doctorId
