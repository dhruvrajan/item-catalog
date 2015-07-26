from flask import Flask, render_template, request, redirect, url_for, flash, \
    jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine("sqlite:///item-catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


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
