from flask import Flask, render_template
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


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
