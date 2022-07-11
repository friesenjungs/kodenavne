import os
import random
import string
import uuid
import json
import fnmatch
import re

from flask import Flask, render_template, request, make_response, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
import db
import sqlalchemy.exc
from sqlalchemy.sql.expression import func

app = Flask(__name__)
socketio = SocketIO(app)
app.config.from_pyfile('config.py')

db.database.init_app(app)
migrate = Migrate(app, db.database)

allowed_board_sizes = [
    {"x": 5, "y": 5},
    {"x": 5, "y": 6},
    {"x": 6, "y": 6},
    {"x": 6, "y": 7},
    {"x": 7, "y": 7},
    {"x": 7, "y": 8},
    {"x": 8, "y": 8}
]
allowed_languages = [
    "en",
    "de"
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


def get_users_json(game_session):
    active_users_in_session = game_session.game.user_sessions.filter_by(active=True).all()
    players = []
    for user in active_users_in_session:
        is_me = user.game_id == game_session.game_id and user.session_id == game_session.session_id
        user_json = {"name": user.user_name, "me": is_me}
        user_role = db.Role.query.filter_by(role_id=user.role_id).first()
        if user_role is not None:
            user_json["role"] = user_role.role_name
        if user.team is not None:
            user_json["team"] = user.team
        players.append(user_json)
    return players


def get_words_json(game_instance, role):
    game_words = game_instance.gameset.words.all()
    words_json = []
    for game_word in game_words:
        game_word_json = {"id": game_word.card_position, "text": game_word.word.word_content}
        if role == "Operative" and not game_word.turned_over:
            game_word_json["team"] = 0
        else:
            game_word_json["team"] = game_word.cardrole_id
        words_json.append(game_word_json)
    return words_json


def join_special_socket_rooms(game_session):
    session_cookie = game_session.user_session.session_cookie
    role_name = game_session.role.role_name
    room_code = game_session.game.room_code
    team = game_session.team
    join_room(f"{room_code}/{role_name}")
    print(f"User with cookie {session_cookie} joined room {room_code}/{role_name}")
    join_room(f"{room_code}/{role_name}/{game_session.team}")
    print(f"User with cookie {session_cookie} joined room {room_code}/{role_name}/{team}")


def get_remaining_cards(game_session):
    all_teams = game_session.game.teams
    remaining_words_all = {}
    for team in all_teams.keys():
        remaining_words = game_session.game.gameset.words.filter_by(cardrole_id=team, turned_over=False).count()
        remaining_words_all[team] = remaining_words
    return remaining_words_all


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
    session_cookie = request.cookies.get("session")
    game_instance = db.Game.query.filter_by(room_code=room_code, active=True).first()

    if game_instance is None:
        return render_template("roomerror.html", errortext="Sorry, this room does not exist!")

    users_in_room = db.GameSession.query.filter_by(game_id=game_instance.game_id, active=True).count()
    possible_to_join = db.GameSession.query.join(db.UserSession).filter(db.GameSession.game_id == game_instance.game_id).filter(db.UserSession.session_cookie == session_cookie).filter(db.GameSession.role_id is not None).filter(db.GameSession.team is not None).first() is not None
    if game_instance.started and not possible_to_join:
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

        emit("show toast", {"title": "New player", "message": f"Let's welcome {game_session.user_name} in the room", "icon": "bi-info-square-fill"},
             room=requested_room_code)
        join_room(requested_room_code)

        print(f"User with cookie {session_cookie} joined room {requested_room_code}")

        emit("show players", get_users_json(game_session), room=game_session.game.room_code)

        if game_session.game.started and game_session.role_id is not None and game_session.team is not None:
            start_game_data = {"board_size": game_session.game.settings["board_size"]}
            join_special_socket_rooms(game_session)
            emit("start game", start_game_data)
            emit("show cards", get_words_json(game_session.game, game_session.role.role_name))
        else:
            emit("show settings", game_session.game.settings)

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
        emit("show players", get_users_json(game_session), room=game_session.game.room_code)
        return True
    else:
        print(f"Malformed username data from {session_cookie}")
        return False


@socketio.on("set setting")
def set_setting_socket(data):
    session_cookie = request.cookies.get("session")
    game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                  session_id=session["game_session_ids"][1]).first()
    if not game_session.game.started:
        if game_session.admin:
            changes = False
            game_instance = db.Game.query.filter_by(game_id=game_session.game_id).first()
            if "board_size" in data:
                if data["board_size"] in allowed_board_sizes:
                    changes = True
                    print(f"User with cookie {session_cookie} updated board_size to {data['board_size']}")
                    game_instance.settings["board_size"] = data["board_size"]
                else:
                    print(f"User with cookie {session_cookie} gave invalid setting for board size ({data['board_size']})")
            if "random" in data:
                if data["random"] is True or data["random"] is False:
                    changes = True
                    print(f"User with cookie {session_cookie} updated random setting to {data['random']}")
                    game_instance.settings["random"] = data["random"]
                else:
                    print(f"User with cookie {session_cookie} gave invalid setting for random ({data['random']})")
            if "lang" in data:
                if data["lang"] in allowed_languages:
                    changes = True
                    print(f"User with cookie {session_cookie} updated language setting to {data['lang']}")
                    game_instance.settings["lang"] = data["lang"]
                else:
                    print(f"User with cookie {session_cookie} gave invalid setting for lang ({data['random']})")
            if changes:
                print(f"Current settings for game room {game_instance.room_code}: {game_instance.settings}")
                emit("show settings", game_instance.settings, room=game_instance.room_code)
                db.database.session.commit()
                return True
            else:
                print(f"User with cookie {session_cookie} did not update settings")
        emit("show settings", game_session.game.settings, room=game_session.game.room_code)
    return False


@socketio.on("set team")
def set_team_socket(data):
    session_cookie = request.cookies.get("session")
    if "team" in data and "role" in data and isinstance(data["team"], int) and isinstance(data["role"], str):
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        if not game_session.game.started:
            users_in_session = game_session.game.user_sessions

            # amount_of_users = len(users_in_session.filter_by(active=True).all())
            # amount_of_teams = amount_of_users // 2 if amount_of_users % 2 == 0 else amount_of_users // 2 + 1
            # amount_of_teams = amount_of_teams if amount_of_teams >= 2 else 2
            amount_of_teams = 4

            chosen_role = db.Role.query.filter_by(role_name=data["role"]).first()
            if 0 < data["team"] <= amount_of_teams and chosen_role is not None:
                already_assigned = users_in_session.filter_by(team=data["team"],
                                                              role_id=chosen_role.role_id).first() is not None
                if not already_assigned:
                    if game_session.role_id is not None and game_session.team is not None:
                        role_room = game_session.role.role_name
                        leave_room(f"{game_session.game.room_code}/{role_room}")
                        print(f"User with cookie {session_cookie} left room {game_session.game.room_code}/{role_room}")
                        leave_room(f"{game_session.game.room_code}/{role_room}/{game_session.team}")
                        print(f"User with cookie {session_cookie} left room {game_session.game.room_code}/{role_room}/{game_session.team}")
                    game_session.team = data["team"]

                    game_session.role_id = chosen_role.role_id
                    db.database.session.commit()
                    join_special_socket_rooms(game_session)
                    print(f"User with cookie {session_cookie} changed team to {game_session.team} and role to {chosen_role.role_name}")
                    emit("show players", get_users_json(game_session), room=game_session.game.room_code)
                    return True
                else:
                    print(f"Requested team and role from user with cookie {session_cookie} is already assigned")
            else:
                print(f"Requested team number by user with cookie {session_cookie} is out of scope or role does not exist ({data})")
        else:
            print(f"User with cookie {session_cookie} can't change teams - game {game_session.game.room_code} already started")
    else:
        print(f"Malformed team and role data from {session_cookie}")
    return False


@socketio.on("start game")
def start_game_socket():
    session_cookie = request.cookies.get("session")
    reason = "Could not start game "
    if "game_session_ids" in session:
        game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                      session_id=session["game_session_ids"][1]).first()
        active_users_in_session = game_session.game.user_sessions.filter_by(active=True).all()
        teams = {}
        for user in active_users_in_session:
            if user.team is not None:
                teams[str(user.team)] = [user.session_id] if str(user.team) not in teams else teams[str(user.team)] + [
                    user.session_id]
        team_sizes = [len(value) for value in teams.values()]
        if sum(team_sizes) != len(active_users_in_session):
            reason += "- All active players must be assigned to a team"
        elif not all(element == 2 for element in team_sizes):
            reason += "- All teams must consist of two players"
        elif not len(team_sizes) >= 2:
            reason += "- You need at least two teams to play the game"
        else:
            if game_session.admin:
                game_instance = db.Game.query.filter_by(game_id=game_session.game_id).first()
                game_instance.started = True

                amount_of_cards = game_instance.settings["board_size"]["x"] * game_instance.settings["board_size"]["y"]

                wordbank = db.WordBank.query.filter_by(wordbank_name="base", lang=game_instance.settings["lang"]).first()
                words = wordbank.words.order_by(func.random()).limit(amount_of_cards).all()
                gameset = db.GameSet(wordbank_id=wordbank.wordbank_id, game_id=game_instance.game_id)
                db.database.session.add(gameset)
                db.database.session.commit()

                gameset = db.GameSet.query.filter_by(game_id=game_instance.game_id).first()
                game_instance.gameset_id = gameset.gameset_id

                roles = [role for role in map(int, teams.keys()) for _ in range(amount_of_cards//(len(team_sizes) + 1))]
                roles = roles + [5 for _ in range(amount_of_cards - len(roles) - 1)] + [6]
                random.shuffle(roles)
                gamewords = []
                for i, word in enumerate(words):
                    gamewords.append(db.GameWord(gameset_id=gameset.gameset_id, word_id=word.word_id, card_position=i, cardrole_id=roles[i], turned_over=False))

                db.database.session.add_all(gamewords)

                print(f"User with cookie {session_cookie} started game in room {game_instance.room_code}")
                print(f"Playing teams in room {game_instance.room_code}: {teams}")

                start_game_data = {"board_size": game_instance.settings["board_size"]}
                emit("start game", start_game_data, room=game_instance.room_code)
                emit("show cards", get_words_json(game_instance, "Operative"), room=f"{game_instance.room_code}/Operative")
                emit("show cards", get_words_json(game_instance, "Spymaster"), room=f"{game_instance.room_code}/Spymaster")

                team_to_start = random.choice(list(map(int, teams.keys())))
                emit("perform spymaster action", room=f"{game_instance.room_code}/Spymaster/{team_to_start}")

                game_instance.teams = teams
                game_instance.current_team = team_to_start
                game_instance.current_team_role = db.Role.query.filter_by(role_name="Spymaster").first().role_id
                db.database.session.commit()
                return True
            else:
                reason += " - You are not authorized"
        print(f"User with cookie {session_cookie} did not managed to start game (message: {reason})")
        emit("show toast", {"title": "Game error", "message": f"{reason}", "icon": "bi-x-octagon-fill"})
    return False


@socketio.on("performed operative action")
def performed_operative_action_socket(data):
    session_cookie = request.cookies.get("session")
    game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                  session_id=session["game_session_ids"][1]).first()
    game_instance = game_session.game
    role_name = db.Role.query.filter_by(role_id=game_instance.current_team_role).first().role_name
    if "id" in data and game_session.team == game_instance.current_team and role_name == "Operative":
        word_to_turn = game_instance.gameset.words.filter_by(card_position=data["id"]).first()
        if not word_to_turn.turned_over:
            word_to_turn.turned_over = True
            if word_to_turn.cardrole_id == db.CardRole.query.filter_by(cardrole_name="black").first().cardrole_id:
                emit("end game", {"looser_team": game_session.team}, room=game_instance.room_code)
                game_instance.current_team = word_to_turn.cardrole_id
                game_instance.current_hint_amount = 0
            all_remaining_cards = get_remaining_cards(game_session)
            for key, value in all_remaining_cards.items():
                if value == 0:
                    emit("end game", {"winner_team": key}, room=game_instance.room_code)
                    game_instance.current_team = word_to_turn.cardrole_id
                    game_instance.current_hint_amount = 0
            if word_to_turn.cardrole_id != game_instance.current_team or game_instance.current_hint_amount == 1:
                next_team = game_instance.current_team
                for i in range(1, 8):
                    if str((next_team+i) % 5) in game_instance.teams:
                        game_instance.current_team = (next_team+i) % 5
                        break
                game_instance.current_team_role = db.Role.query.filter_by(role_name="Spymaster").first().role_id
                game_instance.current_hint_amount = None
                emit("perform spymaster action", room=f"{game_instance.room_code}/Spymaster/{game_instance.current_team}")
            else:
                game_instance.current_hint_amount = game_instance.current_hint_amount - 1
            emit("show cards", get_words_json(game_instance, "Operative"), room=f"{game_instance.room_code}/Operative")
            emit("show cards", get_words_json(game_instance, "Spymaster"), room=f"{game_instance.room_code}/Spymaster")
            db.database.session.commit()
            return True
    else:
        print(f"Malformed operative action from {session_cookie}")
    return False


@socketio.on("performed spymaster action")
def performed_spymaster_action_socket(data):
    session_cookie = request.cookies.get("session")
    game_session = db.GameSession.query.filter_by(game_id=session["game_session_ids"][0],
                                                  session_id=session["game_session_ids"][1]).first()
    game_instance = game_session.game
    role_name = db.Role.query.filter_by(role_id=game_instance.current_team_role).first().role_name
    if "hint" in data and "amount" in data and game_session.team == game_instance.current_team and role_name == "Spymaster":
        spymaster_data = {"hint": data["hint"], "amount": data["amount"]}
        emit("show spymaster hint", spymaster_data, room=f"{game_session.game.room_code}")
        game_session.game.current_team_role = db.Role.query.filter_by(role_name="Operative").first().role_id
        game_session.game.current_hint_amount = int(data["amount"]) + 1
        db.database.session.commit()
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
        emit("show toast", {"title": "Player disconnected", "message": f"Oh no! {game_session.user_name} left the room", "icon:": "bi-exclamation-octagon-fill"}, room=game_session.game.room_code)
        if game_session.role_id is not None and game_session.team is not None:
            role_room = game_session.role.role_name
            leave_room(f"{game_session.game.room_code}/{role_room}")
            leave_room(f"{game_session.game.room_code}/{role_room}/{game_session.team}")
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
            emit("show toast", {"title": "New admin", "message": f"Player {new_admin.user_name} is the new admin", "icon": "bi-info-square-fill"}, room=game_session.game.room_code)
            db.database.session.merge(new_admin)
        emit("show players", get_users_json(game_session), room=game_session.game.room_code)
        leave_room(game_session.game.room_code)
        db.database.session.merge(game_session)
        db.database.session.commit()


if __name__ == "__main__":
    socketio.run(app, host='kodenavne-dev', port=5000)
