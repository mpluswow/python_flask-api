import os
import json
from flask import Blueprint, request, flash, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from flask import current_app as app
from functools import wraps
from flask import session

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'zip', 'apk', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'csv', 'mp4', 'mp3'}

# Blueprint for file management
file_bp = Blueprint('file_management', __name__, template_folder='../data/html')

def login_required(f):
    """Decorator to require login for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_bp.route('/uploads', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Upload a file with a description."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        description = request.form.get('description', '')

        if not file:
            flash('No file selected.', 'danger')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Invalid file type.', 'danger')
            return redirect(request.url)

        if not description.strip():
            flash('Description is required.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))

        # Load or initialize the descriptions
        descriptions_file = os.path.join(upload_folder, 'descriptions.json')
        descriptions = {}
        if os.path.exists(descriptions_file):
            try:
                with open(descriptions_file, 'r') as f:
                    descriptions = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # If the file is empty or invalid, reset it to an empty dictionary
                descriptions = {}

        descriptions[filename] = description
        with open(descriptions_file, 'w') as f:
            json.dump(descriptions, f)

        flash('File uploaded successfully!', 'success')
        return redirect(url_for('file_management.upload_file'))

    return render_template('uploads/upload_file.html')

@file_bp.route('/downloads')
@login_required
def list_downloads():
    """List all available files for download with descriptions."""
    download_folder = os.path.join(os.getcwd(), 'data', 'downloads', 'files')
    descriptions_file = os.path.join(os.getcwd(), 'data', 'downloads', 'descriptions.json')

    if not os.path.exists(descriptions_file):
        flash('Descriptions file not found.', 'danger')
        return redirect(url_for('index'))

    try:
        with open(descriptions_file, 'r') as f:
            descriptions = json.load(f)
    except json.JSONDecodeError:
        flash('Error reading descriptions file.', 'danger')
        return redirect(url_for('index'))

    available_files = []
    for filename in os.listdir(download_folder):
        if os.path.isfile(os.path.join(download_folder, filename)):
            available_files.append({
                'filename': filename,
                'description': descriptions.get(filename, 'No description available.')
            })

    return render_template('downloads/list_downloads.html', files=available_files)

@file_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """Serve files from the downloads folder."""
    download_folder = os.path.join(os.getcwd(), 'data', 'downloads', 'files')
    try:
        return send_from_directory(download_folder, filename, as_attachment=True)
    except FileNotFoundError:
        flash('File not found.', 'danger')
        return redirect(url_for('file_management.list_downloads'))

