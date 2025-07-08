from flask import render_template,request
from models import User

def register_routes(app,db):
    
    @app.route('/')
    def home():
        return render_template('homepage.html')
    
    @app.route('/signup',methods = ['GET','POST'])
    def signup():
        if request.method == "GET":
            return render_template('signup.html')
        else:
            pass
    
    @app.route('/login',methods = ['GET','POST'])
    def login():

        if request.method == "GET":
            return render_template('login.html')
        else:
            pass