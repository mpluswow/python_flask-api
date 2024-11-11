import os
import configparser
from flask import Flask, render_template, flash, redirect, url_for, request, session, send_from_directory
from modules.db_models import db, Account
from modules.api import api_bp, jwt  # Import jwt from api module
from install.install_module import run_installation
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def load_host_config():
    """Load host and port configuration from conf/host.conf."""
    config = configparser.ConfigParser()
    config.read('conf/host.conf')

    host = config.get('server', 'host', fallback='0.0.0.0')  # Changed default to '0.0.0.0'
    port = config.getint('server', 'port', fallback=5000)

    return host, port

def create_app():
    """Application factory pattern for creating the Flask app."""
    app = Flask(
        __name__,
        template_folder='data/html',  # Set templates directory
        static_folder='data'          # Set static files directory
    )
    app.secret_key = 'your_secret_key'  # Replace with a secure key

    # Configure MySQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://apiUser:apiPassword@localhost/api_auth'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT configuration
    app.config['JWT_SECRET_KEY'] = 'another_secret_key'  # Replace with a secure key

    # Initialize the database and JWT
    db.init_app(app)
    jwt.init_app(app)  # Initialize JWTManager with the app

    # Register API blueprint
    app.register_blueprint(api_bp)

    # Web routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = Account.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                user.online = True
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')

        return render_template('auth/login.html')

    @app.route('/logout')
    def logout():
        user_id = session.get('user_id')
        if user_id:
            # Use db.session.get() instead of Account.query.get()
            user = db.session.get(Account, user_id)
            if user:
                user.online = False
                db.session.commit()

        session.clear()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            flash('You must be logged in to access the dashboard.', 'danger')
            return redirect(url_for('login'))

        return render_template('dashboard.html', username=session['username'])

    @app.route('/create-account', methods=['GET', 'POST'])
    def create_account():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if username or email already exists
            if Account.query.filter((Account.username == username) | (Account.email == email)).first():
                flash('Username or email already exists!', 'danger')
                return redirect(url_for('create_account'))

            # Create a new account
            hashed_password = generate_password_hash(password)
            new_account = Account(username=username, email=email, password=hashed_password)
            db.session.add(new_account)
            db.session.commit()

            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))

        return render_template('auth/create_account.html')

    # New download route
    @app.route('/download/<filename>')
    def download_file(filename):
        """Serve files from the downloads folder."""
        download_folder = os.path.join(os.getcwd(), 'data', 'downloads')
        try:
            return send_from_directory(download_folder, filename, as_attachment=True)
        except FileNotFoundError:
            flash('File not found.', 'danger')
            return redirect(url_for('index'))

    return app

if __name__ == '__main__':
    # Run the installation routine to ensure database and tables exist
    run_installation()

    # Load host and port from configuration
    host, port = load_host_config()

    # Create and run the Flask app
    app = create_app()
    app.run(host=host, port=port, debug=True)

