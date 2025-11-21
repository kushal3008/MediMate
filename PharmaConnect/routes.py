from flask import render_template,request,redirect,session,flash,jsonify,url_for,json,make_response
from models import Chemist,Doctor,Patient,Medicine,Sales,Customers,Purchase,Appointments,OrderMedicine,Orders
from flask_login import login_user,logout_user,current_user,login_required
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from api import YOUR_API_KEY,BASE_64_STRING,MAPS_API_KEY
import pdfkit
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import json
from sqlalchemy import and_,func,union_all,Integer
import requests

def register_routes(app,db,bcrypt):

    def get_distance_matrix(location, api_key):
        """
        Calls the Google Maps Distance Matrix API to get travel distance and time
        for multiple origin-destination pairs.

        Args:
            location (dict): A dictionary containing 'originList', 'destinationList',
                            and 'destinationId' lists.
            api_key (str): Your Google Maps API key.

        Returns:
            list: A list of dictionaries with analysis results, or None if the request fails.
        """
        # Base URL for the Distance Matrix API
        base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

        origins = location['originList']
        destinations = location['destinationList']
        destinationId = location['destinationId']

        origins_str = "|".join(origins)
        destinations_str = "|".join(destinations)

        # Set up the parameters for the API request
        params = {
            "origins": origins_str,
            "destinations": destinations_str,
            "key": api_key
        }

        try:
            # Make the GET request to the API
            response = requests.get(base_url, params=params)
            
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()
            
            # Check for API errors in the response
            if data.get("status") != "OK":
                print(f"API Error: {data.get('error_message', 'No error message provided.')}")
                return None
            
            # Pass the data and destination IDs to the analysis function
            return analyze_distance_data(data, destinationId)

        except requests.exceptions.RequestException as e:
            # Handle network or HTTP-related errors
            print(f"Request failed: {e}")
            return None

    def analyze_distance_data(data, destination_ids):
        """
        Parses the JSON response from the Distance Matrix API to get original
        addresses, destination IDs, and distance for all origin-destination pairs.

        Args:
            data (dict): The JSON response from the get_distance_matrix function.
            destination_ids (list): A list of IDs corresponding to the destinations.

        Returns:
            list: A list of dictionaries, where each dictionary contains the
                origin, destination, destinationId, and distance for a single pair.
        """
        if not data or "rows" not in data or not data["rows"]:
            print("Invalid or empty data provided.")
            return []

        results = []
        # Loop through each origin address provided in the request
        for i, row in enumerate(data["rows"]):
            # Loop through each destination address for the current origin
            for j, element in enumerate(row["elements"]):
                # Check the status of the specific route
                if element["status"] == "OK":
                    origin_address = data["origin_addresses"][i]
                    destination_address = data["destination_addresses"][j]
                    distance = element["distance"]["text"]
                    duration = element["duration"]["text"]
                    
                    # Retrieve the destination ID using the same index
                    destination_id = destination_ids[j]

                    results.append({
                        "origin_address": origin_address,
                        "destination_address": destination_address,
                        "destination_id": destination_id,
                        "distance": distance,
                        "duration": duration
                    })
                else:
                    print(f"Route from '{data['origin_addresses'][i]}' to '{data['destination_addresses'][j]}' not found. Status: {element['status']}")
        
        return results

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
            medicineList = Medicine.query.filter_by(chemistId=current_user.chemistId).all()
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
                    flash("Profile Updated Successfully","success")
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
        
    @app.route('/order-medicine/<int:chemistId>',methods=['GET','POST'])
    @login_required
    def order_medicine(chemistId):
        if request.method == "GET":
            return render_template('order_medicine.html',chemistId=chemistId)
        else:
            billamount = 0
            orderId = Orders.query.order_by(Orders.orderId.desc()).limit(1).first()
            if orderId:
                orderId = orderId.orderId + 1
            else:
                orderId = 1 
            data = request.get_json()
            if data:
                cart = data.get('order_details')
                orderDate = datetime.now().date()
                print(cart)
                try:
                    for i in cart:
                        ordermedicine = OrderMedicine(orderId=orderId,
                                                    medicineId=i['id'],
                                                    quantity=i['quantity'],
                                                    medicineName = i['name'],
                                                    pricePerUnit = float(i['price']),
                                                    totalPrice = float(i['total']))
                        billamount += float(i['total'])
                        db.session.add(ordermedicine)
                    order = Orders(orderId=orderId,doctorId=current_user.doctorId,orderDate=orderDate,chemistId=chemistId,status="pending",billAmount=billamount)
                    db.session.add(order)
                    db.session.commit()
                    return jsonify({"success": True, "message": "Order Placed Successfully"}),200
                except Exception as e:
                    db.session.rollback()
                    return jsonify({"success": False, "message": f"An unexpected error occurred: {str(e)}"}), 500
            else:
                return jsonify({"success": False, "message": "No data provided"})

    
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
                                    address=patient.address,
                                    gender=patient.gender)
            else:
                formName = request.form.get('form_name')

                # Profile Page
                if formName == "profile":
                    contactno = request.form.get('patient_phone')
                    address = request.form.get('patient_address')
                    gender = request.form.get('patient_gender')
                    if patient:
                        patient.contactNumber = str(contactno)
                        patient.address = str(address)
                        patient.gender = str(gender)
                        db.session.commit()
                    
                    return render_template('patient.html',
                                        name=patient.patientName,
                                        email=patient.patientEmail,
                                        dob=patient.patientdob,
                                        phone=patient.contactNumber,
                                        address=patient.address,
                                        gender=patient.gender)
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
        user_type = request.args.get('user_type')
        if user_type == "chemist":
            medicineList = Medicine.query.filter_by(chemistId=current_user.chemistId).all()
            med = []
            for i in medicineList:
                med.append({'id':i.medicineId,'name':i.medicineName,'price':i.medicinePrice,'batch':i.batchNo,'quantity':i.stock})
            return jsonify(med)
        elif user_type == "doctor":
            chemistId = request.args.get('chemistId')
            medicineList = Medicine.query.filter_by(chemistId=chemistId).all()
            med = []
            for i in medicineList:
                med.append({'id':i.medicineId,'name':i.medicineName,'price':i.medicinePrice,'batch':i.batchNo,'quantity':i.stock})
            return jsonify(med)
        else:
            return jsonify()
    
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

    @app.route('/out-of-stock')
    @login_required
    def out_of_stock():
        if session['user_type'] != "chemist":
            return jsonify({"error": "Unauthorized"}), 403
        
        threshold = int(request.args.get('threshold', default=10))
        out_of_stock = Medicine.query.filter(Medicine.stock == 0, Medicine.chemistId == current_user.chemistId).all()
        low_stock = Medicine.query.filter(Medicine.stock > 0,Medicine.stock <= threshold, Medicine.chemistId == current_user.chemistId).all()
        def serialize_medicine(med_list):
            return [{
                'name': m.medicineName,
                'batch': m.batchNo,
                'quantity': m.stock,
                'expiryDate': m.expiryDate.isoformat()
            } for m in med_list]
        
        return jsonify({
            'out_of_stock': serialize_medicine(out_of_stock),
            'low_stock': serialize_medicine(low_stock)
        })

    @app.route('/generate-bill',methods=['POST'])
    @login_required
    def generateBill():
        
        chemist = Chemist.query.get(current_user.chemistId)
        if chemist.address is None or chemist.contactNumber is None:
            flash("Setup profile first","error")
            return redirect(url_for('chemist')+'#billing')
        else:
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
        
    @app.route('/stock-chart-data')
    @login_required
    def stockchart():
        medicine = Medicine.query.filter_by(chemistId=current_user.chemistId).order_by(Medicine.stock.desc()).all()
        data = {"labels":[i.medicineName for i in medicine],"datasets":[{"data":[i.stock for i in medicine]}]}
        return jsonify(data)
    
    @app.route('/sales-chart-data')
    @login_required
    def saleschart():
        total_sales_by_day = db.session.query(
            db.func.strftime('%Y-%m-%d', Sales.date).label('sales_date'),
            db.func.sum(Sales.totalPrice).label('daily_total')
        ).filter(
            Sales.chemistId == current_user.chemistId
        ).group_by(
            Sales.date
        ).order_by(
            Sales.date
        ).all()
        data = {"labels":[i.sales_date for i in total_sales_by_day],
                "datasets":[{"data":[i.daily_total for i in total_sales_by_day],"fill":False,"label":"Daily Sales","tension":0.1,"borderColor":"#4CAF50"}],
                }
        return jsonify(data)
    
    @app.route('/search-bar/<keyword>')
    @login_required
    def stockdata(keyword):
        sectionId = request.args.get('section')
        if sectionId == "stock-management":
            medicine = Medicine.query.filter_by(chemistId = current_user.chemistId).filter(Medicine.medicineName.ilike(f"%{keyword}%")).all()
            data = []
            for i in medicine:
                data.append({"medicineId":i.medicineId,
                            "medicineName":i.medicineName,
                            "stock":i.stock,
                            "medicinePrice":i.medicinePrice,
                            "companyName":i.companyName})
            return jsonify(data)
        elif sectionId == "order-medicine":
            chemist = Chemist.query.filter(Chemist.address.isnot(None),Chemist.shopname.ilike(f"%{keyword}%")).all()
            doctor = Doctor.query.get(current_user.doctorId)
            if chemist:
                destinationList = []
                destinationId = []
                for i in chemist:
                    destinationList.append(i.address)
                    destinationId.append({"chemistId":i.chemistId,"address":i.address,"shopname":i.shopname,"chemistName":i.chemistName,"contactNumber":i.contactNumber})
                locations = {"destinationList":destinationList,"originList":[doctor.address],"destinationId":destinationId}
                shopnames = get_distance_matrix(locations,MAPS_API_KEY)
                return jsonify(shopnames)
            return jsonify("No chemist found")
        else:
            return {}
    
    @app.route('/card-data')
    @login_required
    def cardData():
        order = Orders.query.filter_by(chemistId=current_user.chemistId).all()
        sales = Purchase.query.filter_by(chemistId = current_user.chemistId).all()
        pending = Orders.query.filter(Orders.chemistId == current_user.chemistId,Orders.status == "pending").all()
        delivered = Orders.query.filter(Orders.chemistId == current_user.chemistId,Orders.status == "delivered").all()
        orderLen = 0
        salesAmount = 0
        pendingLen = 0
        deliveredLen = 0
        orderBillAmount = 0
        totalSales = 0
        for i in order:
            orderLen += 1
            if i.status == "delivered":
                orderBillAmount += float(i.billAmount)
        for i in pending:
            pendingLen += 1
        for i in delivered:
            deliveredLen += 1
        for i in sales:
            salesAmount += float(i.billAmount)
        totalSales = salesAmount + orderBillAmount
        data = [{"totalOrder":orderLen,"totalSales":f"{totalSales:.2f}","pendingOrder":pendingLen,"deliveredOrder":deliveredLen}]
        return jsonify(data)

        
    
    @app.route('/delete/<medicineId>',methods=['POST'])
    @login_required
    def deleteMedicine(medicineId):
        medicine = Medicine.query.filter_by(chemistId=current_user.chemistId,medicineId=medicineId)
        db.session.delete(medicine)
        db.session.commit()
        return jsonify({"message":"Medicine deleted successfully"}),200
    
    @app.route('/update/<medicineId>',methods=['POST'])
    @login_required
    def updateMedicine(medicineId):
            medicine = Medicine.query.filter_by(chemistId=current_user.chemistId, medicineId=medicineId).first()

            batchNo = request.args.get('batchNo')
            expiryMonths = int(request.args.get('expiryMonths'))
            quantity = request.args.get('quantity')
            mfgDate = request.args.get('mfgDate')
            manufactureDate = datetime.strptime(mfgDate, "%Y-%m-%d").date()
            expiryDate = get_date(manufactureDate,expiryMonths)
            print(f"mfg date:{manufactureDate}, expiry date:{expiryDate},quan:{quantity}, batch:{batchNo}")

            if medicine:
                medicine.batchNo = str(batchNo)
                medicine.stock = int(quantity)
                medicine.manufactureDate = manufactureDate
                medicine.expiryDate = expiryDate
                db.session.commit()
                return jsonify({"message":"Medicine updated successfully"}),200
            else:
                return jsonify({"message":"Medicine not found"}),404
        
    @app.route('/distance-calculator')
    @login_required
    def distanceCalculator():
        chemist = Chemist.query.filter(Chemist.address.isnot(None)).all()
        doctor = Doctor.query.get(current_user.doctorId)
        destinationList = []
        destinationId = []
        for i in chemist:
            destinationList.append(i.address)
            destinationId.append({"chemistId":i.chemistId,"address":i.address,"shopname":i.shopname,"chemistName":i.chemistName,"contactNumber":i.contactNumber})
        originList = [doctor.address]

        locations = {"destinationList":destinationList,"originList":originList,"destinationId":destinationId}

        data = get_distance_matrix(locations,MAPS_API_KEY)
        return jsonify(data)
    
    @app.route('/get-orders')
    @login_required
    def get_orders():
        userType = request.args.get('userType')
        status = request.args.get('status')
        if userType == "doctor":
            if status == "all":
                orders = Orders.query.filter_by(doctorId=current_user.doctorId).all()
                data = []
                for i in orders:
                    chemist = Chemist.query.filter_by(chemistId=i.chemistId).first()
                    doctor = Doctor.query.filter_by(doctorId=current_user.doctorId).first()
                    data.append({"orderId":i.orderId,"orderDate":str(i.orderDate),"shopname":chemist.shopname,"doctorName":doctor.doctorName,"address":doctor.address,"billAmount":i.billAmount,"status":i.status})
                return jsonify(data)
            
            elif status == "pending" or status == "delivered" or status == "cancelled":
                orders = Orders.query.filter_by(doctorId=current_user.doctorId,status=status).all()
                data = []
                for i in orders:
                    chemist = Chemist.query.filter_by(chemistId=i.chemistId).first()
                    doctor = Doctor.query.filter_by(doctorId=current_user.doctorId).first()
                    data.append({"orderId":i.orderId,"orderDate":str(i.orderDate),"shopname":chemist.shopname,"address":doctor.address,"billAmount":i.billAmount,"status":i.status})
                return jsonify(data)
                
            else:
                return jsonify({"message":"Invalid status"}),404
        elif userType == "chemist":
            if status == "all":
                orders = Orders.query.filter_by(chemistId=current_user.chemistId).all()
                data = []
                for i in orders:
                    doctor = Doctor.query.filter_by(doctorId=i.doctorId).first()
                    data.append({"orderId":i.orderId,"orderDate":str(i.orderDate),"doctorName":doctor.doctorName,"address":doctor.address,"billAmount":i.billAmount,"status":i.status})
                return jsonify(data)
            
            elif status == "pending" or status == "delivered" or status == "cancelled":
                orders = Orders.query.filter_by(chemistId=current_user.chemistId,status=status).all()
                data = []
                for i in orders:
                    doctor = Doctor.query.filter_by(doctorId=i.doctorId).first()
                    data.append({"orderId":i.orderId,"orderDate":str(i.orderDate),"doctorName":doctor.doctorName,"address":doctor.address,"billAmount":i.billAmount,"status":i.status})
                return jsonify(data)
            else:
                return jsonify({"message":"Invalid status"}),404
        else:
            return jsonify({"message":"Invalid user type"}),404
        
    @app.route('/view-order/<int:orderId>')
    @login_required
    def view_orders(orderId):
        userType = request.args.get('userType')
        counter = int(request.args.get('counter'))
        if userType == "chemist":
            return render_template('view_order.html',orderId=orderId,counter=counter)
        elif userType == "doctor":
            return render_template('doctor_view_order.html',orderId=orderId,counter=counter)
        else:
            return jsonify({"message":"Invalid user type"}),404
    
    @app.route('/get-order-details/<int:orderId>')
    @login_required
    def get_order_details(orderId):
        meds = OrderMedicine.query.filter_by(orderId=orderId).all()
        order = Orders.query.filter_by(orderId=orderId).first()
        doctor = Doctor.query.filter_by(doctorId=order.doctorId).first()
        orderDetails = {"doctorName":doctor.doctorName,"address":doctor.address,"billAmount":order.billAmount,"status":order.status,"orderDate":str(order.orderDate)}
        medData = []
        for i in meds:
            medicines = Medicine.query.filter_by(medicineId=i.medicineId).first()
            if medicines.stock >= i.quantity:
                stockStatus = "Available"
            else:
                stockStatus = "Out of Stock"
            medData.append({"medicineId":i.medicineId,"medicineName":i.medicineName,"quantity":i.quantity,"mrp":i.pricePerUnit,"totalPrice":i.totalPrice,"stockStatus":stockStatus})
        data = {"orderDetails":orderDetails,"medicineDetails":medData}
        return jsonify(data)
    
    @app.route('/order/<int:orderId>')
    @login_required
    def order(orderId):
        status = request.args.get('status')
        if status == "accept":
            order = Orders.query.filter_by(orderId=orderId).first()
            chemist = Chemist.query.filter_by(chemistId=order.chemistId).first()
            doctor = Doctor.query.filter_by(doctorId=order.doctorId).first()
            medicineList = OrderMedicine.query.filter_by(orderId=orderId).all()

            for medicine in medicineList:
                medicine.pricePerUnit = float(medicine.pricePerUnit)
                medicine.totalPrice = float(medicine.totalPrice)

            renderedHtml = render_template('doctor_bill_template.html',
                                            img_string = BASE_64_STRING,
                                            orderId = orderId,
                                            orderDate = str(order.orderDate),
                                            chemist = chemist,
                                            doctor = doctor,
                                            billAmount = float(order.billAmount),
                                            medicineList = medicineList)
            try:
                # IMPORTANT: You must provide the correct path to the wkhtmltopdf executable.
                # 1. Find where 'wkhtmltopdf.exe' is located on your system.
                # 2. Replace the path below with your actual path.
                # 3. Use a raw string (r'...') to avoid issues with backslashes.
                path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
                config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                
                # Generate the PDF using the configuration
                pdf = pdfkit.from_string(renderedHtml, False, configuration=config)

                if doctor and doctor.doctorEmail:
                    send_email_with_pdf(pdf, doctor.doctorEmail, orderId)

                flash('Bill generated and sent to doctor successfully!', 'success')
                if order:
                    order.status = "delivered"
                    db.session.commit()

                return redirect(url_for('chemist')+'#doctor-order')

            except IOError as e:
                # This will catch the "No wkhtmltopdf executable found" error
                print(f"Error generating PDF: {e}. Please ensure wkhtmltopdf is installed and the path in routes.py is correct.", 'error')
                flash('Error generating PDF.', 'error')
        elif status == "decline":
            # order = Orders.query.filter_by(orderId=orderId).first()
            # if order:
            #     order.status = "cancelled"
            #     db.session.commit()
            flash('Order declined!','success')
            return redirect(url_for('chemist')+'#doctor-order')
        elif status == "view-bill":
            order = Orders.query.filter_by(orderId=orderId).first()
            chemist = Chemist.query.filter_by(chemistId=order.chemistId).first()
            doctor = Doctor.query.filter_by(doctorId=order.doctorId).first()
            medicineList = OrderMedicine.query.filter_by(orderId=orderId).all()

            for medicine in medicineList:
                medicine.pricePerUnit = float(medicine.pricePerUnit)
                medicine.totalPrice = float(medicine.totalPrice)

            return render_template('doctor_bill_template.html',
                                            img_string = BASE_64_STRING,
                                            orderId = orderId,
                                            orderDate = str(order.orderDate),
                                            chemist = chemist,
                                            doctor = doctor,
                                            billAmount = float(order.billAmount),
                                            medicineList = medicineList)
    
    @app.route('/chart-data')
    @login_required
    def chartData():
        graph = request.args.get('graph')
        if graph == "sales":
            try:
                # Query for sales data.
                total_sales_by_day = db.session.query(
                    func.strftime('%Y-%m-%d', Sales.date).label('sales_date'),
                    func.sum(Sales.totalPrice).label('daily_total')
                ).filter(
                    Sales.chemistId == current_user.chemistId
                ).group_by(
                    Sales.date
                ).order_by(
                    Sales.date
                ).all()
                
                # Query for orders data. The billAmount is cast to Integer for summing.
                total_orders_by_day = db.session.query(
                    func.strftime('%Y-%m-%d', Orders.orderDate).label('order_date'),
                    func.sum(Orders.billAmount.cast(Integer)).label('daily_total')
                ).filter(
                    Orders.chemistId == current_user.chemistId
                ).group_by(
                    Orders.orderDate
                ).order_by(
                    Orders.orderDate
                ).all()
                
                # Combine dates from both sales and orders queries to get a comprehensive list
                sales_dates = {row.sales_date for row in total_sales_by_day}
                orders_dates = {row.order_date for row in total_orders_by_day}
                all_dates = sorted(list(sales_dates.union(orders_dates)))
                
                # Create dictionaries for quick lookup of daily totals
                sales_data_map = {row.sales_date: row.daily_total for row in total_sales_by_day}
                orders_data_map = {row.order_date: row.daily_total for row in total_orders_by_day}
                
                # Build a single list of daily totals by summing sales and orders for each date
                combined_totals = []
                for date in all_dates:
                    sales_total = sales_data_map.get(date, 0)
                    orders_total = orders_data_map.get(date, 0)
                    combined_totals.append(sales_total + orders_total)
                
                # Create the final data structure for a single Chart.js dataset
                chart_data = {
                    "labels": all_dates,
                    "datasets": [
                        {
                            "data": combined_totals,
                            "fill": True,
                            "label": "Daily Total Bill Amount",
                            "tension": 0.1,
                            "borderColor": "#42007f",                        
                            "backgroundColor": "rgba(66, 0, 127, 0.2)" # Light purple fill
                        }
                    ]
                }
                
                return jsonify(chart_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        elif graph == "date-range":
            start_date = request.args.get('start')
            end_date = request.args.get('end')
            try:
                # Query for total sales within the date range
                total_sales = db.session.query(
                    func.sum(Sales.totalPrice)
                ).filter(
                    Sales.chemistId == current_user.chemistId,
                    Sales.date.between(start_date, end_date)
                ).scalar() or 0

                # Query for total orders within the date range
                total_orders = db.session.query(
                    func.sum(Orders.billAmount.cast(Integer))
                ).filter(
                    Orders.chemistId == current_user.chemistId,
                    Orders.orderDate.between(start_date, end_date)
                ).scalar() or 0

                # Create the final data structure
                report_data = {
                    "total_sales_amount": total_sales,
                    "total_orders_amount": total_orders,
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    }
                }

                return jsonify(report_data)

            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
    @app.route('/fetch-doctor',methods=['GET','POST'])
    @login_required
    def fetchDoctor():
        if request.method == "GET":
            doctorName = request.args.get('doctorName')
            if doctorName:
                doctor = Doctor.query.filter(Doctor.address.isnot(None),Doctor.doctorName.ilike(f"%{doctorName}%")).all()
                doctorList = []
                for i in doctor:
                    doctorList.append({'doctorId':i.doctorId,'specialization':i.specialization,'doctorName':i.doctorName,'address':i.address,'doctorEmail':i.doctorEmail,'hospitalName':i.hospitalname})
                return jsonify(doctorList)
            else:
                doctor = Doctor.query.filter(Doctor.address.isnot(None)).all()
                doctorList = []
                for i in doctor:
                    doctorList.append({'doctorId':i.doctorId,'specialization':i.specialization,'doctorName':i.doctorName,'address':i.address,'doctorEmail':i.doctorEmail,'hospitalName':i.hospitalname})
                return jsonify(doctorList)
              
        elif request.method == "POST":
            doctorId = request.args.get('doctorId')
            appointmentType = request.args.get('appointmentType')
            doctor = Doctor.query.filter_by(doctorId=doctorId).first()
            if doctor:
                appointments = Appointments(
                    doctorId = doctor.doctorId,
                    patientType = appointmentType,
                    status = "pending",
                    patientId = current_user.patientId
                )
                db.session.add(appointments)
                db.session.commit()
                return redirect('/patient')
            else:
                flash('Doctor not found','error')
                return redirect('/patient')
        else:
            return flash('Invalid request method','error')
        
    @app.route('/fetch-appointments')
    @login_required
    def fetchAppointments():
        status = request.args.get('status')
        if status == "all":
            appointments = Appointments.query.filter_by(doctorId=current_user.doctorId).all()
            appointmentList = []
            for i in appointments:
                patient = Patient.query.filter_by(patientId=i.patientId).first()
                appointmentList.append({'appointmentId':i.appointmentId,'patientName':patient.patientName,'appointmentType':i.patientType,'status':i.status})
            return jsonify(appointmentList)
        elif status == "pending" or status == "scheduled":
            appointments = Appointments.query.filter_by(doctorId=current_user.doctorId,status=status).all()
            appointmentList = []
            for i in appointments:
                patient = Patient.query.filter_by(patientId=i.patientId).first()
                appointmentList.append({'appointmentId':i.appointmentId,'patientName':patient.patientName,'appointmentType':i.patientType,'status':i.status})
            return jsonify(appointmentList)
        
    @app.route('/view-appointment/<int:appointmentId>')
    @login_required
    def viewAppointment(appointmentId):
        return render_template('view_appointment.html',appointmentId=appointmentId)

    @app.route('/update-database')
    def update_database():
        # order = Orders.query.filter_by(orderId = 1).first()
        # if order:
        #     order.status = "delivered"
        #     db.session.commit()
        return "DOne"

