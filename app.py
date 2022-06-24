from flask import Flask, render_template, redirect, request
from flask_migrate import Migrate
from models import db

app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)

@app.route("/")
def index():
    """main page"""
    return render_template("index.html")

@app.route("/room/join", methods=['POST'])
def joinRedirect():
    return redirect("/room/"+ request.form['code'])

@app.route("/room/<roomID>")
def joinRoom(roomID):
    return render_template("roomnotfound.html")

if __name__ == "__main__":
    app.run(host='webeng-project-dhbw', port=5000)
