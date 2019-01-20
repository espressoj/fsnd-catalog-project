import json
import random
import string
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, text
from sqlalchemy.orm import sessionmaker, joinedload, relationship
import requests
from models import Base, User, Items, Categories, Inventory, ItemCategories, ItemTags, ItemPhotos
import datetime
from marshmallow import Schema, fields

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2


app = Flask(__name__)
# DEBUGGING - Echo the SQL
# app.config['SQLALCHEMY_ECHO'] = True
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "HomeBuilt! Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Set a current data parameter for future use in database records updates
currentDateTime = datetime.datetime.now()
# print(currentDateTime)

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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
    # Set some of the session information
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    userid = getUserID(data["email"])
    if userid is None:
        userid = createUser(login_session)

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # DEBUGGING
    # print('In gdisconnect access token is %s' % access_token)
    # print('User name is: %s' % login_session['username'])
    # print('Access Token is: %s' % login_session['access_token'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    # print('URL is: %s' % url)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print('result is %s' % result)
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # print (response)
        return redirect(url_for('home'))
    else:
        print('RESULT STATUS')
        # print(result)
        response = make_response(json.dumps('Process failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
    return response

# Method to check if email exists in database
def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        login_session['user_id'] = user.id
        return user.id
    except:
        return None

# Method to get a user's info
def getUserInfo(userid):
    user = session.query(User).filter_by(id = userid).one()
    return user

# Method to Create a new user
def createUser(login_session):
    new_user = User(name = login_session['username'], email =
        login_session['email'], username = login_session['email'],
        picture = login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    login_session['user_id'] = user.id
    return user.id


# This page will show the entire catalog for the any user
@app.route('/')
@app.route('/catalog/')
def home():
    if not login_session.get('access_token'):
        logged_in = False
    else:
        logged_in = True
    # print(logged_in)
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the latest 5 items
    """MOST RECENT 5"""
    latestItems = session.query(Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                ).join(ItemPhotos
                                ).limit(5
                                ).all()
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    # set the JSON link for the template page.
    json_link = "/catalog/JSON"
    return render_template('home_notLoggedIn.html', categories=categories, latestItems=latestItems
                            , tagCloud=tagCloud, logged_in=logged_in, json_link=json_link)

# JSON APIs to view full catalog
@app.route('/catalog/JSON')
def fullCatalogJSON():
    items = session.query(Items.itemId
                        , Items.itemName
                        , Items.itemDescription
                        , Inventory.itemPrice
                        , Inventory.inventoryCount
                        , Categories.categoryName
                        , ItemPhotos.photoUrl
                        ).outerjoin(Inventory, Items.itemId == Inventory.itemId
                        ).outerjoin(ItemCategories, Items.itemId == ItemCategories.itemId
                        ).outerjoin(Categories, ItemCategories.categoryId == Categories.categoryId
                        ).outerjoin(ItemPhotos, Items.itemId == ItemPhotos.itemId
                        ).all()
    allItems = []
    itemDict = {}
    # Serialize the query data
    for i in items:
        itemDict = {
            "item_id"       : i.itemId,
            "item_name"     : i.itemName,
            "item_desc"     : i.itemDescription,
            "item_price"    : i.itemPrice,
            "item_category" : i.categoryName,
            "item_photo"    : i.photoUrl,
        }
        allItems.append(itemDict)
    #print(allItems)
    return jsonify(catalogItems=allItems)


# This page will show the entire catalog for the logged in owner.
# Create the route and include only the GET method (default)
@app.route('/myCatalog')
# Create the function for displaying a restaurant's menu
def showMyItems():
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    ownerId = login_session["user_id"]
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the database for the specific restaurant information
    myItems = session.query(Items).filter_by(owner=ownerId).order_by("added").all()
    # set the JSON link for the template page.
    json_link = "/myCatalog/JSON"
    # Render the menu page sending the restaurant and menu information
    return render_template('myCatalogItems.html', ownerid=ownerId,
                            myItems=myItems, categories=categories, email=login_session['email'],
                            logged_in=logged_in, json_link=json_link)


# JSON APIs to view myCatalog items - based on user_id in session
@app.route('/myCatalog/JSON')
def myCatalogJSON():
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    ownerId = login_session["user_id"]
    items = session.query(Items.itemId
                        , Items.itemName
                        , Items.itemDescription
                        , Inventory.itemPrice
                        , Inventory.inventoryCount
                        , Categories.categoryName
                        , ItemPhotos.photoUrl
                        ).outerjoin(Inventory, Items.itemId == Inventory.itemId
                        ).outerjoin(ItemCategories, Items.itemId == ItemCategories.itemId
                        ).outerjoin(Categories, ItemCategories.categoryId == Categories.categoryId
                        ).outerjoin(ItemPhotos, Items.itemId == ItemPhotos.itemId
                        ).filter(Items.owner == ownerId
                        ).all()
    allItems = []
    itemDict = {}
    for i in items:
        itemDict = {
            "item_id"       : i.itemId,
            "item_name"     : i.itemName,
            "item_desc"     : i.itemDescription,
            "item_price"    : i.itemPrice,
            "item_category" : i.categoryName,
            "item_photo"    : i.photoUrl,
        }
        allItems.append(itemDict)
    print(allItems)
    return jsonify(myCatalogItems=allItems)


# This page will display all items of a selected category for a non-logged-in user.
@app.route('/catalog/<categoryName>/')
def showCategoryItems(categoryName):
    if not login_session.get('access_token'):
        logged_in = False
    else:
        logged_in = True
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the latest 6 items
    categoryItems = session.query(Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                , ItemCategories.categoryId
                                , Categories.categoryName
                                ).join(ItemPhotos
                                ).join(ItemCategories
                                ).join(Categories
                                ).filter_by(categoryName=categoryName.title()
                                ).all()
    # Display the number of records found
    if len(categoryItems) == 0:
        countMessage = "No items were found in this category."
    else:
        countMessage = "%s items found." % len(categoryItems)
    # FOR DUEBUG - Print the object in the console
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    """ADD RANDOM IMAGES"""
    json_link = "/catalog/%s/JSON" % categoryName
    return render_template('categoryItems_notLoggedIn.html', categories=categories
                            , categoryItems=categoryItems, catName=categoryName, tagCloud=tagCloud
                            , countMessage=countMessage, logged_in=logged_in, json_link=json_link)


# JSON APIs to view myCatalog items - based on user_id in session
@app.route('/catalog/<categoryName>/JSON')
def showCategoryItemsJSON(categoryName):
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    # Query the latest 6 items
    categoryItems = session.query(Items.itemId
                        , Items.itemName
                        , Items.itemDescription
                        , Inventory.itemPrice
                        , Inventory.inventoryCount
                        , Categories.categoryName
                        , ItemPhotos.photoUrl
                        ).outerjoin(Inventory, Items.itemId == Inventory.itemId
                        ).outerjoin(ItemCategories, Items.itemId == ItemCategories.itemId
                        ).outerjoin(ItemPhotos, Items.itemId == ItemPhotos.itemId
                        ).outerjoin(Categories, ItemCategories.categoryId == Categories.categoryId
                        ).filter_by(categoryName=categoryName.title()
                        ).all()
    allItems = []
    itemDict = {}
    for i in categoryItems:
        itemDict = {
            "item_id"       : i.itemId,
            "item_name"     : i.itemName,
            "item_desc"     : i.itemDescription,
            "item_price"    : i.itemPrice,
            "item_inventory": i.inventoryCount,
            "item_category" : i.categoryName,
            "item_photo"    : i.photoUrl,
        }
        allItems.append(itemDict)
    print(allItems)
    return jsonify(categoryItems=allItems)


# This page will display all items of a with the selected tag for a non-logged-in user.
@app.route('/catalog/tags/<tag>/')
def showTaggedItems(tag):
    if not login_session.get('access_token'):
        logged_in = False
    else:
        logged_in = True
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the items with the supplied tag
    taggedItems = session.query(Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                , ItemTags.tag
                                ).join(ItemPhotos
                                ).join(ItemTags
                                ).filter_by(tag=tag
                                ).all()
    # FOR DUEBUG - Print the object in the console
    # print(taggedItems)
    # Display a count of the number of records found
    if len(taggedItems) == 0:
        countMessage = "No items were found."
    else:
        countMessage = "%s items found." % len(taggedItems)
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    json_link = "/catalog/tags/%s/JSON" % tag
    return render_template('taggedItems_notLoggedIn.html', categories=categories
                            , taggedItems=taggedItems, tagCloud=tagCloud, tagName=tag
                            , countMessage=countMessage, logged_in=logged_in, json_link=json_link)


# JSON APIs to view myCatalog items - based on user_id in session
@app.route('/catalog/tags/<tag>/JSON')
def showTaggedItemsJSON(tag):
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    # Query the items with the supplied tag
    taggedItems = session.query(Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                , ItemTags.tag
                                ).join(ItemPhotos
                                ).join(ItemTags
                                ).filter_by(tag=tag
                                ).all()
    allItems = []
    itemDict = {}
    for i in taggedItems:
        itemDict = {
            "item_id"       : i.itemId,
            "item_name"     : i.itemName,
            "item_desc"     : i.itemDescription,
            "item_photo"    : i.photoUrl,
        }
        allItems.append(itemDict)
    print(allItems)
    return jsonify(categoryItems=allItems)

# This page will show the full item details for a non-logged-in user.
@app.route('/catalog/items/<int:itemId>')
def showItemDetails(itemId):
    if not login_session.get('access_token'):
        logged_in = False
    else:
        logged_in = True
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the specific item based on itemId
    item = session.query(Items.itemId
                        , Items.itemName
                        , Items.itemDescription
                        , ItemPhotos.photoUrl
                        , Inventory.itemPrice
                        , Inventory.inventoryCount
                        ).outerjoin(ItemPhotos
                        ).outerjoin(Inventory
                        ).filter(Items.itemId==int(itemId)
                        ).first()
    # FOR DUEBUG - Print the object in the console
    print(item)
    # Display a count of the number of records found
    if not item:
        countMessage = "Item not found."
        countMessageClass = "badge badge-warning"
        display = "none"
    else:
        countMessage = ""
        countMessageClass = ""
        display = "initial"
    # FOR DUEBUG - Print the object in the console
    # for i in taggedItems:
    #     print("ItemID: %s" % i[0])
    #     print("ItemUrl: %s" % i[1])
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    json_link = "/catalog/items/%s/JSON" % str(itemId)
    return render_template('item_notLoggedIn.html', categories=categories, tagCloud=tagCloud
                            , itemDisplay=display, item=item, countMessageClass=countMessageClass
                            , countMessage=countMessage, logged_in=logged_in, json_link=json_link)


# JSON APIs to view myCatalog items - based on user_id in session
@app.route('/catalog/items/<int:itemId>/JSON')
def itemDetailsJSON(itemId):
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    items = session.query(Items.itemId
                        , Items.itemName
                        , Items.itemDescription
                        , Inventory.itemPrice
                        , Inventory.inventoryCount
                        , Categories.categoryName
                        , ItemPhotos.photoUrl
                        ).outerjoin(Inventory, Items.itemId == Inventory.itemId
                        ).outerjoin(ItemCategories, Items.itemId == ItemCategories.itemId
                        ).outerjoin(Categories, ItemCategories.categoryId == Categories.categoryId
                        ).outerjoin(ItemPhotos, Items.itemId == ItemPhotos.itemId
                        ).filter(Items.itemId==int(itemId)
                        ).all()
    allItems = []
    itemDict = {}
    for i in items:
        itemDict = {
            "item_id"       : i.itemId,
            "item_name"     : i.itemName,
            "item_desc"     : i.itemDescription,
            "item_price"    : i.itemPrice,
            "item_category" : i.categoryName,
            "item_photo"    : i.photoUrl,
        }
        allItems.append(itemDict)
    print(allItems)
    return jsonify(ItemDetails=allItems)


# "This page will show a form for adding a new item to a personal catalog."
# Create the route and include both the POST and GET methods
@app.route('/catalog/addItem', methods=['GET','POST'])
def addCatalogItem():
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    ownerId = login_session["user_id"]
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # POST methods actions
    if request.method == 'POST':
        # Set the name of the new restaurant into the dictionary
        new_item = Items(itemName=request.form['item_name'],
                        itemDescription=request.form['item_description'],
                        owner=ownerId,
                        added=currentDateTime,
                        modified=currentDateTime,
                        status='A')
        # Add it to the session
        session.add(new_item)
        # Commit the addition to the database
        session.commit()
        # Send the Flash Message - Restaurant added.
        flash("Your new item has been added!", "success")
        addedItem = session.query(Items).order_by(Items.itemId.desc()).first()
        new_item_category = ItemCategories(categoryId=request.form['item_category'],
                                            itemId=addedItem.itemId)
        new_item_inventory = Inventory(itemId=addedItem.itemId,
                                        inventoryCount=request.form['item_inventory'],
                                        itemPrice=request.form['item_price'],
                                        lastUpdated=currentDateTime)
        session.add(new_item_category)
        session.add(new_item_inventory)
        session.commit()
        # Item Tags - Outside of scope of this project - Do later
        # Item Photo - Outside of scope of this project - Do later
        # Redirect the user back to the main Restaurants page
        return redirect(url_for('showMyItems'))
    # GET method actions
    else:
        # Display the Add New Restaurant form page
        return render_template('addItem_LoggedIn.html', categories=categories
                                , email=login_session['email'], logged_in=logged_in)

# Edit a restaurant
@app.route('/catalog/items/<int:itemId>/update/', methods=['GET', 'POST'])
def editItem(itemId):
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    editedItem = session.query(Items.owner
                                , Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                , Inventory.itemPrice
                                , ItemCategories.categoryId
                                , Inventory.inventoryCount
                                ).outerjoin(ItemCategories
                                ).outerjoin(ItemPhotos
                                ).outerjoin(Inventory
                                ).filter(Items.itemId==int(itemId)
                                ).filter(Items.owner==int(login_session['user_id'])
                                ).first()
    # If the user is not the owner of the restaurant record, redirect to home
    if editedItem.owner != login_session.get('user_id'):
        return redirect(url_for('showMyItems'))
    if request.method == 'POST':
        if request.form['item_name']:
            print(request.form['item_name'])
            itemToEdit = session.query(Items
                                        ).filter(Items.itemId==int(itemId)
                                        ).filter(Items.owner==int(login_session['user_id'])
                                        ).all()
            for i in itemToEdit:
                i.itemName = request.form['item_name']
                i.itemDescription = request.form['item_description']
            session.commit()
            itemCategory = session.query(ItemCategories
                                        ).filter(ItemCategories.itemId==int(itemId)
                                        ).all()
            for i in itemCategory:
                i.categoryId = request.form['item_category']
            session.commit()
            itemInventory = session.query(Inventory
                                        ).filter(Inventory.itemId==int(itemId)
                                        ).all()
            for i in itemInventory:
                i.inventoryCount = request.form['item_inventory']
                i.itemPrice = request.form['item_price']
                i.lastUpdated = currentDateTime
            session.commit()
            flash('Item Successfully Edited %s' % editedItem.itemName)
            return redirect(url_for('showMyItems'))
    else:
        return render_template('editItem_LoggedIn.html', categories=categories, item=editedItem
                                , logged_in=logged_in)

# Edit a restaurant
@app.route('/catalog/items/<int:itemId>/delete/', methods=['POST'])
def deleteItem(itemId):
    if not login_session.get('access_token'):
        return redirect('/')
    else:
        logged_in = True
    ownerId = login_session["user_id"]
    deleteItem = session.query(Items.owner
                                , Items.itemId
                                , Items.itemName
                                , Items.itemDescription
                                , ItemPhotos.photoUrl
                                , Inventory.itemPrice
                                , ItemCategories.categoryId
                                , Inventory.inventoryCount
                                ).outerjoin(ItemCategories
                                ).outerjoin(ItemPhotos
                                ).outerjoin(Inventory
                                ).filter(Items.itemId==int(itemId)
                                ).filter(Items.owner==int(ownerId)
                                ).first()
    # If the user is not the owner of the restaurant record, redirect to home
    if deleteItem.owner != login_session.get('user_id'):
        return redirect(url_for('showMyItems'))
    if request.method == 'POST':
        session.query(Items).filter(Items.itemId==int(itemId)).delete()
        session.commit()
        flash('Item Successfully Deleted %s' % deleteItem.itemName)
        return redirect(url_for('showMyItems'))
    else:
        return redirect(url_for('showMyItems'))


if __name__ == '__main__':
    app.secret_key = 'dja90d8fa0sdnfasidpfaksjfd9s8ad'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000) # , ssl_context=('cert.pem', 'key.pem')
