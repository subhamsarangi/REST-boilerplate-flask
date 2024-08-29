from app import create_app, socketio

app = create_app(config_class='development')

from app.models import *

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8000)
