from app import db
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

class Chemist(db.Model,UserMixin):
    __tablename__ = 'chemist'

    chemistId = db.Column(db.Integer,primary_key=True)
    shopname = db.Column(db.String,nullable=False)
    chemistName = db.Column(db.String,nullable=False)
    chemistEmail = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.String,nullable=False)
    contactNumber = db.Column(db.String)
    address = db.Column(db.String)

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
    address = db.Column(db.String)
    contactNumber = db.Column(db.String)
    specialization = db.Column(db.String)

    def __repr__(self):
            return ""
    
    def get_id(self):
          return self.doctorId
    
class Patient(db.Model,UserMixin):
    __tablename__ = "patient"
    patientId = db.Column(db.Integer,primary_key=True)
    patientdob = db.Column(db.Date,nullable=False)
    patientName = db.Column(db.String,nullable=False)
    patientEmail = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.String,nullable=False)
    contactNumber = db.Column(db.String)
    address = db.Column(db.String)
    gender = db.Column(db.String)

    def __repr__(self):
            return ""
    
    def get_id(self):
          return self.patientId
    
class Medicine(db.Model):
    __tablename__ = 'medicines'

    medicineId = db.Column(db.Integer,primary_key=True)
    medicineName = db.Column(db.String,nullable=False)
    batchNo = db.Column(db.String,nullable=False)
    stock = db.Column(db.Integer,nullable=False)
    medicinePrice = db.Column(db.String,nullable=False)
    companyName = db.Column(db.String,nullable=False)
    expiryDate = db.Column(db.Date,nullable=False)
    manufactureDate = db.Column(db.Date,nullable=False)
    	
    def __repr__(self):
          return ""
    
    def get_id(self):
          return self.medicineId
    
class Sales(db.Model):
      __tablename__ = 'sales'
      
      salesId = db.Column(db.Integer,primary_key=True)
      billId = db.Column(db.Integer,nullable=False)
      name = db.Column(db.String,nullable=False)
      quantity = db.Column(db.Integer,nullable=False)
      pricePerUnit = db.Column(db.String,nullable=False)
      totalPrice = db.Column(db.Integer,nullable=False)
      date = db.Column(db.Date,nullable=False)
      chemistId = db.Column(db.Integer,nullable=False)

      def __repr__(self):
          return ""
      
      def get_id(self):
          return self.salesId

class Customers(db.Model):
      __tablename__ = 'customers'

      customerId = db.Column(db.Integer,primary_key=True)
      customerEmail = db.Column(db.String,nullable=False)
      customerName = db.Column(db.String,nullable=False)

      def __repr__(self):
          return ""
      
      def get_id(self):
          return self.customerId
      
class Purchase(db.Model):
     __tablename__ = 'purchase'

     purchaseId = db.Column(db.Integer,primary_key=True)
     billId = db.Column(db.Integer,nullable=False)
     customerId = db.Column(db.Integer,nullable=False)
     billAmount = db.Column(db.Integer,nullable=False)
     chemistId = db.Column(db.Integer,nullable=False)

     def __repr__(self):
          return ""
     
     def get_id(self):
          return self.purchaseId
     
class Appointments(db.Model):
     __tablename__ = 'appointment'

     appointmentId = db.Column(db.Integer,primary_key=True)
     doctorId = db.Column(db.Integer,nullable = False)
     appointmentDate = db.Column(db.Date,nullable=False)
     patientId = db.Column(db.Integer,nullable=False)
     appointmentTime = db.Column(db.String,nullable=False)

     def __repr__(self):
          return ""
     
     def get_id(self):
          return self.appointmentId