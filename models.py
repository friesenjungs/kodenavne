from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Class for database table user"""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __repr__(self):
        return '<id {}>'.format(self.id)
