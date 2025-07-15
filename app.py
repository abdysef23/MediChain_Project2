import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from supabase import create_client, Client
import uuid
from dotenv import load_dotenv # Used to load environment variables
from datetime import datetime
import traceback

# Load environment variables from a .env file
load_dotenv()

# --- Initialize Flask App ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

 # Set host to '0.0.0.0' to make it accessible on your network
@app.template_filter('format_datetime')
def format_datetime_filter(s):
    """
    Formats a UTC timestamp string from the database into a more
    readable format, e.g., 'THURSDAY, 18 JULY 2024, 10:30 AM'.
    """
    if s is None:
        return "No date provided"
    # Parse the ISO 8601 format string from Supabase
    dt_object = datetime.fromisoformat(s.replace('Z', '+00:00'))
    # Format it into the desired string
    return dt_object.strftime('%A, %d %B %Y, %I:%M %p').upper()

# --- Initialize Supabase ---
# Get credentials from environment variables for better security
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

# Check if credentials are set
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set in the .env file")

try:
    # ** THE FIX IS HERE: The original URL was incorrect **
    # The create_client now correctly points to your .com address
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Successfully connected to Supabase.")
except Exception as e:
    # This will catch connection errors on startup
    print(f"Error connecting to Supabase: {e}")
    # Exit if we can't connect to the database
    exit()


# --- Routes ---

@app.route('/')
def index():
    """Renders the new landing page or redirects to dashboard if logged in."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/auth')
def auth():
    """Renders the new login/signup page."""
    # If the user is already logged in, just send them to the dashboard.
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')


# REPLACE THE ENTIRE signup FUNCTION WITH THIS CORRECTED BLOCK

@app.route('/signup', methods=['POST'])
def signup():
    """
    Handles user registration by passing all data to Supabase Auth.
    A database trigger will automatically create the user profile.
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')
        name = data.get('name')

        if not all([email, password, user_type, name]):
            return jsonify({"message": "Missing required fields"}), 400

        # This is the correct way to sign up. It passes the name and user_type
        # as metadata, which our database trigger will use.
        # It does NOT try to insert into the 'users' table manually.
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    'name': name,
                    'user_type': user_type
                }
            }
        })

        # If the signup is successful, we just return a success message.
        return jsonify({"message": "User created successfully. Please log in."}), 201

    except Exception as e:
        # This catches errors from Supabase (like "User already registered")
        # and returns them as a clear message instead of crashing the server.
        # You can see this message in your browser's developer console.
        error_message = str(e)
        print(f"SIGNUP ERROR: {error_message}") # Print the real error to your Flask console
        return jsonify({"message": error_message}), 400

# END OF REPLACEMENT BLOCK


@app.route('/login', methods=['POST'])
def login():
    """Handles user login and redirects them intelligently."""
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session['user_id'] = res.user.id
        
        # Check if there's a URL to redirect back to, otherwise default to the dashboard
        next_url = session.pop('next_url', None)
        redirect_url = next_url or url_for('dashboard')
        
        # Send the redirect URL back to the frontend JavaScript
        return jsonify({"message": "Login successful", "redirect_url": redirect_url}), 200
        
    except Exception as e:
        return jsonify({"message": "Invalid credentials"}), 401


@app.route('/logout')
def logout():
    """Clears the user session and redirects to the login page."""
    session.clear() # Removes all data from the session
    return redirect(url_for('index'))

# THIS IS THE FINAL AND CORRECT RECORD_DETAIL FUNCTION

@app.route('/record/<string:record_id>')
def record_detail(record_id):
    """Displays details for a single record, including prescribed drugs."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    user = supabase.table('users').select('*').eq('id', user_id).single().execute().data
    if not user:
        return redirect(url_for('auth'))

    # Fetch the main record details
    record_response = supabase.table('files').select('*').eq('id', record_id).single().execute()
    record = record_response.data
    if not record:
        return "Record not found", 404

    # Fetch the prescribed drugs linked to this record
    prescriptions_response = supabase.table('record_prescriptions').select('*, drug:drugs(*)').eq('record_id', record_id).execute()
    prescribed_drugs = [p['drug'] for p in prescriptions_response.data]

    # Determine the file type for the icon
    file_type = 'image' if record.get('file_name', '').lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'pdf'

    return render_template('record_detail.html', record=record, file_type=file_type, prescribed_drugs=prescribed_drugs, user=user)
@app.route('/dashboard')
def dashboard():
    """
    DEBUGGING VERSION: This function will print database results to the console
    to help diagnose why appointments are not appearing.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    user_response = supabase.table('users').select('*').eq('id', user_id).single().execute()
    user = user_response.data

    if not user:
        session.clear()
        return redirect(url_for('auth'))

    if user['user_type'] == 'doctor':
        print("--- DOCTOR DASHBOARD DEBUG ---")
        print(f"Attempting to fetch appointments for doctor_id: {user_id}")

        try:
            # TEMPORARY: Fetch ALL appointments, with NO filters, to see what's in the table.
            all_appointments_response = supabase.table('appointments').select('*').execute()
            
            print("\nRAW RESPONSE FROM SUPABASE:")
            print(all_appointments_response)
            
            # Now, we will try the original, filtered query and print its result.
            filtered_appointments_response = supabase.table('appointments') \
                .select('*, patient:patient_id(*)') \
                .eq('doctor_id', user_id) \
                .eq('status', 'upcoming') \
                .execute()

            print("\nFILTERED RESPONSE (what the page should show):")
            print(filtered_appointments_response)
            print("\n--- END DEBUG ---")

            # We will use the filtered data for the page
            appointments = filtered_appointments_response.data
            return render_template('doctor_dashboard.html', doctor=user, appointments=appointments)

        except Exception as e:
            print(f"AN ERROR OCCURRED: {e}")
            return f"A server error occurred during debugging: {e}", 500

    else:
        return render_template('dashboard.html', user=user)


@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
def complete_appointment(appointment_id):
    """Marks an appointment as 'completed' in the database."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    # Security check: Ensure the logged-in user is a doctor
    user_id = session['user_id']
    user_info = supabase.table('users').select('user_type').eq('id', user_id).single().execute().data
    if not user_info or user_info.get('user_type') != 'doctor':
        return "Permission Denied.", 403

    # Update the status of the appointment
    supabase.table('appointments').update({'status': 'completed'}).eq('id', appointment_id).execute()
    
    # Redirect back to the doctor's dashboard
    return redirect(url_for('dashboard'))


@app.route('/records')
def records():
    """Shows the detailed list of a patient's records."""
    if 'user_id' not in session: return redirect(url_for('index'))
    user_id = session['user_id']
    user = supabase.table('users').select('name').eq('id', user_id).single().execute().data
    records = supabase.table('files').select('*').eq('user_id', user_id).order('uploaded_at', desc=True).execute().data
    return render_template('records.html', user=user, records=records)

# END OF REPLACEMENT BLOCK


@app.route('/qr_code')
def qr_code():
    """Renders the QR code page for the patient."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    user_data = supabase.table('users').select('qr_id').eq('id', user_id).single().execute().data
    qr_id = user_data.get('qr_id')

    # Construct the URL for the doctor to scan
    doctor_view_url = request.host_url + url_for('doctor_view', qr_id=qr_id)
    return render_template('qr_code.html', qr_code_url=doctor_view_url)


@app.route('/doctor/view/<qr_id>')
def doctor_view(qr_id):
    """
    SECURED: Shows records to a doctor, redirecting to login if necessary.
    This version correctly handles the Supabase response object.
    """
    # Security Check Part 1: Is anyone even logged in?
    if 'user_id' not in session:
        session['next_url'] = request.url
        return redirect(url_for('index'))

    # Security Check Part 2: Is the logged-in user a doctor?
    doctor_id = session['user_id']
    doctor_response = supabase.table('users').select('user_type').eq('id', doctor_id).single().execute()
    doctor_info = doctor_response.data # Get data safely
    
    if not doctor_info or doctor_info.get('user_type') != 'doctor':
        return "Permission Denied: You must be a logged-in doctor to view this page.", 403

    # If security checks pass, proceed as before
    try:
        # Get the response object first
        patient_response = supabase.table('users').select('id, name').eq('qr_id', qr_id).single().execute()
        # Then get the data from it
        patient = patient_response.data 

        # Now, correctly check if the patient data exists
        if not patient:
            return "Invalid or expired QR Code", 404
        
        patient_id = patient.get('id')

        # Get the records response object first
        records_response = supabase.table('files').select('*').eq('user_id', patient_id).order('uploaded_at', desc=True).execute()
        # Then get the data from it
        records = records_response.data

        return render_template('records.html', user=patient, records=records, doctor_view=True, patient_id=patient_id)
        
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/upload_page/<patient_id>')
def upload_page(patient_id):
    """Renders the upload page and provides a list of all drugs."""
    patient_response = supabase.table('users').select('id, name, qr_id').eq('id', patient_id).single().execute()
    patient = patient_response.data
    
    # Fetch all drugs to populate the dropdown
    drugs_response = supabase.table('drugs').select('id, trade_name').order('trade_name').execute()
    all_drugs = drugs_response.data
    
    return render_template('upload_records.html', patient=patient, all_drugs=all_drugs)

# END OF THE NEW FUNCTION BLOCK
# REPLACE THE ENTIRE upload_record FUNCTION WITH THIS CORRECTED BLOCK

# THIS IS THE FINAL AND CORRECT UPLOAD_RECORD FUNCTION

@app.route('/upload_record', methods=['POST'])
def upload_record():
    """Handles file upload and linking prescribed drugs."""
    try:
        file = request.files.get('file')
        patient_id = request.form.get('patient_id')
        record_name = request.form.get('record_name')
        classification = request.form.get('classification')
        hints = request.form.get('hints')
        prescribed_drug_ids = request.form.getlist('prescribed_drugs')

        if not all([patient_id, record_name, classification, file]):
            return jsonify({"message": "Missing required fields"}), 400

        # --- File Upload Logic ---
        file_path = f"{patient_id}/{uuid.uuid4()}-{file.filename}"
        supabase.storage.from_('medical-records').upload(
            file=file.read(),
            path=file_path,
            file_options={"content-type": file.content_type}
        )
        file_url = supabase.storage.from_('medical-records').get_public_url(file_path)

        # --- Database Insertion Logic ---
        new_record_response = supabase.table('files').insert({
            "user_id": patient_id, "file_name": record_name, "file_url": file_url,
            "classification": classification, "hints": hints
        }).execute()
        new_record_id = new_record_response.data[0]['id']

        if new_record_id and prescribed_drug_ids:
            prescriptions_to_insert = [
                {'record_id': new_record_id, 'drug_id': drug_id}
                for drug_id in prescribed_drug_ids
            ]
            supabase.table('record_prescriptions').insert(prescriptions_to_insert).execute()
        
        # --- Redirect Logic ---
        patient_qr_response = supabase.table('users').select('qr_id').eq('id', patient_id).single().execute()
        patient_qr_id = patient_qr_response.data.get('qr_id')

        return redirect(url_for('doctor_view', qr_id=patient_qr_id))

    except Exception as e:
        print(f"AN ERROR OCCURRED during upload: {e}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

def auth():
    return render_template('auth.html')

# ADD THIS NEW ROUTE TO APP.PY

# REPLACE THE EXISTING profile FUNCTION WITH THIS NEW VERSION

# REPLACE THE ENTIRE profile FUNCTION WITH THIS CORRECTED BLOCK

# REPLACE THE ENTIRE profile FUNCTION WITH THIS CORRECTED BLOCK

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """
    Handles viewing and updating user profile information.
    This version has simplified and corrected logic for saving data.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']

    # Define the list of available medical specialties
    specialties = [
        "Cardiology", "Dermatology", "Neurology", "Pediatrics",
        "Orthopedics", "Radiology", "Gastroenterology", "Oncology",
        "Psychiatry", "General Practice"
    ]

    # --- THIS IS THE CORRECTED LOGIC FOR SAVING DATA ---
    if request.method == 'POST':
        # Prepare the data dictionary with the gender, which is always present
        update_data = {
            'gender': request.form.get('gender')
        }

        # The 'specialty' field is only sent by the form if the user is a doctor.
        # We can check if the form sent this field.
        if 'specialty' in request.form:
            update_data['specialty'] = request.form.get('specialty')

        # Execute the update query in the database
        supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        # Redirect to the dashboard after saving
        return redirect(url_for('dashboard'))
    # --- END OF CORRECTED LOGIC ---

    # If just viewing the page (GET request), the logic remains the same
    user_response = supabase.table('users').select('*').eq('id', user_id).single().execute()
    user = user_response.data
    
    return render_template('profile.html', user=user, specialties=specialties)

# END OF REPLACEMENT BLOCK



# ADD THESE TWO NEW ROUTES TO APP.PY

# REPLACE THE EXISTING drug_guide FUNCTION
@app.route('/drug_guide')
def drug_guide():
    """Renders the main Drug Guide page and handles search."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    user = supabase.table('users').select('*').eq('id', user_id).single().execute().data
    
    query = request.args.get('q', '')
    if query:
        drugs_response = supabase.table('drugs').select('*').or_(f'trade_name.ilike.%{query}%,scientific_name.ilike.%{query}%').execute()
    else:
        drugs_response = supabase.table('drugs').select('*').order('trade_name').execute()
        
    drugs = drugs_response.data
    return render_template('drug_guide.html', drugs=drugs, search_query=query, user=user)


# REPLACE THE EXISTING drug_detail FUNCTION
@app.route('/drug/<int:drug_id>')
def drug_detail(drug_id):
    """Renders the detailed page for a single drug."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    user = supabase.table('users').select('*').eq('id', user_id).single().execute().data

    drug_response = supabase.table('drugs').select('*').eq('id', drug_id).single().execute()
    drug = drug_response.data
    if not drug:
        return "Drug not found", 404

    alternatives_response = supabase.table('drugs').select('*').eq('scientific_name', drug['scientific_name']).neq('id', drug['id']).execute()
    alternatives = alternatives_response.data

    return render_template('drug_detail.html', drug=drug, alternatives=alternatives, user=user)




@app.route('/my_appointments')
def my_appointments():
    """Shows the patient their own upcoming and past appointments."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    user_id = session['user_id']
    
    # Fetch all appointments for the logged-in patient, joining with doctor info
    # The syntax 'doctor:doctor_id(*)' tells Supabase to fetch all columns from the linked doctor
    appointments_response = supabase.table('appointments').select('*, doctor:doctor_id(*)').eq('patient_id', user_id).order('appointment_time', desc=True).execute()
    all_appointments = appointments_response.data
    
    # Separate appointments into upcoming and past
    upcoming_appointments = [appt for appt in all_appointments if appt['status'] == 'upcoming']
    past_appointments = [appt for appt in all_appointments if appt['status'] != 'upcoming']
    
    return render_template('my_appointments.html', upcoming=upcoming_appointments, past=past_appointments)


@app.route('/find_a_doctor')
def find_a_doctor():
    """Shows a list of doctors, sorted by popularity, with filtering."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))
        
    try:
        # Call the database function to get the sorted list of doctors
        doctors_response = supabase.rpc('get_doctors_sorted_by_appointments').execute()
        doctors = doctors_response.data
        
        # THIS IS THE CORRECTED LOGIC FOR GETTING SPECIALTIES
        # It handles cases where a specialty might be None or an empty string
        all_specialties = [doc['specialty'] for doc in doctors if doc.get('specialty')]
        # Get a unique, sorted list of the specialties
        unique_specialties = sorted(list(set(all_specialties)))

        return render_template('find_a_doctor.html', doctors=doctors, specialties=unique_specialties)
        
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return "Could not load doctor list.", 500

@app.route('/book_appointment/<doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    """
    Handles the appointment booking process for a specific doctor.
    This version has the corrected route definition.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    patient_id = session['user_id']

    if request.method == 'POST':
        appt_time_str = request.form.get('appointment_time')
        if appt_time_str:
            supabase.table('appointments').insert({
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'appointment_time': appt_time_str,
                'status': 'upcoming'
            }).execute()
        return redirect(url_for('my_appointments'))

    doctor_response = supabase.table('users').select('*').eq('id', doctor_id).single().execute()
    doctor = doctor_response.data

    if not doctor or doctor.get('user_type') != 'doctor':
        return "Doctor not found.", 404
        
    return render_template('book_appointment.html', doctor=doctor)

# END OF REPLACEMENT BLOCK


if __name__ == '__main__':
    # Set host to '0.0.0.0' to make it accessible on your network
    
    app.run(debug=True, host='0.0.0.0')
# ADD THIS BLOCK RIGHT AFTER app = Flask(__name__)

def format_datetime_filter(value):
    """Jinja2 filter to format a datetime string for display."""
    if not value:
        return ""
    # Parse the ISO format string from Supabase
    dt_object = datetime.fromisoformat(value.replace('Z', '+00:00'))
    # Format it into a more readable string
    return dt_object.strftime('%A, %d %B %Y, %I:%M %p')

# Register the function as a filter with Jinja2
app.jinja_env.filters['format_datetime'] = format_datetime_filter

# END OF NEW BLOCK