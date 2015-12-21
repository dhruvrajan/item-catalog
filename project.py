from flask import Flask, render_template, request, redirect, url_for, flash, \
    jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open("client_secrets.json", "r").read())["web"]["client_id"]

engine = create_engine("sqlite:///item-catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    print(state)
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get("state") != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        print("++++Invalid State Parameter: 401++++++")
        print("Request:", request.args.get(bytes("state", "utf-8")), "Session:", login_session["state"])
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    print(type(code), code)

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='https://www.googleapis.com/auth/calendar')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError, e:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        print("++++++++Failed to upgrade the authorization code: 401++++++")
        print(e.message)
        response.headers['Content-Type'] = 'application/json'
        return response


    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        print("++++++ERROR: 500+++++")
        response.headers['Content-Type'] = 'application/json'
        print("Failed at line #79")

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        print("++++++Token's user ID doesn't match given user ID: 401+++")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("+++++Token's client ID does not match app's: 401++++")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        print("+++++Current User is ALready connected: 200+++++++")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route("/")
@app.route("/catalog/")
def catalog():
    # Get List of Categories
    categories = session.query(Category).all()
    return render_template("catalog.html", categories=categories)


@app.route("/catalog/<int:category_id>/")
def category(category_id):
    # Get List of Items for a Category
    print(type(category_id))
    c = session.query(Category).filter(Category.id == category_id)[0]
    items = session.query(Item).filter(Item.category_id == category_id)
    return render_template("category.html", category=c, items=items)


@app.route("/catalog/<int:category_id>/new/", methods=["GET", "POST"])
def new_item(category_id):
    # Get List of Items for a Category
    category = session.query(Category).filter(Category.id == category_id)[0]
    if request.method == "POST":
        new_item = Item(
            name=request.form["name"],
            description=request.form["description"],
            price=request.form["price"],
            category=category
        )
        session.add(new_item)
        session.commit()
        return redirect(url_for("category", category_id=category_id))

    return render_template("add_item.html", category=category)


@app.route("/catalog/<int:category_id>/<int:item_id>/edit/",
           methods=["GET", "POST"])
def edit_item(category_id, item_id):
    # Get List of Items for a Category
    category = session.query(Category).filter(Category.id == category_id)[0]
    item = session.query(Item).filter(Item.id == item_id)[0]
    print("Item: ", item.name, item.description)
    if request.method == "POST":
        print("Request: ", request.form["name"], request.form["description"])
        print("@types: ", type(item.name), type(request.form["name"]))
        item.name = request.form["name"]
        item.description = request.form["description"]
        item.price = request.form["price"]
        item.category = category
        print("Doing Fine")
        return redirect(url_for("category", category_id=category_id))

    return render_template("edit_item.html", category=category, item=item)


@app.route("/catalog/<int:category_id>/<int:item_id>/delete/",
           methods=["GET", "POST"])
def delete_item(category_id, item_id):
    category = session.query(Category).filter(Category.id == category_id)[0]
    item = session.query(Item).filter(Item.id == item_id)[0]

    if request.method == "POST":
        session.query(Item).filter(Item.id == item_id).delete()
        session.commit()
        return redirect(url_for("category", category_id=category_id))

    return render_template("delete_item.html", category=category, item=item)


@app.route("/catalog/<int:category_id>/<int:item_id>/json/")
def item_json(category_id, item_id):
    item = session.query(Item).filter(Item.id == item_id)[0]
    return jsonify(items=[item.serialize, ])


@app.route("/catalog/<int:category_id>/json/")
def category_json(category_id):
    category = session.query(Category).filter(Category.id == category_id)[0]
    items = session.query(Item).filter(Item.category_id == category_id)
    return jsonify(items=[item.serialize for item in items], name=category.name,
                   id=category.id)


@app.route("/catalog/json/")
def catalog_json():
    categories = session.query(Category).all()
    return jsonify(
        categories=[{
                        "name": category.name,
                        "items": [item.serialize for item in
                                  session.query(Item).filter(
                                      Item.category_id == category.id)],
                        "id": category.id
                    }
                    for category in categories]
    )


if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
