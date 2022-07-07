import os
import random
import string
import uuid
import json
import fnmatch

from flask import Flask, render_template, request, make_response, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from flask_migrate import Migrate
import db
import sqlalchemy.exc

app = Flask(__name__)
socketio = SocketIO(app)
app.config.from_pyfile('config.py')

db.database.init_app(app)
migrate = Migrate(app, db.database)


def generate_unique_room_code():
    room_code = ""
    unique_code = False
    while not unique_code:
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        unique_code = db.Game.query.filter_by(room_code=room_code).first() is None
    return room_code


def create_session_cookie():
    session_cookie = str(uuid.uuid4())
    user_session = db.UserSession(session_cookie=session_cookie)
    db.database.session.add(user_session)
    db.database.session.commit()
    return session_cookie


def create_game_session(room_code):
    session_cookie = request.cookies.get("session")

    user_session = db.UserSession.query.filter_by(session_cookie=session_cookie).first()
    game = db.Game.query.filter_by(room_code=room_code).first()

    game_session = db.GameSession.query.filter_by(game_id=game.game_id, session_id=user_session.session_id).first()
    if game_session is None:
        game_session = db.GameSession()

        game_session.game = game
        game_session.user_session = user_session

        player_in_room = db.GameSession.query.join(db.Game).filter(db.Game.game_id == game.game_id).all()

        game_session.player = len(player_in_room)
        game_session.user_name = f"Player {game_session.player}"

        if len(player_in_room) == 1:
            game_session.admin = True
        else:
            game_session.admin = False

        db.database.session.add(game_session)
        db.database.session.commit()


@app.before_first_request
def populate_with_initial():
    with app.app_context():
        print("Updating DB entries...")
        entries = []
        for file in fnmatch.filter(os.listdir(os.environ["POSTGRES_DB_DEFAULT_DATA"]), "*.json"):
            with open(f"{os.environ['POSTGRES_DB_DEFAULT_DATA']}/{file}", "r") as init_file:
                try:
                    init_json = json.load(init_file)
                    db_table_name = file.split(".json")[0]
                    db_table = getattr(globals()["db"], db_table_name)
                    for entry in init_json:
                        try:
                            if db_table.query.filter_by(**entry).first() is None:
                                print(f"Inserting entry {entry} to table {db_table_name}")
                                entries.append(db_table(**entry))
                        except sqlalchemy.exc.InvalidRequestError as e:
                            print(e)
                        except sqlalchemy.exc.DataError as e:
                            print(e)
                except json.decoder.JSONDecodeError:
                    print(f"File {file} has no valid json format")
                except KeyError:
                    print(f"File {file} has no corresponding database table")
        if len(entries) == 0:
            print("No changes are made to DB, all entries up to date")
        else:
            db.database.session.add_all(entries)
            db.database.session.commit()
            print("Successfully applied changes to DB")


@app.before_request
def cookie_manager():
    session_cookie = request.cookies.get("session")

    existing_session = db.UserSession.query.filter_by(session_cookie=session_cookie).first()
    if existing_session is None:
        session_cookie = ""

    if session_cookie is None or session_cookie == "":
        session_cookie = create_session_cookie()
        resp = make_response(redirect(url_for("home")))
        resp.set_cookie("session", session_cookie, secure=True, httponly=True)
        return resp


@app.route("/")
def home():
    """main page"""
    resp = make_response(render_template("index.html"))
    return resp


@app.route("/room/create", methods=['POST'])
def create_room():
    room_code = generate_unique_room_code()
    db.database.session.add(db.Game(room_code=room_code, active=True))
    db.database.session.commit()
    return redirect(url_for("game_room", room_code=room_code))


@app.route("/room/join", methods=['POST'])
def join_redirect():
    return redirect(url_for("game_room", room_code=request.form['code']))


@app.route("/room/<room_code>")
def game_room(room_code):
    room_exist = db.Game.query.filter_by(room_code=room_code, active=True).first() is not None
    if room_exist:
        create_game_session(room_code)
        resp = make_response(render_template("room.html"))
        return resp
    else:
        return render_template("roomnotfound.html")


@socketio.on('connect')
def connect_socket():
    session_cookie = request.cookies.get("session")
    print(f"User with cookie {session_cookie} connected to socket")


@socketio.on("join")
def join_room_socket(data):
    session_cookie = request.cookies.get("session")
    possible_sessions = db.GameSession.query.join(db.Game, db.UserSession).filter(
        db.UserSession.session_cookie == session_cookie).filter(db.Game.active == True).all()
    requested_room_code = data["room_code"]
    search_session = [s for s in possible_sessions if s.game.room_code == requested_room_code]
    if len(search_session) == 1:
        game_session = search_session[0]
        session["game_session_ids"] = (game_session.game_id, game_session.session_id)
        game_session.active = True

        join_room(requested_room_code)
        print(f"User with cookie {session_cookie} joined room {requested_room_code}")

        emit("server message", {"message": f"Let's welcome {game_session.user_name} in the room"},
             room=requested_room_code)
        db.database.session.merge(game_session)
        db.database.session.commit()


@socketio.on("client message")
def client_message_socket(data):
    session_cookie = request.cookies.get("session")
    print(f"Got message from {session_cookie}: {data['message']}")


@socketio.on("set username")
def client_set_username_socket(data):
    session_cookie = request.cookies.get("session")
    if "username" in data and data["username"] is not None and data["username"] != "":
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        game_session.user_name = data["username"]
        db.database.session.merge(game_session)
        db.database.session.commit()
        print(f"Changed username for {game_session.user_session.session_cookie} to {game_session.user_name}")
    else:
        print(f"Malformed username data from {session_cookie}")


@socketio.on('disconnect')
def disconnect_socket():
    session_cookie = request.cookies.get("session")
    print(f"User with cookie {session_cookie} disconnected from socket")
    if "game_session_ids" in session:
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        game_session.active = False
        remaining_players = db.GameSession.query.join(db.Game).filter(db.Game.game_id == game_session.game_id).filter(
            db.GameSession.active == True).all()
        if len(remaining_players) == 0:
            inactive_game = db.Game.query.filter_by(game_id=game_session.game_id).first()
            inactive_game.active = False
            db.database.session.merge(inactive_game)
            print(f"Room {inactive_game.room_code} is left with no players - status is now inactive")
        elif game_session.admin:
            game_session.admin = False
            new_possible_admins = [p for p in remaining_players if p.session_id != game_session.session_id]
            new_admin = new_possible_admins[random.randint(0, len(new_possible_admins) - 1)] if len(
                new_possible_admins) == 1 else new_possible_admins[0]
            new_admin.admin = True
            print(f"Player with username {new_admin.user_name} is the new admin of room with id {new_admin.game_id}")
            db.database.session.merge(new_admin)
        db.database.session.merge(game_session)
        db.database.session.commit()


if __name__ == "__main__":
    socketio.run(app, host='kodenavne-dev', port=5000)
