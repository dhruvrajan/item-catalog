__author__ = 'dhruv'

import sqlalchemy
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item


class CatalogAccess:
    def __init__(self):
        engine = create_engine("sqlite:///itemcatalog.db")
        Base.metadata.bind = engine
        Session = sessionmaker()
        Session.configure(bind=engine)
        self.session = Session()

    def get_categories(self):
        """ Returns a list of Category objects
        """
        print("Getting Categories")
        return self.session.query(Category).all()

    def get_restaurant_by_id(self, id):
        print("Getting %d" % id)
        return self.session.query(Category).filter(Category.id == id)[0]

    def edit_restaurant(self, id, name):
        """Edit the name of a restaurant given its id
        """
        print("Editing Restaurant: ", id, name)
        self.session.query(Category).filter(Category.id == id). \
            update({Restaurant.name: name})
        self.session.commit()

    def add_restaurant(self, name):
        """Add Restaurant to the Database"""
        print("Adding Restaurant", name)
        self.session.add(Restaurant(name=name))
        self.session.commit()

    def delete_restaurant(self, id):
        """Delete Restaurant from Database"""
        print("Deleting Restaurant.")
        self.session.query(Restaurant).filter(Restaurant.id == id).delete()
        self.session.commit()

    def add_menu_item(self, item):
        """Adds a menu item to the databases
        :param item: a new MenuItem
        """
        self.session.add(item)
        self.session.commit()

    def get_menu_items(self, restaurant_id):
        return self.session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)

    def get_menu_item_by_id(self, menu_id):
        return self.session.query(MenuItem).filter(MenuItem.id == menu_id)[0]

    def delete_menu_item(self, menu_id):
        self.session.query(MenuItem).filter(MenuItem.id == menu_id).delete()
        self.session.commit


if __name__ == '__main__':
    rv = RestaruantMenuViewer()
    print("Restaurants:", [x.name for x in rv.get_restaurants()])
