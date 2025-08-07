from flask import Flask
from auth.routes import auth
from database.routes import dbr

from flask import Flask, redirect, render_template, session, url_for, request, jsonify
from flask_cors import CORS

from dotenv import load_dotenv
import os
import json

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from extensions import jwt, oauth

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

    jwt.init_app(app)
    oauth.init_app(app)
    
    oauth.register(
        "auth0",
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        api_base_url=f'https://{os.getenv("AUTH0_DOMAIN")}',
        access_token_url=f'https://{os.getenv("AUTH0_DOMAIN")}/oauth/token',
        authorize_url=f'https://{os.getenv("AUTH0_DOMAIN")}/authorize',
        server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration',
        client_kwargs={
            "scope": "openid profile email",
        },
    )

    app.register_blueprint(auth)
    app.register_blueprint(dbr)


    return app

create_app().run()