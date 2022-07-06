from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

database = SQLAlchemy()


class GameSession(database.Model):
    """Class for database table GAME_SESSION"""

    __tablename__ = 'GAME_SESSION'

    game_id = database.Column(database.ForeignKey("GAME.game_id"), primary_key=True)
    session_id = database.Column(database.ForeignKey("USER_SESSION.session_id"), primary_key=True)
    user_name = database.Column("user_name", database.String())
    player = database.Column("player", database.Integer)
    team = database.Column("team", database.Integer)
    role_id = database.Column(database.ForeignKey("ROLE.role_id"))
    active = database.Column(database.Boolean)
    admin = database.Column(database.Boolean)

    game = relationship("Game", back_populates="user_sessions")
    user_session = relationship("UserSession", back_populates="game_sessions")


class Game(database.Model):
    """Class for database table GAME"""

    __tablename__ = 'GAME'

    game_id = database.Column(database.Integer, primary_key=True)
    room_code = database.Column(database.String())
    active = database.Column(database.Boolean)

    user_sessions = relationship("GameSession", back_populates="game")

    def __init__(self, room_code, active):
        self.room_code = room_code
        self.active = active

    def __repr__(self):
        return f'GAME<game_id:{self.game_id}, room_code:{self.room_code}>'


class UserSession(database.Model):
    """Class for database table USER_SESSION"""

    __tablename__ = 'USER_SESSION'

    session_id = database.Column(database.Integer, primary_key=True)
    session_cookie = database.Column(database.String())

    game_sessions = relationship("GameSession", back_populates="user_session")

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie

    def __repr__(self):
        return f'USER_SESSION<session_id:{self.session_id}, session_cookie:{self.session_cookie}>'


class Role(database.Model):
    """Class for database table ROLE"""

    __tablename__ = 'ROLE'

    role_id = database.Column(database.Integer, primary_key=True)
    role_name = database.Column(database.String())

    game_sessions = relationship("GameSession")

    def __init__(self, role_name):
        self.role_name = role_name

    def __repr__(self):
        return f'Role<role_id:{self.role_id}, role_name:{self.role_name}>'
