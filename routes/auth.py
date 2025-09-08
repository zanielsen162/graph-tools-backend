from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask, redirect, render_template, session, url_for, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2 as psy
from psycopg2.extras import RealDictCursor

from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required, JWTManager, set_access_cookies, unset_jwt_cookies
from flask_cors import CORS

from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

import os
import json

from flask import Blueprint
from extensions import jwt, oauth
from services.db import authenticate, create_user_db, checking_user_exist


auth = Blueprint('auth', __name__)

# will sub with actual database once implemented

# Using an `after_request` callback, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
@auth.after_request
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

@auth.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True)
    )

@auth.route("/login_direct", methods=["POST"])
def login_direct():
    data = request.json
    input_id = data.get("username", None)
    input_password = data.get("password", None)
    user = None

    if not input_id or not input_password:
        return jsonify({'msg': 'Missing credentials', 'status': 400})

    auth_result = authenticate(input_id, input_password).get_json()
    if auth_result['status'] == 200:
        access_token = create_access_token(
            identity=auth_result['user']['id'],
            additional_claims=auth_result['user']
        )
        response = jsonify({'msg': 'Login successful', 'status': 200})
        set_access_cookies(response, access_token)
        return response

    return jsonify({'msg': 'Error signing in. Please check credentials.', 'status': 400})

@auth.route("/callback")
def callback():
    token = oauth.auth0.authorize_access_token()
    userInfo = token.get('userinfo')

    username=userInfo['nickname']
    userId=userInfo['sub']
    email=userInfo['email']

    row = checking_user_exist(username, email)

    if row:
        if not row['user_id'] == userId:
            return redirect(
                "https://" + os.getenv("AUTH0_DOMAIN")
                + "/v2/logout?"
                + urlencode({
                    "returnTo": 'http://localhost:3000/login?error=failed',
                    "client_id": os.getenv("AUTH0_CLIENT_ID"),
                }, quote_via=quote_plus)
            )
        
    creating_user_response = create_user_db(
        username=userInfo['nickname'],
        userId=userInfo['sub'],
        email=userInfo['email']
    )

    print(creating_user_response)

    access_token = create_access_token(identity=userInfo["sub"], additional_claims={"auth_source": "auth0"})
    response = redirect("http://localhost:3000/")
    set_access_cookies(response, access_token)
    return response

@auth.route("/logout", methods=["GET"])
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
        return jsonify({"msg": "Error during logout", "error": str(e)}), 500


@auth.route("/verify", methods=["GET"])
@jwt_required()
def verify():
    username = get_jwt_identity()
    auth_source = get_jwt()['auth_source']

    if auth_source == 'direct':
        username = get_jwt()['username']
        id = get_jwt()['id']
        email = get_jwt()['email']
        return jsonify(id=id, username=username, email=email, auth_source=auth_source)
    
    return jsonify(id=username, auth_source=auth_source)
    