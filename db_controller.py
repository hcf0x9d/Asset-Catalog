#!/usr/bin/python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import Base, Category, Item, User

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

database_session = sessionmaker(bind=engine)
session = database_session()


class DatabaseController:
    """Controller to handle database operations between view and model layers"""

    def create_user(self, auth_session):
        newUser = User(name=auth_session['name'], email=auth_session['email'],
                       picture=auth_session['picture'])
        session.add(newUser)
        session.commit()
        return

    def read_user(self, auth_session):
        try:
            user = session.query(User).filter_by(email=auth_session['email']).one()
            return user
        except:
            self.addUser(auth_session)
            return session.query(User).filter_by(email=auth_session['email']).one()

    def read_category(self, category_slug, auth_session):
        return session.query(Category).filter_by(slug=category_slug,
                                                 user_id=auth_session['user_id']).one()

    def read_category_list(self, auth_session):
        return session.query(Category).filter_by(user_id=auth_session['user_id']).all()

    def read_item(self, item_slug):
        return session.query(Item, Category).filter_by(slug=item_slug).join(Category).one()

    def read_item_list(self, category_id, auth_session):
        return session.query(Item).filter_by(category_id=category_id,
                                             user_id=auth_session['user_id']).all()

    def read_item_list_api(self, category_id, auth_session):
        obj = session.query(Item).filter_by(category_id=category_id).all()
        return obj

    def add_item(self, obj, user_id):
        """Controller for passing items within a category to DB

        :param obj: JSON passed from AJAX
        :param user_id: User ID Integer
        :return:
        """
        new_item = Item()
        new_item.name = obj['name']
        new_item.category_id = obj['category_id']
        new_item.description = obj['description']
        new_item.slug = obj['slug']
        new_item.user_id = user_id

        session.add(new_item)
        session.commit()
        return

    def update_item(self, obj, user_id):
        """Controller for passing items within a category to DB

        :param obj: JSON passed from AJAX
        :param user_id: User ID Integer
        :return:
        """
        new_item = session.query(Item).filter_by(id=obj['id']).one()
        new_item.name = obj['name']
        new_item.description = obj['description']
        print(new_item)
        session.commit()
        return

    def add_category(self, obj, user_id):
        """Controller for passing items within a category to DB

        :param obj: JSON passed from AJAX
        :param user_id: User ID Integer
        :return:
        """
        new_category = Category()
        new_category.name = obj['name']
        new_category.slug = obj['slug']
        new_category.icon= obj['icon']
        new_category.user_id = user_id

        session.add(new_category)
        session.commit()
        return

    def delete_item(self, item, user_id):
        remove_item = session.query(Item).filter_by(id=item['id'],
                                                    user_id=user_id).one()
        session.delete(remove_item)
        session.commit()
        return

    def delete_category(self, category, user_id):
        remove_item = session.query(Category).filter_by(slug=category['slug'],
                                                        user_id=user_id).one()

        session.query(Item).filter_by(category_id=remove_item.id).update(dict(category_id=5))

        session.delete(remove_item)
        session.commit()

        return
