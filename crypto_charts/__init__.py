import os
import secrets

from flask import Flask


def create_app(test_config=None):
    """Create and configure the app"""
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = secrets.token_urlsafe((32))

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import coins
    app.register_blueprint(coins.bp)
    app.add_url_rule('/', endpoint='index')
    return app
