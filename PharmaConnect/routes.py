from flask import render_template,request,redirect,session,flash
from models import Chemist,Doctor,Patient
from flask_login import login_user,logout_user,current_user,login_required
from datetime import datetime
from api import YOUR_API_KEY

def register_routes(app,db,bcrypt):

    def bot(input):

        message = input.lower()

        if "hello" in message:
            return "Hi there! How can I help you?"
        elif "appointment" in message:
            return "You can book appointments in the 'Book Appointment' section."
        elif "report" in message:
            return "Your latest reports are available under 'View Reports'."
        elif "prescription" in message:
            return "Prescriptions are under the 'View Prescriptions' section."
        else:
            from groq import Groq

            client = Groq(
                api_key=YOUR_API_KEY,
            )
            system_prom=(
                "You are an assistant for medical and pharmacy tasks"
                "Use the following pieces of retrived context to answer"
                "the question.If you don't know the answer,say thank you"
                "don't know.Use three sentence maximun and keep the"
                "answer concise.If the question is not related to medical"
                "or pharmacy, say sorry i dont know the answer."
                "\n\n"
                "{context}"
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prom,
                    },
                    {
                        "role": "user",
                        "content": f"{input}",
                    }
                ],
                model="llama-3.3-70b-versatile",
                stream=False,
            )
            return chat_completion.choices[0].message.content
        
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
                chemistEmail = request.form.get('chemistemail').lower()
                unhash_cpassword = request.form.get('chemistpassword')

                password = bcrypt.generate_password_hash(unhash_cpassword)

                chemist = Chemist(shopname=shopname,chemistName=chemistName,chemistEmail=chemistEmail,password=password)
                db.session.add(chemist)
                db.session.commit()

                return redirect('/login')
            
            elif user_type == "doctor":
                hospitalname = request.form.get('hospitalname')
                doctorName = request.form.get('doctorname')
                doctorEmail = request.form.get('doctoremail').lower()
                unhash_dpassword = request.form.get('doctorpassword')

                password = bcrypt.generate_password_hash(unhash_dpassword)

                doctor = Doctor(hospitalname=hospitalname,doctorName=doctorName,doctorEmail=doctorEmail,password=password)
                db.session.add(doctor)
                db.session.commit()

                return redirect('/login')

            elif user_type == "patient":
                patientName = request.form.get('patientname')
                patientEmail = request.form.get('patientemail').lower()
                dob_str = request.form.get('patientdob')
                patientdob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                unhash_ppassword = request.form.get('patientpassword')

                password = bcrypt.generate_password_hash(unhash_ppassword)

                patient = Patient(patientdob=patientdob,patientName=patientName,patientEmail=patientEmail,password=password)
                db.session.add(patient)
                db.session.commit()

                return redirect('/login')

            
            else:
                return "Something Went Worng!"

    
    @app.route('/login',methods = ['GET','POST'])
    def login():

        if request.method == "GET":
            error = session.pop('login_error', None)
            active_tab = session.pop('active_tab', None)
            return render_template('login.html', error=error, active_tab=active_tab)
        elif request.method == "POST":
            user_type = request.form.get('user_type')

            if user_type == "chemist":
                chemistEmail = request.form.get('chemist_email').lower()
                cpassword = request.form.get('chemist_password')

                chemist = Chemist.query.filter(Chemist.chemistEmail == chemistEmail).first()
                if chemist is None:
                    session['login_error'] = "No user found"
                    session['active_tab'] = "chemist"
                    return redirect('/login')
                if bcrypt.check_password_hash(chemist.password,cpassword):
                    login_user(chemist)
                    session['user_type'] = 'chemist'
                    return redirect('/chemist')
                else:
                    session['login_error'] = "Wrong Password"
                    session['active_tab'] = "chemist"
                    return redirect('/login')

            elif user_type == "doctor":
                doctorEmail = request.form.get('doctor_email').lower()
                dpassword = request.form.get('doctor_password')

                doctor = Doctor.query.filter(Doctor.doctorEmail == doctorEmail).first()
                if doctor is None:
                    session['login_error'] = "No user found"
                    session['active_tab'] = "doctor"
                    return redirect('/login')
                if bcrypt.check_password_hash(doctor.password ,dpassword):
                    login_user(doctor)
                    session['user_type'] = 'doctor'
                    return redirect('/doctor')
                else:
                    session['login_error'] = "Wrong Password"
                    session['active_tab'] = "doctor"
                    return redirect('/login')
                
            elif user_type == "patient":

                patientEmail = request.form.get('patient_email').lower()
                ppassword = request.form.get('patient_password')

                patient = Patient.query.filter(Patient.patientEmail == patientEmail).first()
                if patient is None:
                    session['login_error'] = "No user found"
                    session['active_tab'] = "patient"
                    return redirect('/login')
                if bcrypt.check_password_hash(patient.password,ppassword):
                    login_user(patient)
                    session['user_type'] = "patient"
                    return redirect('/patient')
                else:
                    session['login_error'] = "Wrong Password"
                    session['active_tab'] = "patient"
                    return redirect('/login')


            else:
                return "Something Went Wrong!"
            
    @app.route('/logout')
    @login_required
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
    
    @app.route('/patient',methods=['GET','POST'])
    @login_required
    def patient():
        patient = Patient.query.get(current_user.patientId)
        if request.method == "GET":
            return render_template('patient.html',
                                   name=patient.patientName,
                                   email=patient.patientEmail,
                                   dob=patient.patientdob,
                                   phone=patient.contactNumber,
                                   address = patient.address)
        else:
            contactno = request.form.get('patient_phone')
            address = request.form.get('patient_address')
            if patient:
                patient.contactNumber = str(contactno)
                patient.address = str(address)
                db.session.commit()
            return render_template('patient.html',
                                   name=patient.patientName,
                                   email=patient.patientEmail,
                                   dob=patient.patientdob,
                                   phone=patient.contactNumber,
                                   address = patient.address)


    
    @app.route('/chat',methods=['GET','POST'])
    @login_required
    def chat():
        if request.method == "GET":
            return render_template("chatbot_section.html")
        else:
            user_input =request.form.get("user_input")
            bot_response = bot(user_input)
            return render_template('chatbot_section.html',user_input = user_input,bot_response=bot_response)
