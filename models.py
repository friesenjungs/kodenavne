from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class GameSession(db.Model):
    """Class for database table GAME_SESSION"""

    __tablename__ = 'GAME_SESSION'

    game_id = db.Column(db.ForeignKey("GAME.game_id"), primary_key=True)
    session_id = db.Column(db.ForeignKey("USER_SESSION.session_id"), primary_key=True)
    user_name = db.Column("user_name", db.String())
    team_id = db.Column("team_id", db.Integer)
    role_id = db.Column(db.ForeignKey("ROLE.role_id"))

    game = relationship("Game", back_populates="user_sessions")
    user_session = relationship("UserSession", back_populates="games")


class Game(db.Model):
    """Class for database table GAME"""

    __tablename__ = 'GAME'

    game_id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String())
    active = db.Column(db.Boolean)
    user_sessions = relationship("GameSession", back_populates="game")

    def __init__(self, room_code, active):
        self.room_code = room_code
        self.active = active

    def __repr__(self):
        return f'GAME<game_id:{self.game_id}, room_code:{self.room_code}>'


class UserSession(db.Model):
    """Class for database table USER_SESSION"""

    __tablename__ = 'USER_SESSION'

    session_id = db.Column(db.Integer, primary_key=True)
    session_cookie = db.Column(db.String())
    games = relationship("GameSession", back_populates="user_session")

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie

    def __repr__(self):
        return f'USER_SESSION<session_id:{self.session_id}, session_cookie:{self.session_cookie}>'


class Role(db.Model):
    """Class for database table ROLE"""

    __tablename__ = 'ROLE'

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String())

    game_sessions = relationship("GameSession")

    def __init__(self, role_name):
        self.role_name = role_name

    def __repr__(self):
        return f'Role<role_id:{self.role_id}, role_name:{self.role_name}>'
