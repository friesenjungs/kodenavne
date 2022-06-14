import os

basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
TESTING = False
CSRF_ENABLED = True
STATIC_FOLDER = 'static'
TEMPLATES_FOLDER = 'templates'
SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ['POSTGRES_USER']}:" \
                          f"@db:5432/{os.environ['POSTGRES_DB']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
