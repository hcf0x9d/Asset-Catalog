import json
import random
import string

import httplib2
import requests
from flask import Flask, url_for, session, redirect, request
from flask import make_response
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets

from db_controller import DatabaseController

app = Flask(__name__)


db = DatabaseController()
credentials = {}
token_info = {}

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


# Connect and Disconnect endpoints.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    print('run gconnect')
    return check_authorization(request)


@app.route('/gdisconnect')
def gdisconnect():
    return logout()


# oAuth Flow and Error Checking
def check_client_auth(client_state):
    return client_state == session['state']


def check_authorization(client_request):
    print('run check authorization')
    if not check_client_auth(client_request.args.get('state')):
        return json_response('Invalid authentication paramaters.', 401)
    else:
        request_data = client_request.data
        return try_oauth_upgrade(request_data)


def try_oauth_upgrade(request_data):
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        set_credentials(oauth_flow.step2_exchange(request_data))
        return validate_access()
    except FlowExchangeError:
        return json_response('Failed to upgrade the authorization code.', 401)


def validate_access():
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % credentials['access_token'])
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        return json_response(result.get('error'), 500)
    else:
        set_token_info(result)
    return check_token_user_match()


def check_token_user_match():
    if token_info['user_id'] != credentials['id_token']['sub']:
        return json_response('Token\'s user ID doesn\'t match given user ID.', 401)
    else:
        return check_token_status()


def check_token_status():
    if token_info['issued_to'] != CLIENT_ID:
        return json_response('Token\'s client ID does not match.', 401)
    else:
        return check_user_auth()


def check_user_auth():
    if session.get('credentials') is not None:
        if credentials['id_token']['sub'] == session.get('gplus_id'):
            return json_response('Current user is already connected.', 200)
    else:
        return create_user_session()


def create_user_session():
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials['access_token'], 'alt': 'json'}
    response = requests.get(url, params=params)
    data = response.json()
    session['access_token'] = credentials['access_token']
    session['gplus_id'] = credentials['id_token']['sub']
    session['name'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']
    session['user_id'] = db.read_user(session).id
    print(session.get('access_token'))
    return json_response('User successfully connected.', 200)


def logout():
    if session.get('access_token')is None:
        return json_response('Current user not connected', 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % session.get('access_token')
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del session['access_token']
        del session['gplus_id']
        del session['name']
        del session['picture']
        del session['email']
        del session['user_id']
        return redirect(url_for('render_categories'))
    else:
        return json_response('Failed to revoke token for given user.', 400)


# Setters for global variables
def set_credentials(new_credential):
    global credentials
    credentials = new_credential


def set_token_info(token):
    global token_info
    token_info = token


def create_session():
    if session.get('state') is None:
        session['state'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
        return session

    return session


def json_response(message, response_code):
    response = make_response(json.dumps(message), response_code)
    response.headers['Content-Type'] = 'application/json'
    return response
