from flask import render_template,request,redirect,session,flash
from models import Chemist,Doctor,Patient,Medicine,Sales,Customers,Purchase,Appointments
from flask_login import login_user,logout_user,current_user,login_required
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api import YOUR_API_KEY

def register_routes(app,db,bcrypt):

    #Chat bot for user 
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
    
    # Get date for expiry based on months
    def get_date(start_date,n_month):
        date = start_date + relativedelta(months=n_month)
        return date

    # Homepage
    @app.route('/')
    def home():
        return render_template('homepage.html')
    
    # Singup Page
    @app.route('/signup',methods = ['GET','POST'])
    def signup():
        if request.method == "GET":
            return render_template('signup.html')
        elif request.method == "POST":
            # Chemist Signup
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
            
            # Doctor Signup
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

            # Patient Signup
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

    # Login Page
    @app.route('/login',methods = ['GET','POST'])
    def login():

        if request.method == "GET":
            error = session.pop('login_error', None)
            active_tab = session.pop('active_tab', None)
            return render_template('login.html', error=error, active_tab=active_tab)
        elif request.method == "POST":
            user_type = request.form.get('user_type')

            # Chemist Login
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
                
            # Doctor Login
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

            # Patient Login    
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

    # Logout        
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('user_type',None)
        return redirect('/')
    
    # Chemist Page
    @app.route('/chemist',methods=['GET','POST'])
    @login_required
    def chemist():
        if session['user_type'] == "chemist":
            chemist = Chemist.query.get(current_user.chemistId)
            medicineList = Medicine.query.all()
            if request.method == "POST":
                formName = request.form.get('form_name')

                # Profile Page
                if formName == "profile":
                    contactno = request.form.get('company_phone')
                    address = request.form.get('shop_address')
                    if chemist:
                        chemist.contactNumber = str(contactno)
                        chemist.address = str(address)
                        db.session.commit()
                    return render_template('chemist.html',
                                        name = chemist.shopname,
                                        address = chemist.address,
                                        email = chemist.chemistEmail,
                                        phone = chemist.contactNumber,
                                        medicineList=medicineList)
                
                # Register Medicine Page    
                elif formName == "register_med":
                    medicineName = request.form.get('medicine_name')
                    medicineQuantity = int(request.form.get('medicine_quantity'))
                    batchNo = request.form.get('batch_number')
                    manufactureDateStr = request.form.get('manufacturing_date')
                    manufactureDate = datetime.strptime(manufactureDateStr, "%Y-%m-%d").date()
                    medicinePrice = request.form.get('medicine_price')
                    companyName = request.form.get('company_name')
                    expireMonths = int(request.form.get('expiry_date'))
                    expiryDate = get_date(manufactureDate,expireMonths)

                    medicine = Medicine(medicineName=medicineName,
                                        batchNo=batchNo,
                                        medicineQuantity=medicineQuantity,
                                        medicinePrice=medicinePrice,
                                        companyName=companyName,
                                        manufactureDate=manufactureDate,
                                        expiryDate=expiryDate,
                                        medicineList=medicineList)
                    db.session.add(medicine)
                    db.session.commit()
                    return render_template('chemist.html',
                                    name = chemist.shopname,
                                    address = chemist.address,
                                    email = chemist.chemistEmail,
                                    phone = chemist.contactNumber,
                                    medicineList=medicineList)
            else:
                return render_template('chemist.html',
                                    name = chemist.shopname,
                                    address = chemist.address,
                                    email = chemist.chemistEmail,
                                    phone = chemist.contactNumber,
                                    medicineList=medicineList)
        else:
            return redirect('/permission')
    
    # Doctor Page
    @app.route('/doctor',methods=['GET','POST'])
    @login_required
    def doctor():
        if session['user_type'] == "doctor":
            doctor = Doctor.query.get(current_user.doctorId)
            if request.method == "POST":
                formName = request.form.get('form_name')    

                # Profile Page
                if formName == "profile":
                    contactno = request.form.get('contact_number')
                    specialization = request.form.get('doctor_specialization')
                    address = request.form.get('clinic_address')
                    if doctor:
                        doctor.contactNumber = str(contactno)
                        doctor.specialization = str(specialization)
                        doctor.address = str(address)
                        db.session.commit()
                    return render_template('doctor.html',
                                        name = doctor.doctorName,
                                        email = doctor.doctorEmail,
                                        phone = doctor.contactNumber,
                                        address = doctor.address,
                                        specialization = doctor.specialization)
            else:
                return render_template('doctor.html',
                                    name = doctor.doctorName,
                                    email = doctor.doctorEmail,
                                    phone = doctor.contactNumber,
                                    address = doctor.address,
                                    specialization = doctor.specialization)
        else:
            return redirect('/permission')
    
    # Patient Page
    @app.route('/patient',methods=['GET','POST'])
    @login_required
    def patient():
        if session['user_type'] == "patient":
            patient = Patient.query.get(current_user.patientId)
            if request.method == "GET":
                return render_template('patient.html',
                                    name=patient.patientName,
                                    email=patient.patientEmail,
                                    dob=patient.patientdob,
                                    phone=patient.contactNumber,
                                    address = patient.address)
            else:
                formName = request.form.get('form_name')

                # Profile Page
                if formName == "profile":
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
        else:
            return redirect('/permission')


    # Chatbot Route
    @app.route('/chat',methods=['GET','POST'])
    @login_required
    def chat():
        if request.method == "GET":
            return render_template("chatbot_section.html")
        else:
            user_input =request.form.get("user_input")
            bot_response = bot(user_input)
            return render_template('chatbot_section.html',user_input = user_input,bot_response=bot_response)
    

    # Permission error page
    @app.route('/permission')
    def permission():
        return render_template('permission.html')
