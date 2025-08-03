from flask import render_template,request,redirect,session,flash,jsonify,url_for,json,make_response
from models import Chemist,Doctor,Patient,Medicine,Sales,Customers,Purchase,Appointments
from flask_login import login_user,logout_user,current_user,login_required
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from api import YOUR_API_KEY,BASE_64_STRING
import pdfkit
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


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
    
    def send_email_with_pdf(pdf,receiver,billId):
        subject = "Subject: Your Medicine Bill"
        body = "Thanks for purchase."
        host = "smtp.gmail.com"
        port = 465
        user_name = "kushal.limit@gmail.com"  # Email address
        password = "wbsi hlxp hizf xsnz"  # App password

        context = ssl.create_default_context()

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = user_name
        msg['To'] = receiver
        msg['Subject'] = subject

        # Attach the body of the email
        msg.attach(MIMEText(body, 'plain'))

         # FIX: Attach the PDF directly from the pdf_content variable.
        # The 'with open(...)' block was removed as it was causing the error.
        attach_part = MIMEApplication(pdf, _subtype="pdf")
        # FIX: Provide a specific filename for the attachment. The original code used an undefined variable 'pdf_path'.
        attach_part.add_header('Content-Disposition', 'attachment', filename=f"{billId}.pdf")
        msg.attach(attach_part)

        try:
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user_name, password)
                server.sendmail(user_name, receiver, msg.as_string())
            print("Email with PDF sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

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
            med = []
            for i in medicineList:
                med.append({'id':i.medicineId,'name':i.medicineName,'price':i.medicinePrice,'batch':i.batchNo,'quantity':i.stock})
            
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
                    companyName = request.form.get('company_name').upper()
                    expireMonths = int(request.form.get('expiry_date'))
                    expiryDate = get_date(manufactureDate,expireMonths)

                    try:
                        medicine = Medicine(medicineName=medicineName,
                                            batchNo=batchNo,
                                            stock=medicineQuantity,
                                            medicinePrice=medicinePrice,
                                            companyName=companyName,
                                            manufactureDate=manufactureDate,
                                            expiryDate=expiryDate,
                                            chemistId=current_user.chemistId)
                        db.session.add(medicine)
                        db.session.commit()
                        flash(f'Medicine "{medicineName}" registered successfully!', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Error registering medicine: {str(e)}', 'error')
                    
                    return redirect(url_for('chemist')+'#register-drug')
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
    
    # Medicine Data Route
    @app.route('/search-medicine')
    def search_medicine():
        medicineList = Medicine.query.all()
        med = []
        for i in medicineList:
            med.append({'id':i.medicineId,'name':i.medicineName,'price':i.medicinePrice,'batch':i.batchNo,'quantity':i.stock})
        return jsonify(med)
    
    # New Route to get expired and expiring medicines
    @app.route('/expired-and-expiring-medicines')
    @login_required
    def expired_and_expiring_medicines():
        if session['user_type'] != "chemist":
            return jsonify({"error": "Unauthorized"}), 403

        today = date.today()
        # End date for "about to expire" (today + 30 days)
        in_30_days = today + timedelta(days=30)
        
        # Get medicines that are already expired
        expired = Medicine.query.filter(
            Medicine.expiryDate < today,
            Medicine.chemistId == current_user.chemistId
        ).all()
        
        # Get medicines that are about to expire in the next 30 days
        about_to_expire = Medicine.query.filter(
            Medicine.expiryDate.between(today, in_30_days),
            Medicine.chemistId == current_user.chemistId
        ).all()

        # Helper function to serialize medicine objects
        def serialize_medicine(med_list):
            return [{
                'name': m.medicineName,
                'batch': m.batchNo,
                'expiryDate': m.expiryDate.isoformat(),
                'quantity': m.stock
            } for m in med_list]
        
        return jsonify({
            'expired': serialize_medicine(expired),
            'about_to_expire': serialize_medicine(about_to_expire)
        })

    @app.route('/generate-bill',methods=['POST'])
    @login_required
    def generateBill():
        data = request.form.get('billing_cart')
        name = request.form.get('customer_name')
        email = request.form.get('customer_email').lower()
        billAmount = request.form.get('bill_amount')
        if data:
            cart = json.loads(data)
            billId = Sales.query.filter(Sales.chemistId == current_user.chemistId).order_by(Sales.salesId.desc()).limit(1).first()
            if billId:
                billId = billId.salesId + 1
            else:
                billId = 1
            
            try:
                for i in cart:
                    medicine_name = i['name']
                    quantity = i['quantity']
                    totalPrice = float(i['total'])
                    pricePerUnit = float(i['price'])
                    date = datetime.now().date()
                    chemistId = current_user.chemistId

                    # Sales Input
                    sales = Sales(billId=billId,name=medicine_name,quantity=quantity,pricePerUnit=pricePerUnit,totalPrice=totalPrice,date=date,chemistId=chemistId)
                    db.session.add(sales)

                    medicine = Medicine.query.filter(Medicine.medicineName == medicine_name).first()
                    medicine.stock -= quantity
                
                # Checks Customer
                customer = Customers.query.filter(Customers.customerEmail == email).first()
                if customer is None:
                    customer = Customers(customerEmail=email,customerName=name)
                    db.session.add(customer)
                    db.session.commit()
                    db.session.flush()  
                    db.session.refresh(customer)
                    customerId = customer.customerId
                else:
                    customerId = customer.customerId

                # Purchase table input
                purchase = Purchase(customerId=customerId,billAmount=float(billAmount),chemistId=chemistId,billId=billId)
                db.session.add(purchase)
                db.session.commit()

                if billId:
                    return redirect(url_for('generate_pdf', billId=billId))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error generating bill: {str(e)}", 'error')
                return redirect(url_for('chemist')+'#billing')
            

        else:
            pass
        return redirect(url_for('chemist')+'#billing')
    
    @app.route('/generate-pdf/<int:billId>')
    @login_required
    def generate_pdf(billId):
        if session.get('user_type') != 'chemist':
            return redirect(url_for('permission'))

        # Fetch all necessary data for the bill from the database
        chemist = Chemist.query.get(current_user.chemistId)
        purchase_info = Purchase.query.filter_by(billId=billId, chemistId=current_user.chemistId).first()

        if not purchase_info:
            flash('Bill not found!')
            return redirect(url_for('chemist'))

        customer = Customers.query.get(purchase_info.customerId)
        sales_items = Sales.query.filter_by(billId=billId, chemistId=current_user.chemistId).all()
        
        # FIX: Add a failsafe to ensure all prices are floats before rendering
        # This handles cases where data might have been stored as a string in the DB
        for item in sales_items:
            item.pricePerUnit = float(item.pricePerUnit)
            item.totalPrice = float(item.totalPrice)
        purchase_info.billAmount = float(purchase_info.billAmount)


        # Render an HTML template with the bill information
        rendered_html = render_template('bill_template.html',
                                        chemist=chemist,
                                        customer=customer,
                                        purchase=purchase_info,
                                        sales_items=sales_items,
                                        billId=billId,
                                        img_string = BASE_64_STRING,
                                        date=datetime.now().strftime("%Y-%m-%d"))

        try:
            # IMPORTANT: You must provide the correct path to the wkhtmltopdf executable.
            # 1. Find where 'wkhtmltopdf.exe' is located on your system.
            # 2. Replace the path below with your actual path.
            # 3. Use a raw string (r'...') to avoid issues with backslashes.
            path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            
            # Generate the PDF using the configuration
            pdf = pdfkit.from_string(rendered_html, False, configuration=config)

            if customer and customer.customerEmail:
                send_email_with_pdf(pdf, customer.customerEmail, billId)

            flash('Bill generated and sent to customer successfully!', 'success')
            return redirect(url_for('chemist')+'#billing')

        except IOError as e:
            # This will catch the "No wkhtmltopdf executable found" error
            print(f"Error generating PDF: {e}. Please ensure wkhtmltopdf is installed and the path in routes.py is correct.", 'error')
            flash('Error generating PDF.', 'error')
            return redirect(url_for('chemist') + '#billing')