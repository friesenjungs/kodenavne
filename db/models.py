from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

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

    role = relationship("Role", back_populates="game_sessions")
    game = relationship("Game", back_populates="user_sessions")
    user_session = relationship("UserSession", back_populates="game_sessions")

    def __repr__(self):
        return f'GAMESESSION<game_id:{self.game_id}, session_id:{self.session_id}>'


class Game(database.Model):
    """Class for database table GAME"""

    __tablename__ = 'GAME'

    game_id = database.Column(database.Integer, primary_key=True)
    room_code = database.Column(database.String())
    active = database.Column(database.Boolean)
    started = database.Column(database.Boolean)
    settings = database.Column(MutableDict.as_mutable(JSONB))
    teams = database.Column(MutableDict.as_mutable(JSONB))
    current_team = database.Column(database.Integer)
    current_team_role = database.Column(database.ForeignKey("ROLE.role_id"))
    current_hint_amount = database.Column(database.Integer)

    gameset = relationship("GameSet", back_populates="game", uselist=False)
    user_sessions = relationship("GameSession", back_populates="game", lazy="dynamic")

    def __init__(self, room_code):
        self.room_code = room_code
        self.active = True
        self.started = False
        self.settings = {"board_size": {"x": 5, "y": 5}, "random": False, "lang": "en"}

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

    game_sessions = relationship("GameSession", back_populates="role")

    def __init__(self, role_name):
        self.role_name = role_name

    def __repr__(self):
        return f'ROLE<role_id:{self.role_id}, role_name:{self.role_name}>'


class BankWord(database.Model):
    """Class for database table BANK_WORD"""

    __tablename__ = 'BANK_WORD'

    wordbank_id = database.Column(database.ForeignKey("WORD_BANK.wordbank_id"), primary_key=True)
    word_id = database.Column(database.ForeignKey("WORD.word_id"), primary_key=True)

    wordbank = relationship("WordBank", back_populates="words")
    word = relationship("Word", back_populates="wordbanks")

    def __repr__(self):
        return f'BANK_WORD<wordbank_id:{self.wordbank_id}, word_id:{self.word_id}>'


class GameWord(database.Model):
    """Class for database table GAME_WORD"""

    __tablename__ = 'GAME_WORD'

    gameset_id = database.Column(database.ForeignKey("GAME_SET.gameset_id"), primary_key=True)
    word_id = database.Column(database.ForeignKey("WORD.word_id"), primary_key=True)
    card_position = database.Column(database.Integer)
    turned_over = database.Column(database.Boolean)
    cardrole_id = database.Column(database.ForeignKey("CARD_ROLE.cardrole_id"))

    gameset = relationship("GameSet", back_populates="words")
    word = relationship("Word", back_populates="gamesets")

    def __repr__(self):
        return f'GAME_WORD<gameset_id:{self.gameset_id}, word_id:{self.word_id}>'


class Word(database.Model):
    """Class for database table WORD"""

    __tablename__ = 'WORD'

    word_id = database.Column(database.Integer, primary_key=True)
    word_content = database.Column(database.String())

    gamesets = relationship("GameWord", back_populates="word")
    wordbanks = relationship("BankWord", back_populates="word")

    def __repr__(self):
        return f'WORD<word_id:{self.word_id}, word_content:{self.word_content}>'


class WordBank(database.Model):
    """Class for database table WORD_BANK"""

    __tablename__ = 'WORD_BANK'

    wordbank_id = database.Column(database.Integer, primary_key=True)
    wordbank_name = database.Column(database.String())
    lang = database.Column(database.String())
    description = database.Column(database.String())

    words = relationship("BankWord", back_populates="wordbank", lazy="dynamic")
    gamesets = relationship("GameSet")

    def __repr__(self):
        return f'WORD_BANK<wordbank_id:{self.wordbank_id}, wordbank_name:{self.wordbank_name}>'


class GameSet(database.Model):
    """Class for database table GAME_SET"""

    __tablename__ = 'GAME_SET'

    gameset_id = database.Column(database.Integer, primary_key=True)
    wordbank_id = database.Column(database.ForeignKey("WORD_BANK.wordbank_id"))
    game_id = database.Column(database.ForeignKey("GAME.game_id"))

    game = relationship("Game", back_populates="gameset")
    words = relationship("GameWord", back_populates="gameset", lazy="dynamic")

    def __repr__(self):
        return f'GAME_SET<gameset_id:{self.gameset_id}, wordbank_id:{self.wordbank_id}>'


class CardRole(database.Model):
    """Class for database table CARD_ROLE"""

    __tablename__ = 'CARD_ROLE'

    cardrole_id = database.Column(database.Integer, primary_key=True)
    cardrole_name = database.Column(database.String())

    gamewords = relationship("GameWord")

    def __repr__(self):
        return f'CARD_ROLE<cardrole_id:{self.cardrole_id}, cardrole_name:{self.cardrole_name}>'
