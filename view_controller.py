#!/usr/bin/python
import random
import string
import httplib2
import json
import requests

from functools import wraps
from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, flash, make_response
from flask import session as login_session

from db_controller import DatabaseController

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(
    random.choice(string.ascii_uppercase + string.digits) for x in range(32))
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


token_info = {}

CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']


@app.route('/login')
def show_login():
    """Create an anti-forgery state token to assist security"""
    create_session()
    print(login_session)
    return render_template('login.html', STATE=login_session['state'])


# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    print('\nrequest args')
    print(request.args.get('state'))
    print('login session')
    print(login_session['state'])
    print('\n')
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['name'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = db.read_user(login_session)

    if not user_id.id:
        user_id = db.create_user(login_session)
    login_session['user_id'] = user_id.id

    output = '<h1>redirecting...</h1>'
    flash("you are now logged in as %s" % login_session['name'], 'success')
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Google Plus API disconnect/logout route"""
    return logout()


def logout():
    if login_session.get('access_token')is None:
        return json_response('Current user not connected', 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session.get('access_token')
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


def set_token_info(token):
    """Set the token into the global"""
    global token_info
    token_info = token


def create_session():
    """Verify the session exists or make a new one"""
    if login_session.get('state') is None:
        login_session['state'] = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(32))
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
    categories = db.read_category_list()
    return render_template('catalog.html',
                           categories=categories,
                           user_id=login_session.get('user_id'),
                           STATE=login_session.get('state'))


@app.route('/<string:category_slug>/')
@login_required
def render_category_items(category_slug):
    category = db.read_category(category_slug)
    categories = db.read_category_list()
    items = db.read_item_list(category.id)
    return render_template('category.html',
                           category=category,
                           categories=categories,
                           items=items,
                           user_id=login_session.get('user_id'),
                           STATE=login_session.get('state')
                           )


@app.route('/deleteItem', methods=['POST'])
@login_required
def delete_item_from_category():
    db.delete_item(request.form, login_session.get('user_id'))
    # flash('Added an Item to the DB')
    return json.dumps({'status': 'OK',
                       'user': login_session.get('user_id'),
                       'post': ''})


@app.route('/addItem', methods=['POST'])
@login_required
def add_item():
    db.add_item(request.form, login_session.get('user_id'))
    flash(u'Added a new item', u'success')
    return json.dumps({'status': 'OK',
                       'user': login_session.get('user_id'),
                       'post': request.form})


@app.route('/updateItem', methods=['POST'])
@login_required
def update_item():
    db.update_item(request.form, login_session.get('user_id'))
    flash(u'Item updated', u'success')
    return json.dumps({'status': 'OK',
                       'user': login_session.get('user_id'),
                       'post': request.form})


@app.route('/deleteCategory', methods=['POST'])
@login_required
def delete_category():
    db.delete_category(request.form, login_session.get('user_id'))
    return json.dumps({'status': 'OK'})


@app.route('/addCategory', methods=['POST'])
@login_required
def add_category():
    db.add_category(request.form, login_session.get('user_id'))
    flash(u'Added a new category', u'success')
    return json.dumps({'status': 'OK',
                       'user': login_session.get('user_id'),
                       'post': request.form})


@app.route('/<string:category_slug>/<string:item_slug>/')
@login_required
def render_item(category_slug, item_slug):

    categories = db.read_category_list()
    item = db.read_item(item_slug, category_slug)

    return render_template('item.html',
                           categories=categories,
                           item_category=item.Category,
                           item=item.Item,
                           # main_category=category_id,
                           user_id=login_session.get('user_id'),
                           # STATE=session.get('state')
                           )


@app.route('/api/<string:category_slug>/items', methods=['POST', 'GET'])
def api_get_items(category_slug):
    category = db.read_category(category_slug)
    items = db.read_item_list(category.id)
    return jsonify(status='OK', items=[item.serialize for item in items])


@app.route('/api/<string:category_slug>/<string:item_slug>',
           methods=['POST', 'GET'])
def api_get_item(category_slug, item_slug):
    items = db.read_item(item_slug, category_slug)
    return jsonify(status='OK', items=[item.serialize for item in items])

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
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
