import os
import mysql.connector
from mysql.connector import errorcode
from modules.db_models import db, Account
from flask import Flask

# MySQL configuration
DB_NAME = 'api_auth'
DB_CONFIG = {
    'user': 'apiUser',
    'password': 'apiPassword',
    'host': 'localhost'
}

def create_database(cursor):
    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
        print(f"Database {DB_NAME} created successfully.")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            print(f"Database {DB_NAME} already exists.")
        else:
            print(f"Failed to create database {DB_NAME}: {err}")
            exit(1)

def check_and_create_tables(app):
    # Check and create tables using SQLAlchemy
    with app.app_context():
        db.create_all()
        print("All tables checked and created if not exist.")

def run_installation():
    # Connect to MySQL server
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
        # Create database if not exists
        cursor.execute(f"USE {DB_NAME}")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = DB_NAME
        else:
            print(err)
            exit(1)

    # Ensure tables exist
    cursor.close()
    cnx.close()

    # Flask app for table creation
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://apiUser:apiPassword@localhost/api_auth'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    check_and_create_tables(app)

