import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from supabase import create_client, Client
import uuid
from dotenv import load_dotenv # Used to load environment variables

# Load environment variables from a .env file
load_dotenv()

# --- Initialize Flask App ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

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
    """Renders the login/signup page."""
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    """Handles user registration."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')
    name = data.get('name')

    if not all([email, password, user_type, name]):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Create user in Supabase Auth
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        # Get the user ID from the successful auth response
        user_id = res.user.id

        # Insert additional user info into the 'users' table
        qr_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": email,
            "name": name,
            "user_type": user_type,
            "qr_id": qr_id
        }
        supabase.table('users').insert(user_data).execute()

        return jsonify({"message": "User created successfully"}), 201

    except Exception as e:
        # Provide a more specific error message
        return jsonify({"message": f"Error during sign-up: {e}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session['user_id'] = res.user.id
        return jsonify({"message": "Login successful"}), 200
    except Exception as e:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    """Clears the user session and redirects to the login page."""
    session.clear() # Removes all data from the session
    return redirect(url_for('index'))

@app.route('/record/<record_id>')
def record_detail(record_id):
    """Displays the details for a single medical record."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    
    try:
        # Fetch the specific record from the database
        record_response = supabase.table('files').select('*').eq('id', record_id).single().execute()
        record = record_response.data

        # Security Check: Make sure the record belongs to the logged-in user
        if not record or record['user_id'] != user_id:
            return "Error: Record not found or you do not have permission to view it.", 404
            
        # Determine the file type for the icon
        file_type = 'image' if record['file_name'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'pdf'

        return render_template('record_detail.html', record=record, file_type=file_type)

    except Exception as e:
        return f"An error occurred: {str(e)}", 500
# REPLACE THE OLD DASHBOARD FUNCTION WITH THIS ENTIRE BLOCK

@app.route('/dashboard')
def dashboard():
    """Renders the patient's main dashboard."""
    if 'user_id' not in session: return redirect(url_for('index'))
    user_id = session['user_id']
    user = supabase.table('users').select('*').eq('id', user_id).single().execute().data
    return render_template('dashboard.html', user=user)

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
    Shows records to a doctor using the main 'records.html' template for consistent styling.
    """
    try:
        # Find the patient associated with the scanned QR ID
        user_response = supabase.table('users').select('id, name').eq('qr_id', qr_id).single().execute()
        
        if not user_response.data:
            return "Invalid or expired QR Code", 404
        
        patient = user_response.data
        patient_id = patient.get('id')

        # Fetch all medical records for that patient
        records = supabase.table('files').select('*').eq('user_id', patient_id).order('uploaded_at', desc=True).execute().data

        # Render the 'records.html' template with a special flag for the doctor's view
        return render_template(
            'records.html', 
            user=patient, 
            records=records, 
            doctor_view=True,  # This flag tells the template to show the doctor's version
            patient_id=patient_id # Pass the ID for the "Upload" button link
        )

    except Exception as e:
        return f"An error occurred: {str(e)}", 500
# ADD THIS ENTIRE FUNCTION TO APP.PY

@app.route('/upload_page/<patient_id>')
def upload_page(patient_id):
    """Renders the dedicated drag-and-drop upload page for doctors."""
    # We fetch the patient's info just to display their name on the upload page
    patient = supabase.table('users').select('id, name').eq('id', patient_id).single().execute().data
    return render_template('upload_records.html', patient=patient)

# END OF THE NEW FUNCTION BLOCK
@app.route('/upload_record', methods=['POST'])
def upload_record():
    # Step 1: First, check if the 'file' key even exists in the request.
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the form submission"}), 400

    # Step 2: Now that we know it exists, we can safely create the 'file' variable.
    file = request.files['file']

    # Step 3: Check if the user submitted the form without choosing a file (filename is empty).
    if file.filename == '':
        return jsonify({"message": "No file selected for upload"}), 400

    # Now we can safely proceed with the rest of the logic
    patient_id = request.form.get('patient_id')
    record_name = request.form.get('record_name')
    classification = request.form.get('classification')
    hints = request.form.get('hints')

    if not all([patient_id, record_name, classification]):
        return jsonify({"message": "Missing required form fields like patient ID or record name"}), 400

    try:
        file_path = f"{patient_id}/{uuid.uuid4()}-{file.filename}"
        
        supabase.storage.from_('medical-records').upload(
            file=file.read(),
            path=file_path,
            file_options={"content-type": file.content_type}
        )
        
        file_url = supabase.storage.from_('medical-records').get_public_url(file_path)

        # The typo was here. It is now corrected to 'record_name'.
        supabase.table('files').insert({
            "user_id": patient_id,
            "file_name": record_name,  # <<< THIS WAS THE FIX
            "file_url": file_url, 
            "classification": classification,
            "hints": hints
        }).execute()
        
        patient_qr_response = supabase.table('users').select('qr_id').eq('id', patient_id).single().execute()
        patient_qr_id = patient_qr_response.data.get('qr_id')
        
        return redirect(url_for('doctor_view', qr_id=patient_qr_id))

    except Exception as e:
        return jsonify({"message": f"An error occurred during upload: {str(e)}"}), 500





@app.route('/profile')
def profile():
    """Renders the user's profile page."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    user_data = supabase.table('users').select('*').eq('id', user_id).single().execute().data
    return render_template('profile.html', user=user_data)

if __name__ == '__main__':
    # Set host to '0.0.0.0' to make it accessible on your network
    app.run(debug=True, host='0.0.0.0')