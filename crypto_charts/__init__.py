import os
import secrets

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session


def create_app(test_config=None):
    """Create and configure the app"""
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = secrets.token_urlsafe((32))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SESSION_TYPE'] = 'sqlalchemy'

    db = SQLAlchemy(app)

    app.config['SESSION_SQLALCHEMY'] = db

    sess = Session(app)

    db.create_all()

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from crypto_charts import coins
    app.register_blueprint(coins.bp)
    app.add_url_rule('/', endpoint='index')
    return app
