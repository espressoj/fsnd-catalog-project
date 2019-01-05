from flask import Flask, render_template, jsonify, redirect, url_for, request, json, flash

from sqlalchemy import create_engine, literal
from sqlalchemy.orm import sessionmaker, join
from models import Base, User, Items, Categories, ItemCategories, ItemPhotos, ItemTags, Inventory


app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# This page will show the home page for non-logged-in users.
@app.route('/')
@app.route('/catalog/')
def showCatsAndItems():
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the latest 6 items
    """MOST RECENT 5"""
    latestItems = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhotos.photoUrl).join(ItemPhotos).limit(5).all()
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    """ADD RANDOM IMAGES"""
    return render_template('home_notLoggedIn.html', categories=categories, latestItems=latestItems, tagCloud=tagCloud)

# This page will display all items of a selected category for a non-logged-in user.
@app.route('/catalog/<categoryName>/')
def showCategoryItems(categoryName):
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the latest 6 items
    categoryItems = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhotos.photoUrl, ItemCategories.categoryId, Categories.categoryName).join(ItemPhotos).join(ItemCategories).join(Categories).filter_by(categoryName=categoryName.title()).all()
    # print(categoryItems)
    # Display the number of records found
    if len(categoryItems) == 0:
        countMessage = "No items were found in this category."
    else:
        countMessage = "%s items found." % len(categoryItems)
    # FOR DUEBUG - Print the object in the console
    # for i in categoryItems:
    #     print("ItemID: %s" % i[0])
    #     print("ItemUrl: %s" % i[1])
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    """ADD RANDOM IMAGES"""
    return render_template('categoryItems_notLoggedIn.html', categories=categories, categoryItems=categoryItems, catName=categoryName, tagCloud=tagCloud, countMessage=countMessage)

# This page will display all items of a with the selected tag for a non-logged-in user.
@app.route('/catalog/tags/<tag>/')
def showTaggedItems(tag):
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the items with the supplied tag
    taggedItems = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhotos.photoUrl, ItemTags.tag).join(ItemPhotos).join(ItemTags).filter_by(tag=tag).all()
    # FOR DUEBUG - Print the object in the console
    # print(taggedItems)
    # Display a count of the number of records found
    if len(taggedItems) == 0:
        countMessage = "No items were found."
    else:
        countMessage = "%s items found." % len(taggedItems)
    # FOR DUEBUG - Print the object in the console
    # for i in taggedItems:
    #     print("ItemID: %s" % i[0])
    #     print("ItemUrl: %s" % i[1])
    # Query the top 30 tags
    tagCloud = session.query(ItemTags).limit(30).all()
    """ADD RANDOM IMAGES"""
    return render_template('taggedItems_notLoggedIn.html', categories=categories, taggedItems=taggedItems, tagCloud=tagCloud, tagName=tag, countMessage=countMessage)

# This page will show the full item details for a non-logged-in user.
@app.route('/catalog/items/<int:itemId>')
def showItemDetails(itemId):
    # Query all of the categories
    categories = session.query(Categories).order_by("categoryName").all()
    # Query the specific item based on itemId
    #item = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhotos.photoUrl, Inventory.itemPrice, Inventory.inventoryCount).join(ItemPhotos).join(Inventory).filter_by(itemId=int(itemId)).all()
    item = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhotos.photoUrl, Inventory.itemPrice, Inventory.inventoryCount).outerjoin(ItemPhotos).outerjoin(Inventory).filter(Items.itemId==int(itemId)).first()
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
    """ADD RANDOM IMAGES"""
    return render_template('item_notLoggedIn.html', categories=categories, tagCloud=tagCloud, itemDisplay=display, item=item, countMessageClass=countMessageClass, countMessage=countMessage)


# This page will display the search results for a non-logged-in user.
@app.route('/search', methods=['GET'])
def search_results():
    results = []
    search_string = search.data['search']
    """GET SEARCH FEATURE WORKING"""
    if search_string:

        # searchedItems = session.query(Items.itemId, Items.itemName, Items.itemDescription, ItemPhoto.photoUrl, ItemTags.tag).join(ItemPhotos).join(ItemTags).filter(Items.itemName.contains(search_string)).all()
        # .filter(Items.itemName.like(%search_string%) | Items.itemDescription.like(%search_string%) )
        #, literal(search_string).contains(ItemTags.tag))).all()
        results = searchedItems.all()
    else:
        qry = db_session.query(Album)
        results = qry.all()

    if not results:
        flash('No results found!')
        return redirect('/')
    else:
        # display results
        table = Results(results)
        table.border = True
        return render_template('results.html', table=table)

# "This page will show a form for adding a new restaurant."
# Create the route and include both the POST and GET methods
@app.route('/catalog/addItem', methods=['GET','POST'])
def newRestaurant():
    # POST methods actions
    if request.method == 'POST':
        # Set the name of the new restaurant into the dictionary
        new_restaurant = Restaurant(name=request.form['restaurant_name'])
        # Add it to the session
        session.add(new_restaurant)
        # Commit the addition to the database
        session.commit()
        # Send the Flash Message - Restaurant added.
        flash("Your new item has been added!", "success")
        # Redirect the user back to the main Restaurants page
        return redirect(url_for('showRestaurants'))
    # GET method actions
    else:
        # Display the Add New Restaurant form page
        return render_template('newRestaurant.html')

# "This page will show a form to edit a restaurant."
# Create the route and include both the POST and GET methods
@app.route('/catalog/<int:itemId>/edit', methods=['GET','POST'])
# Create the function for editing a restaurant
def editRestaurant(itemId):
    # Query the DB for the specific restaurant information
    update_restaurant = session.query(Restaurant).filter_by(
        id=restaurant_id).one()
    # POST method actions
    if request.method == 'POST':
        # Check existance of form field and then set the parameter(s) to update
        if request.form['restaurant_name']:
            update_restaurant.name = request.form['restaurant_name']
            # Add the change to the session
            session.add(update_restaurant)
            # Commit the change to the DB
            session.commit()
            # Send the Flash Message - Restaurant updated.
            flash("The restaurant has been updated!", "success")
        # Redirect the user back to the Restaurant List (main page)
        return redirect( url_for('showRestaurants') )
    # GET method actions
    else:
        # Render the editRestaurant template which includes the update form.
        return render_template('editRestaurant.html',
            restaurant_id=str(restaurant_id), restaurant=update_restaurant.name)

# This page will show/process a form to delete a restaurant.
# Create the route and include both the POST and GET methods
@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET','POST'])
# Create the function for deleting a restaurant
def deleteRestaurant(restaurant_id):
    # POST method actions
    if request.method == 'POST':
        """ Use the query parameter *restaurant_id* to get the correct
        restaurant to delete """
        delete_restaurant = session.query(Restaurant).filter_by(
            id = int(restaurant_id)
        ).one()
        # Add the change to the session
        session.delete(delete_restaurant)
        # Commit the delete to the database
        session.commit()
        # Send the Flash Message - Restaurant deleted.
        flash("Restaurant has been successfully deleted!", "deleteSuccess")
        # Redirect back to the restaurant list (main page)
        return redirect(url_for('showRestaurants'))
    #GET method actions
    else:
        # Query the database for the specific restaurant
        rest = session.query(Restaurant).filter_by(id=restaurant_id).one()
        # Render the confirmation page before deleting
        return render_template('deleteRestaurant.html',
            restaurant_id=restaurant_id, restaurant=rest)

#return "This page will show the entire menu for a restaurant."
# Create the route and include only the GET method (default)
@app.route('/catalog/<categoryName>')
@app.route('/restaurants/<int:restaurant_id>/menu')
# Create the function for displaying a restaurant's menu
def showMenu(restaurant_id):
    # Query the database for the specific restaurant information
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    # Query the database for the menu items associated with that restaurant
    items = session.query(MenuItem).filter_by(restaurant_id=
    restaurant.id).order_by("course", "name")
    # Render the menu page sending the restaurant and menu information
    return render_template('menu.html', restaurant_id=restaurant_id,
    restaurant=restaurant, items=items)

# This page will show a form to add a menu item.
# Create the route and include both the POST and GET methods
@app.route('/restaurants/<int:restaurant_id>/menu/new', methods=['GET','POST'])
# Create the function to add a new menu item
def newMenuItem(restaurant_id):
    # POST method actions
    if request.method == 'POST':
        # Create a new instance of the MenuItem class
        new_menu_item = MenuItem()
        # Set the restaurant_id
        new_menu_item.restaurant_id = restaurant_id
        """ Check to see if the form fields are completed and add to the
        session as necessary """
        if request.form['itemname']:
            new_menu_item.name = request.form['itemname']
        if request.form['itemcourse']:
            new_menu_item.course = request.form['itemcourse']
        if request.form['itemdesc']:
            new_menu_item.description = request.form['itemdesc']
        if request.form['itemcost']:
            new_menu_item.price = request.form['itemcost']
        # Add the form data to the session for a new menu item
        session.add(new_menu_item)
        # Commit the addition to the database
        session.commit()
        # Send the Flash Message - Menu item added.
        flash("The new menu item has been successfully added!", "success")
        # Redirect the user back to the restaurant menu
        return redirect( url_for('showMenu', restaurant_id=restaurant_id) )
    else:
        # Query the database for the specific restaurant information
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        return render_template('newMenuItem.html', restaurant_id=restaurant_id,
        restaurant=restaurant.name)

# This page will show a form to edit a menu item.
# Create the route and include only both the GET and POST methods
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit',
methods=['GET','POST'])
# Create the function to edit an existing menu item for an existing restaurant
def editMenuItem(restaurant_id, menu_id):
    # POST method actions
    if request.method == 'POST':
        # Set the update_menu_item variable with a db query for the record
        update_menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
        # Check existance of form field and then set the parameter(s) to update
        if request.form['itemname']:
            update_menu_item.name = request.form['itemname']
        if request.form['itemcourse']:
            update_menu_item.course = request.form['itemcourse']
        if request.form['itemcost']:
            update_menu_item.price = request.form['itemcost']
        if request.form['itemdesc']:
            update_menu_item.description = request.form['itemdesc']
            # Add the change to the session
            session.add(update_menu_item)
            # Commit the change to the DB
            session.commit()
            # Send the Flash Message - Menu item updated.
            flash("The menu item successfully updated!", "success")
        # Redirect the user back to the Restaurant List (main page)
        return redirect( url_for('showMenu', restaurant_id=restaurant_id) )
    # GET method actions
    else:
        # Query the database for the restaurant information
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        # Query the database for the menu item information
        menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
        # Render the editMenuItem page with the prefilled form (placeholders)
        return render_template('editMenuItem.html',
            restaurant_id=restaurant_id, restaurant=restaurant.name,
            item=menu_item)

# This page will show a form to delete a menu item.
# Create the route and include only both the GET and POST methods
@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete'
    , methods=['GET','POST'])
# Create the function to delete an existing menu item for an existing restaurant
def deleteMenuItem(restaurant_id, menu_id):
    # POST method actions
    if request.method == 'POST':
        """ Use the query parameters *restaurant_id* and *menu_id* to get the
        correct restaurant's menu item to delete """
        delete_menu_item = session.query(MenuItem).filter_by(id = int(menu_id)
            , restaurant_id=int(restaurant_id)
        ).one()
        # Add the change to the session
        session.delete(delete_menu_item)
        # Commit the delete to the database
        session.commit()
        # Send the Flash Message - Menu item deleted.
        flash("The menu item has been successfully deleted!", "deleteSuccess")
        # Redirect back to the restaurant list (main page)
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    # GET method actions
    else:
        # Query the database for the restaurant information
        restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
        # Query the database for the menu item information
        menu_item = session.query(MenuItem).filter_by(id=menu_id).one()
        # Render the confirmation page before deleting the item
        return render_template('deleteMenuItem.html'
            , restaurant_id=restaurant_id, restaurant=restaurant.name,
            item=menu_item)

@app.route('/restaurants/data/JSON')
def showRestaurantsJSON():
    # This page will show all restaurants in JSON format.
    restaurant = session.query(Restaurant).all()
    return jsonify(Restaurants=[i.serialize for i in restaurant])

@app.route('/restaurants/<int:restaurant_id>/data/JSON')
def showRestaurantMenuJSON(restaurant_id):
    # This page will show a restaurant menu in JSON format.
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/data/JSON')
def showRestaurantMenuItemJSON(restaurant_id, menu_id):
    # This page will show a single restaurant menu item in JSON format.
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(restaurant_id=restaurant_id,
    id=menu_id).one()
    return jsonify(item.serialize)



if __name__ == '__main__':
    app.secret_key = 'dja90d8fa0sdnfasidpfaksjfd9s8ad'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
