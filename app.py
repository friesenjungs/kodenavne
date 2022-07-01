import random
import string
import uuid
import json

from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_socketio import SocketIO
from flask_migrate import Migrate
from models import db, Game, GameSession, UserSession, Role

app = Flask(__name__)
socketio = SocketIO(app)
app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)


def generate_unique_room_code():
    room_code = ""
    unique_code = False
    while not unique_code:
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        unique_code = Game.query.filter_by(room_code=room_code).first() is None
    return room_code


def create_session_cookie():
    session_cookie = request.cookies.get("session")
    if session_cookie is None or session_cookie == "":
        session_cookie = str(uuid.uuid4())
        user_session = UserSession(session_cookie=session_cookie)
        db.session.add(user_session)
        db.session.commit()
        return session_cookie


def create_game_session(room_code):
    session_cookie = request.cookies.get("session")
    if session_cookie is None or session_cookie == "":
        session_cookie = create_session_cookie()

    user_session = UserSession.query.filter_by(session_cookie=session_cookie).first()
    game = Game.query.filter_by(room_code=room_code).first()

    game_session = GameSession.query.filter_by(game_id=game.game_id, session_id=user_session.session_id).first()
    if game_session is None:
        game_session = GameSession()

        game_session.game = game
        game_session.user_session = user_session

        db.session.add(game_session)
        db.session.commit()

    return game_session


@app.before_first_request
def populate_with_initial():
    with app.app_context():
        with open("./db_initial/Role.json", "r") as roles:
            roles_json = json.load(roles)
            for role in roles_json:
                role_name = role["role_name"]
                if Role.query.filter_by(role_name=role_name).first() is None:
                    new_role = Role(role_name=role_name)
                    db.session.add(new_role)
        db.session.commit()


@app.route("/")
def home():
    """main page"""
    resp = make_response(render_template("index.html"))
    return resp


@app.route("/room/create", methods=['POST'])
def create_room():
    room_code = generate_unique_room_code()
    db.session.add(Game(room_code=room_code, active=True))
    db.session.commit()
    return redirect(url_for("join_room", room_code=room_code))


@app.route("/room/join", methods=['POST'])
def join_redirect():
    return redirect(url_for("join_room", room_code=request.form['code']))


@app.route("/room/<room_code>")
def join_room(room_code):
    room_exist = Game.query.filter_by(room_code=room_code, active=True).first() is not None
    if room_exist:
        game_session = create_game_session(room_code)
        resp = make_response(room_code)
        if request.cookies.get("session") != game_session.user_session.session_cookie:
            resp.set_cookie("session", game_session.user_session.session_cookie)
        return resp
    else:
        return render_template("roomnotfound.html")


if __name__ == "__main__":
    socketio.run(app, host='kodenavne-dev', port=5000)
