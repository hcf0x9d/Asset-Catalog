#!/usr/bin/python

from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify, make_response
from flask import session as login_session
app = Flask(__name__)

import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials

import httplib2
import json
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def createUser(login_session):
    newUser = User(name=login_session['user'],
                   picture=login_session['picture'],
                   email=login_session['email'])

    session.add(newUser)
    session.commit()

    user = session.query(User).filter_by(email=login_session['email']).one()

    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        return None


# Login route and system
@app.route('/login')
def showLogin():
    """Create an anti-forgery state token and then load up the login
        template with the state token stored in session and sent to
        the template"""

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Connect to Google Plus API using a POST to get authentication
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Login to the application using Google's OAuth2 API"""

    # This is may be a hijacked session, kill the process for security
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameters'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    # Credentials not matching the oauth response, kill the process
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade code'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    access_token = credentials.access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # Some kind of server error, we are broken
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

        return response

    gplus_id = credentials.id_token['sub']

    # User doesn't have valid access to this application
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID does not match given ID"), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')

    # This user has already authenticated, pass them along like normal
    if stored_credentials is not None and gplus_id == stored_gplus_id:

        response = make_response(json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'

        return response

    # We need to store the credentials response as JSON otherwise, brokesauce
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    # Grab some user information and send it to the login_session object
    login_session['provider'] = 'google'
    login_session['user'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>' + login_session['user'] + '</h1>'
    flash('You are now logged in as ' + login_session['user'])
    return output


@app.route('/gdisconnect')
def gdisconnect():

    credentials = json.loads(login_session.get('credentials'))

    if credentials is None:
        print('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials['access_token']

    print('In gdisconnect access token is %s', access_token)
    print('User name is: ' + login_session['user'])
    print
    print(access_token)
    print
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    print('result is :: ')
    print(result)

    if result['status'] == '200':
        del json.loads(login_session['credentials'])['access_token']
        del login_session['gplus_id']
        del login_session['user']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':

            gdisconnect()
            del login_session['credentials']


@app.route('/')
def catalogView():

    # If the user hasn't authenticated, we will need to ask them to do so
    if 'user' not in login_session:
        return redirect('/login')

    user_id = getUserId(login_session['email'])

    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    print(login_session)

    return


# Add user id when creating an item or a category

# @app.route('/<str:catalog_name>/items')
# def itemList():

#     return

if __name__ == '__main__':

    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
