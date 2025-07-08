from app import db

class User(db.Model):
    __tablename__ = 'user'

    uid = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text,nullable = False)
    
    def __repr__(self):
        return f"Name : {self.name}"