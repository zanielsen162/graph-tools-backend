from flask import Flask, request, url_for, session, redirect, render_template
from authlib.integrations.flask_client import OAuth
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'super-secret-key'

login_manager = LoginManager(app)

# should use a database in production
users = {
    'testuser': generate_password_hash('password')
}

class User(UserMixin):
    def __init__(self, id=None):
        self.id = id
    
    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    return User(id=user_id)

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id='PM9i6rUCSNbdJXoz26Dzy4mTj9epfou5',
    client_secret='CZXrq9NaIxcUcdX3scBDPvaUGGAwZdj1ElGJjp_vj6Xxn6CpKY_AZETOsvu2OYEK',
    api_base_url='https://dev-h0hfe6xbw838xquv.us.auth0.com',
    access_token_url='https://dev-h0hfe6xbw838xquv.us.auth0.com/oauth/token',
    authorize_url='https://dev-h0hfe6xbw838xquv.us.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    }
)

@app.route('/')
def index():
    error_message = session.pop('error', None)  # Gets the error from the session and removes it
    html_error = '<div style="color: red; text-align: center; margin-bottom: 20px; margin-top: 10px;">Invalid credentials</div>' if error_message else ''

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login Page</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }}

            form {{
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                width: 300px;
            }}

            h1 {{
                text-align: center;
                color: #333;
            }}

            label {{
                margin-bottom: 8px;
                display: block;
            }}

            input[type="text"], input[type="password"] {{
                width: 100%;
                padding: 10px;
                margin-bottom: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}

            input[type="submit"] {{
                background-color: #007BFF;
                color: #fff;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 10px;
            }}

            a {{
                display: block;
                text-align: center;
                margin-top: 10px;
                color: #007BFF;
                text-decoration: none;
            }}

            p {{
                text-align: center;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <form action="/login_direct" method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username">

            <label for="password">Password:</label>
            <input type="password" name="password" id="password">

            {html_error}

            <input type="submit" value="Login Directly">
            <p>OR</p>
            <a href="/login">Login via SSO</a>
        </form>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    return auth0.authorize_redirect(
        redirect_uri='http://localhost:5000/callback'
    )

@app.route('/callback')
def callback_handling():
    response = auth0.authorize_access_token()
    session['jwt_payload'] = response.json()
    user = User(
        user_id=session['jwt_payload']['sub']
    )
    user.id = session['jwt_payload']['sub']
    login_user(user)
    
    return redirect('/dashboard')

@app.route('/login_direct', methods=['POST'])
def login_direct():
    if check_password_hash(users.get(request.form['username'], ''), request.form['password']):
        user = User()
        user.id = request.form['username']
        login_user(user)
        return redirect('/dashboard')
    else:
        session['error'] = 'Invalid credentials, please try again.'
        return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return f'''
    <h1>Welcome to the Dashboard</h1>
    <p>You are logged in as: {current_user.id}</p>
    <a href="/logout">Logout</a>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)