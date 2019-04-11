import os
from flask import Flask, session, redirect, request, url_for, jsonify, render_template, render_template_string
from requests_oauthlib import OAuth2Session

from pony.flask import Pony

import roxbot
from roxbot.db import db

OAUTH2_CLIENT_ID = roxbot.config["webapp"]['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = roxbot.config["webapp"]['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__)
Pony(app)
app.debug = True
app.use_reloader=False
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
app.config['TEMPLATES_AUTO_RELOAD'] = False


if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route("/")
def index():
    if session.get('oauth2_token') is None:
        return render_template_string("""<a href="{{ url_for(".login") }}">Login</a>""")
    else:
        return render_template_string("""<a href="{{ url_for(".logout") }}">logout</a>""")


@app.route('/login')
def login():
    scope = request.args.get(
        'scope',
        'identify guilds')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for(".index"))


@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.me'))


@app.route('/me')
def me():
    if session.get('oauth2_token') is None:
        return redirect(url_for("index"))
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    return db.Users.get(id=user["id"]).pronouns


if __name__ == '__main__':
    app.run()
