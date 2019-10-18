from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup_final import Category, Base, Item, User
from flask import session as login_session
import random
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import string
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "project_final"


#engine = create_engine('sqlite:///category.db'
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token


@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print ("access token received %s ") % access_token
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open(
            'fb_client_secrets.json', 'r').read(
                ))['web']['app_secret']
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the 
        server token exchange we have to
        split the token first on commas and select the first index which 
        gives us the key : value
        for the server access token then we split it on
        colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used 
        directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    "url = 'https://graph.facebook.com/v2.8\n"
    "/me/picture?access_token=%s&redirect\n"
    "=0&height=200&width=200' % token"
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;height: 300px;border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output
    

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps(
            'Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            '/var/www/catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps(
                'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if result['status'] == '200':
        response = make_response(
            json.dumps(
                'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
def showmainpage():
    categories = session.query(Category.cname).all()
    items = session.query(
        Category.cname, Item.iname).filter(
            Item.category_id == Category.id).all()
    return render_template(
        'showmainpage.html', categories=categories, items=items)


@app.route('/categorys/<string:category_name>/items')
def categoryitem(category_name):
    categories = session.query(Category.cname).all()
    category = session.query(
        Category).filter(
            category_name == Category.cname).all()
    items = session.query(Item).all()
    return render_template(
        'categoryitem.html', 
        category_name=category_name, 
        category=category, items=items, categories=categories)


@app.route('/categorys/<string:category_name>/<string:item_name>')
def discription(category_name, item_name):
    items = session.query(Item).filter_by(iname=item_name)
    return render_template(
        'discription.html', items=items, 
        category_name=category_name, item_name=item_name)


@app.route(
    '/categorys/<string:category_name>/<string:items_name>/descriptions/')
def discriptionlog(category_name, items_name):
    items = session.query(Item).filter_by(iname=items_name)
    return render_template('discriptionedit.html', items=items)


@app.route('/add/')
def mainpagelogin():
    categories = session.query(Category.cname).all()
    items = session.query(Category.cname, Item.iname).filter(
        Item.category_id == Category.id).all()
    return render_template(
        'mainpagelogin.html', categories=categories, items=items)

 
@app.route('/categorys/<string:category_name>/<string:items_name>/edit',
           methods=['GET', 'POST'])
def edititems(category_name, items_name):
    if 'username' not in login_session:
        return redirect('/login')
    items = session.query(Item).all()
    editeditems = session.query(Item).filter(
        items_name == Item.iname).one()
    if Category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You\
            are not authorized to edit this item.\
            Please create your own item in order\
            to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        category1 = request.form['categories_select']
        real_id = session.query(
            Category.id).filter(Category.cname == category1).one() 
        Real_id = convert(real_id) 
        if request.form['name']:
            editeditems.iname = request.form['name']
        if request.form['description']:
            editeditems.description = request.form['description']
        if request.form['categories_select']:
            editeditems.category_id = Real_id
        session.add(editeditems)
        session.commit()
        return redirect(url_for('mainpagelogin'))
    else:
        return render_template(
            'edititem.html', category_name=category_name, 
            items_name=items_name,
            item=editeditems, items=items)


@app.route('/categorys/NewItem', methods=['GET', 'POST'])
def newMenuItem():
    if 'username' not in login_session:
        return redirect('/login')
    
    if request.method == 'POST':
        category1 = request.form['categories_select']
        real_id = session.query(
            Category.id).filter(Category.cname == category1).one() 
        Real_id = convert(real_id)
        NewItem = Item(iname=request.form['name'], description=request.form[
            'description'], category_id=Real_id)
        session.add(NewItem)
        session.commit()
        return redirect(url_for('mainpagelogin'))
    else:
        return render_template('addnewitem.html')


def convert(list):  
    s = [str(i) for i in list]  
    res = int("".join(s)) 
    return(res)


@app.route(
    '/categorys/<string:category_name>/<string:items_name>/delete', 
    methods=['GET', 'POST'])
def deletitems(category_name, items_name):
    if 'username' not in login_session:
        return redirect('/login')
    itemdelete = session.query(Item).filter_by(iname=items_name).one()
    if Category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You\
            are not authorized to edit this item.\
            Please create your own item in order\
            to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemdelete)
        session.commit()
        return redirect(url_for('mainpagelogin'))
    else:
        return render_template(
                'deleteitem.html', category_name=category_name, 
                items_name=items_name, name=itemdelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('mainpagelogin'))
    else:
        flash("You were not logged in")
        return redirect(url_for('mainpagelogin'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
