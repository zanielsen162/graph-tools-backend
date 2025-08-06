from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask, redirect, render_template, session, url_for, request
from flask import jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
from flask_cors import CORS

from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

import os
import json


load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# If true this will only allow the cookies that contain your JWTs to be sent
# over https. In production, this should always be set to True
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_COOKIE_CSRF_PROTECT"] = True
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

jwt = JWTManager(app)
oauth = OAuth(app)

# will sub with actual database once implemented
users = {
    "testuser": {
        "password": generate_password_hash('password'),
        "name": "Test User",
        "email": "testuser@gmail.com"
    }
}

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

# Using an `after_request` callback, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
@app.after_request
def refresh_expiring_jwts(response):
    if request.endpoint == "logout":
        return response
        
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        claims = get_jwt()
        auth_source = claims.get("auth_source")  
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(
                identity=get_jwt_identity(),
                additional_claims={"auth_source": auth_source} if auth_source else None
            )
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/login_direct", methods=["POST"])
def login_direct():
    print("Login direct called")
    data = request.json
    username = data.get("username", None)
    password = data.get("password", None)

    if username in users and check_password_hash(users[username]["password"], password):
        response = jsonify({'msg': 'Login successful', 'status': 200})
        access_token = create_access_token(identity=username, additional_claims={"auth_source": "direct"})
        set_access_cookies(response, access_token)
        
        return response

    response = jsonify({'msg': 'Login failed', 'status': 401})
    return response

@app.route("/callback")
def callback():
    token = oauth.auth0.authorize_access_token()
    userInfo = token.get('userinfo')

    access_token = create_access_token(identity=userInfo["sub"], additional_claims={"auth_source": "auth0"})
    response = redirect("http://localhost:3000/")
    set_access_cookies(response, access_token)
    return response

@app.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    try:
        response = jsonify({"msg": "logout successful", "status": 200 })
        unset_jwt_cookies(response)

        auth_source = get_jwt()["auth_source"]

        if auth_source == "auth0":
            response = redirect(
                "https://" + os.getenv("AUTH0_DOMAIN")
                + "/v2/logout?"
                + urlencode({
                    "returnTo": 'http://localhost:3000/login',
                    "client_id": os.getenv("AUTH0_CLIENT_ID"),
                }, quote_via=quote_plus)
            )
            unset_jwt_cookies(response)

        return response
    except Exception as e:
        print(e)
        return jsonify({"msg": "Error during logout", "error": str(e)}), 500


@app.route("/verify", methods=["GET"])
@jwt_required()
def verify():
    username = get_jwt_identity()
    auth_source = get_jwt()['auth_source']
    return jsonify(id=username, auth_source=auth_source)


if __name__ == "__main__":
    app.run()