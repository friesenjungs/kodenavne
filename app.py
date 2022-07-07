import os
import random
import string
import uuid
import json
import fnmatch
import re

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

allowed_board_sizes = [
    {"x": 5, "y": 5},
    {"x": 6, "y": 6},
    {"x": 7, "y": 7},
    {"x": 8, "y": 8}
]


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
        if bool(re.match(r"(\/room\/[A-Z\d]{6})$", request.path)):
            resp = make_response(redirect(url_for("game_room", room_code=request.path.split("/")[-1])))
        resp.set_cookie("session", session_cookie, secure=True, httponly=True)
        return resp


@app.route("/")
def home():
    """main page"""
    resp = make_response(render_template("index.html"))
    return resp


@app.route("/room/create", methods=['GET'])
def create_room():
    room_code = generate_unique_room_code()
    db.database.session.add(db.Game(room_code=room_code))
    db.database.session.commit()
    return redirect(url_for("game_room", room_code=room_code))


@app.route("/room/join", methods=['POST'])
def join_redirect():
    return redirect(url_for("game_room", room_code=request.form['code']))


@app.route("/room/<room_code>")
def game_room(room_code):
    game_instance = db.Game.query.filter_by(room_code=room_code, active=True).first()

    if game_instance is None:
        return render_template("roomerror.html", errortext="Sorry, this room does not exist!")

    users_in_room = db.GameSession.query.filter_by(game_id=game_instance.game_id, active=True).count()
    if game_instance.started:
        return render_template("roomerror.html", errortext="Sorry, this game already started!")
    elif users_in_room == 8:
        return render_template("roomerror.html", errortext="Sorry, this room reached the maximum amount of players!")
    else:
        create_game_session(room_code)
        resp = make_response(render_template("room.html"))
        return resp


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
def set_username_socket(data):
    session_cookie = request.cookies.get("session")
    if "username" in data and data["username"] is not None and data["username"] != "":
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        game_session.user_name = data["username"]
        db.database.session.merge(game_session)
        db.database.session.commit()
        print(f"Changed username for {game_session.user_session.session_cookie} to {game_session.user_name}")
        return True
    else:
        print(f"Malformed username data from {session_cookie}")
        return False


@socketio.on("set setting")
def set_setting_socket(data):
    session_cookie = request.cookies.get("session")
    game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                  session_id=session["game_session_ids"][1]).first()
    if game_session.admin:
        changes = False
        game_instance = db.Game.query.filter_by(game_id=game_session.game_id).first()
        if "board_size" in data:
            changes = True
            if data["board_size"] in allowed_board_sizes:
                print(f"User with cookie {session_cookie} updated board_size to {data['board_size']}")
                game_instance.settings["board_size"] = data["board_size"]
                print(f"Current settings for game room {game_instance.room_code}: {game_instance.settings}")
            else:
                print(f"User with cookie {session_cookie} gave invalid setting for board size ({data['board_size']})")
        if "random" in data:
            changes = True
            if data["random"] is True or data["random"] is False:
                print(f"User with cookie {session_cookie} updated random setting to {data['random']}")
                game_instance.settings["random"] = data["random"]
            else:
                print(f"User with cookie {session_cookie} gave invalid setting for random ({data['random']})")
        if changes:
            db.database.session.commit()
            return True
        else:
            print(f"User with cookie {session_cookie} did not update settings")
    return False


@socketio.on("set team")
def set_team_socket(data):
    session_cookie = request.cookies.get("session")
    if "team" in data and "role" in data and isinstance(data["team"], int) and isinstance(data["role"], str):
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        users_in_session = game_session.game.user_sessions
        amount_of_users = len(users_in_session.filter_by(active=True).all())
        amount_of_teams = amount_of_users // 2 if amount_of_users % 2 == 0 else amount_of_users // 2 + 1
        amount_of_teams = amount_of_teams if amount_of_teams >= 2 else 2

        chosen_role = db.Role.query.filter_by(role_name=data["role"]).first()
        if 0 <= data["team"] < amount_of_teams and chosen_role is not None:
            already_assigned = users_in_session.filter_by(team=data["team"],
                                                          role_id=chosen_role.role_id).first() is not None
            if not already_assigned:
                game_session.team = data["team"]
                game_session.role_id = chosen_role.role_id
                db.database.session.commit()
                print(f"User with cookie {session_cookie} changed team to {game_session.team} and role to {chosen_role.role_name}")
                return True
            else:
                print(f"Requested team and role from user with cookie {session_cookie} is already assigned")
        else:
            print(f"Requested team number by user with cookie {session_cookie} is out of scope or role does not exist ({data})")
    else:
        print(f"Malformed team and role data from {session_cookie}")
    return False


@socketio.on("start game")
def start_game_socket():
    session_cookie = request.cookies.get("session")
    if "game_session_ids" in session:
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        if game_session.admin:
            game_instance = db.Game.query.filter_by(game_id=game_session.game_id).first()
            game_instance.started = True

            # here comes game start action

            print(f"User with cookie {session_cookie} started game in room {game_instance.room_code}")
        else:
            print(f"User with cookie {session_cookie} is not authorized to start game")


@socketio.on("performed operative action")
def performed_operative_action_socket(data):
    session_cookie = request.cookies.get("session")
    if "cards" in data:
        pass
    else:
        print(f"Malformed operative action from {session_cookie}")


@socketio.on("performed spymaster action")
def performed_spymaster_action_socket(data):
    session_cookie = request.cookies.get("session")
    if "hint" in data and "amount" in data:
        pass
    else:
        print(f"Malformed spymaster action from {session_cookie}")


@socketio.on('disconnect')
def disconnect_socket():
    session_cookie = request.cookies.get("session")
    print(f"User with cookie {session_cookie} disconnected from socket")
    if "game_session_ids" in session:
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        game_session.active = False
        if not game_session.game.started:
            game_session.team = None
            game_session.role_id = None
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
