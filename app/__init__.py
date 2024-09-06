import traceback
from celery import Celery
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from graphene_file_upload.flask import FileUploadGraphQLView

from settings.config import app_config


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt()
celery = Celery(__name__)
jwt = JWTManager()
socketio = SocketIO()
mongo = PyMongo()

def make_celery(app):
    # Update Celery configuration
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        accept_content=app.config['CELERY_ACCEPT_CONTENT'],
        task_serializer=app.config['CELERY_TASK_SERIALIZER'],
        result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
        timezone=app.config['CELERY_TIMEZONE']
    )
    celery.autodiscover_tasks(['app.tasks'])
    return celery

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(app_config[config_class])
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="http://127.0.0.1:5500")
    CORS(app, origins=["http://127.0.0.1:5500"])
    
    mongo.init_app(app)
    make_celery(app)

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        if app.config['DEVELOPMENT']:
            app.logger.error("An error occurred: %s\n%s", str(e), traceback.format_exc())
        from app.exceptions import handle_exception
        return handle_exception(e)
    
    @app.route('/')
    def index():
        from app.tasks import article_task
        task = article_task.delay(123)
        socketio.emit('message', {'data': f"Task {task.id} has started."})
        return f"FLOG: welcome to my blog. Task {task.id}"
    

    from app.auth.routes import auth_bp
    from app.article.routes import article_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(article_bp, url_prefix='/api/articles')

    from app.auth.schema import schema
    app.add_url_rule(
    '/graphql/auth',
    view_func=FileUploadGraphQLView.as_view(
        'graphql', schema=schema, graphiql=True
    )
)

    return app
