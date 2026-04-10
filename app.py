import atexit

from flask import Flask

from config import Config
from routes.auth import auth_bp
from routes.notes import notes_bp
from routes.other import other_bp
from routes.tasks import tasks_bp
import models



app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(other_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(tasks_bp)

def close_db_connection():
    models.close_shared_connection()


atexit.register(close_db_connection)

if __name__ == '__main__':
    app.run(debug=False, port=5000, use_reloader=False)