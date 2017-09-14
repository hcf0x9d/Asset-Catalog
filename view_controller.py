#!/usr/bin/python
import random
import string
import httplib2
import json
import requests

from functools import wraps
from flask import Flask, render_template, request
from flask import redirect, url_for, flash, make_response
from flask import session as login_session

from db_controller import DatabaseController


from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)
db = DatabaseController()


# =============================================================================
# AUTHENTICATION


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if login_session.get('user_id') is None:
            return redirect(url_for('show_login', next=request.url))

        return f(*args, **kwargs)

    return decorated_function


credentials = {}
token_info = {}

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def show_login():
    """Create an anti-forgery state token to assist security"""
    # state = create_session()['state']
    login_session['state'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    return render_template('login.html', STATE=login_session['state'])


# Connect and Disconnect endpoints.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Connect to the Google Plus API"""
    return check_authorization(request)


@app.route('/gdisconnect')
def gdisconnect():
    """Google Plus API disconnect/logout route"""
    return logout()


def check_client_auth(client_state):
    """Validate the client authentication params"""
    return client_state == login_session['state']


def check_authorization(client_request):
    """Verify the client can authorize on this application"""
    print('CHECKIT')
    if not check_client_auth(client_request.args.get('state')):
        # Nope, this is not allowed
        return json_response('Invalid authentication paramaters.', 401)
    else:
        request_data = client_request.data
        return try_oauth_upgrade(request_data)


def try_oauth_upgrade(request_data):
    """Attempt to upgrade to an OAuth access token"""
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        set_credentials(oauth_flow.step2_exchange(request_data))
        return validate_access()
    except FlowExchangeError:
        return json_response('Failed to upgrade the authorization code.', 401)


def validate_access():
    """Check the Google API to see if this is a valid request"""
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % credentials.access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        return json_response(result.get('error'), 500)
    else:
        set_token_info(result)
    return check_token_user_match()


def check_token_user_match():
    """Verify the two tokens match in order to verify user"""
    if token_info['user_id'] != credentials.id_token['sub']:
        return json_response('Token\'s user ID doesn\'t match given user ID.', 401)
    else:
        return check_token_status()


def check_token_status():
    """Verify the token is issued to the correct client"""
    if token_info['issued_to'] != CLIENT_ID:
        return json_response('Token\'s client ID does not match.', 401)
    else:
        return check_user_auth()


def check_user_auth():
    """See if the user is already authenticated in the system"""
    if login_session.get('credentials') is not None:
        if credentials.id_token['sub'] == login_session.get('gplus_id'):
            return json_response('Current user is already connected.', 200)
    else:
        return create_user_session()


def create_user_session():
    """Create a new user in the login_session"""
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    response = requests.get(url, params=params)
    data = response.json()
    login_session['logged_in'] = True
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = credentials.id_token['sub']
    login_session['name'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['user_id'] = db.read_user(login_session).id

    return json_response('User successfully connected.', 200)


def logout():
    if login_session.get('access_token')is None:
        return json_response('Current user not connected', 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session.get('access_token')
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['name']
        del login_session['picture']
        del login_session['email']
        del login_session['user_id']
        return redirect(url_for('render_categories'))
    else:
        return json_response('Failed to revoke token for given user.', 400)


def set_credentials(new_credential):
    """Store the new credential in the global"""
    global credentials
    credentials = new_credential


def set_token_info(token):
    """Set the token into the global"""
    global token_info
    token_info = token


def create_session():
    """Verify the session exists or make a new one"""
    if login_session.get('state') is None:
        login_session['state'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
        return login_session


def json_response(message, response_code):
    """Build a JSON output"""
    response = make_response(json.dumps(message), response_code)
    response.headers['Content-Type'] = 'application/json'
    return response

# =============================================================================


# Static Pages
@app.route('/')
@login_required
def render_categories():
    categories = db.read_category_list(login_session)
    return render_template('catalog.html',
                           categories=categories,
                           user_id=login_session.get('user_id'),
                           STATE=login_session.get('state'))


@app.route('/<string:category_slug>/')
@login_required
def render_category_items(category_slug):
    category = db.read_category(category_slug, login_session)
    categories = db.read_category_list(login_session)
    items = db.read_item_list(category.id, login_session)
    return render_template('category.html',
                           category=category,
                           categories=categories,
                           items=items,
                           user_id=login_session.get('user_id'),
                           STATE=login_session.get('state')
                           )


@app.route('/addItem', methods=['POST'])
def add_item_to_category():
    db.add_item(request.form, login_session.get('user_id'))
    flash('Added an Item to the DB')
    return json.dumps({'status': 'OK',
                       'user': login_session.get('user_id'),
                       'post': request.form})


@app.route('/<string:category_slug>/<string:item_slug>/')
@login_required
def render_item(category_slug, item_slug):
    categories = db.read_category_list(login_session)
    item = db.read_item(item_slug)

    print(item)
    return render_template('item.html',
                           categories=categories,
                           item=item,
                           # main_category=category_id,
                           # user_id=session.get('user_id'),
                           # STATE=session.get('state')
                           )
#
#
# @app.route('/')
# def catalog_view():
#     print('load')
#     print(login_session)
#
#     # # If the user hasn't authenticated, we will need to ask them to do so
#     if 'user' not in login_session:
#         return redirect('/login')
#
#     user_id = get_user_info(login_session['user']['email'])
#
#     if not user_id:
#         user_id = create_user(login_session)
#
#     login_session['user']['user_id'] = user_id
#     print(login_session['user']['email'])
#     return render_template('catalog.html')
#
#
# @app.route('/api/users/<int:id>')
# def get_user(id):
#     user = session.query(User).filter_by(id=id).one()
#     if not user:
#         abort(400)
#     return jsonify({'username': user.username})
#
#
# @app.route('/api/resource')
# @login_required
# def get_resource():
#     return jsonify({ 'data': 'Hello, %s!' % g.user.username })




# Let's get it started in here.
if __name__ == '__main__':

    app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
