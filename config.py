import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
DB_HOST = os.getenv('DB_HOST', '10.0.2.15:5432')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Passw0rd')
DB_NAME = os.getenv('DB_NAME', 'fyyur')

DB_PATH = 'postgresql+psycopg2://{}:{}@{}/{}'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = DB_PATH
