import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

DEBUG = False
TESTING = False
CSRF_ENABLED = True
STATIC_FOLDER = 'static'
TEMPLATES_FOLDER = 'templates'
SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}" \
                          f"@db:5432/{os.environ['POSTGRES_DB']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
