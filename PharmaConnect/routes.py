from flask import render_template,request,redirect,session
from models import Chemist,Doctor
from flask_login import login_user,logout_user,current_user,login_required

def register_routes(app,db,bcrypt):
    
    @app.route('/')
    def home():
        return render_template('homepage.html')
    
    @app.route('/signup',methods = ['GET','POST'])
    def signup():
        if request.method == "GET":
            return render_template('signup.html')
        elif request.method == "POST":
            user_type = request.form.get('user_type')
            if user_type == "chemist":
                shopname = request.form.get('shopname')
                chemistName = request.form.get('chemistname')
                chemistEmail = request.form.get('chemistemail')
                unhash_cpassword = request.form.get('chemistpassword')

                password = bcrypt.generate_password_hash(unhash_cpassword)

                chemist = Chemist(shopname=shopname,chemistName=chemistName,chemistEmail=chemistEmail,password=password)
                db.session.add(chemist)
                db.session.commit()

                return redirect('/login')
            
            elif user_type == "doctor":
                hospitalname = request.form.get('hospitalname')
                doctorName = request.form.get('doctorname')
                doctorEmail = request.form.get('doctoremail')
                unhash_dpassword = request.form.get('doctorpassword')

                password = bcrypt.generate_password_hash(unhash_dpassword)

                doctor = Doctor(hospitalname=hospitalname,doctorName=doctorName,doctorEmail=doctorEmail,password=password)
                db.session.add(doctor)
                db.session.commit()

                return redirect('/login')
            
            else:
                return "Something Went Worng!"

    
    @app.route('/login',methods = ['GET','POST'])
    def login():

        if request.method == "GET":
            return render_template('login.html')
        elif request.method == "POST":
            user_type = request.form.get('user_type')

            if user_type == "chemist":
                chemistEmail = request.form.get('chemist_email')
                cpassword = request.form.get('chemist_password')

                chemist = Chemist.query.filter(Chemist.chemistEmail == chemistEmail).first()
                if bcrypt.check_password_hash(chemist.password,cpassword):
                    login_user(chemist)
                    session['user_type'] = 'chemist'
                    print(current_user.chemistName)
                    return redirect('/chemist')
                else:
                    return "Wrong Password"

            elif user_type == "doctor":
                doctorEmail = request.form.get('doctor_email')
                dpassword = request.form.get('doctor_password')

                doctor = Doctor.query.filter(Doctor.doctorEmail == doctorEmail).first()
                if bcrypt.check_password_hash(doctor.password ,dpassword):
                    login_user(doctor)
                    print(current_user.doctorName)
                    session['user_type'] = 'doctor'
                    return redirect('/doctor')
                else:
                    return "Wrong Password"

            else:
                return "Something Went Wrong!"
            
    @app.route('/logout')
    def logout():
        logout_user()
        session.pop('user_type',None)
        return redirect('/')
    
    @app.route('/chemist')
    @login_required
    def chemist():
        return render_template('chemist.html')
    
    @app.route('/doctor')
    @login_required
    def doctor():
        return render_template('doctor.html')