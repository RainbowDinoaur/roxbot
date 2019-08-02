import os
from quart import Quart
import configparser

from pony.orm import Database, db_session, TransactionIntegrityError

db = Database()
db.bind(provider='postgres', user='roxie', password='', host='localhost', database='roxbot')
db.generate_mapping(create_tables=True)

print(db.entities)


config = configparser.ConfigParser()
config.read("../roxbot.conf")

app = Quart(__name__)


OAUTH2_CLIENT_ID = config["webapp"]['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = config["webapp"]['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
IMAGE_BASE_URL = "https://cdn.discordapp.com/"


app.debug = True
app.use_reloader=False
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
app.config['TEMPLATES_AUTO_RELOAD'] = False

from webapp import routes, oauth



