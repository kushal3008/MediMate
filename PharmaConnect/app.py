from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,template_folder='templates',static_folder='static',static_url_path="/")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testdb.db'
    app.secret_key = '2c64363168c162cdec670ff10b8eab35'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models import Chemist,Doctor
        from flask import session
        user_type = session.get('user_type')

        if user_type == "chemist":
            return Chemist.query.get(int(user_id))
        elif user_type == "doctor":
            return Doctor.query.get(int(user_id))
        else:
            return None

    migrate = Migrate(app,db)
    bcrypt = Bcrypt(app)

    from routes import register_routes

    register_routes(app,db,bcrypt)

    return app