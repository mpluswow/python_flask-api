import os
import configparser
from flask import Flask, render_template, flash, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from modules.db_models import db, Account
from modules.api import api_bp, jwt
from modules.file_management import file_bp  # Import the file management blueprint
from install.install_module import run_installation
from modules.game import game_bp  # Import the game blueprint
from datetime import datetime
from functools import wraps


def load_host_config():
    """Load host and port configuration from conf/host.conf."""
    config = configparser.ConfigParser()
    config.read('conf/host.conf')

    host = config.get('server', 'host', fallback='0.0.0.0')
    port = config.getint('server', 'port', fallback=5000)
    return host, port


def login_required(f):
    """Decorator to require login for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    """Application factory pattern for creating the Flask app."""
    app = Flask(
        __name__,
        template_folder='data/html',
        static_folder='data'
    )
    app.secret_key = 'your_secret_key'  # Replace with a secure key

    # Configure MySQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://apiUser:apiPassword@localhost/api_auth'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT configuration
    app.config['JWT_SECRET_KEY'] = 'another_secret_key'  # Replace with a secure key

    # Upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'data', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB limit

    # Initialize the database and JWT
    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(file_bp)  # Register the file management blueprint
    app.register_blueprint(game_bp, url_prefix='/game')
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
            user = db.session.get(Account, user_id)
            if user:
                user.online = False
                db.session.commit()

        session.clear()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = db.session.get(Account, session['user_id'])
        session['email'] = user.email
        session['last_login'] = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Unknown'
        return render_template('dashboard.html', username=session['username'])

    @app.route('/create-account', methods=['GET', 'POST'])
    def create_account():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            if Account.query.filter((Account.username == username) | (Account.email == email)).first():
                flash('Username or email already exists!', 'danger')
                return redirect(url_for('create_account'))

            hashed_password = generate_password_hash(password)
            new_account = Account(username=username, email=email, password=hashed_password)
            db.session.add(new_account)
            db.session.commit()

            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))

        return render_template('auth/create_account.html')

    return app


if __name__ == '__main__':
    run_installation()
    host, port = load_host_config()
    app = create_app()
    app.run(host=host, port=port, debug=True)

