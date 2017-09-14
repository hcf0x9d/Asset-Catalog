#!/usr/bin/python

# Configuration ============================================================= #
import random
import string

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)

Base = declarative_base()

# Generating a secret key for our OAuth process
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))


class User(Base):
    """Table of users, each user can only modify their own items and categories

    Extends:
        Base

    Variables:
        __tablename__ {str} -- name of the table in the database
        id {int} -- unique id (primary key)
        name {str} -- user's full name as provided by Google
        email {str} -- email address of the user provided by Google
        picture {str} -- URI to users image from Google
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False, index=True)
    picture = Column(String(250))
    password_hash = Column(String(64))

    # TODO: Not sure if we are going to go forward with passwords
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def varify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }


class Category(Base):
    """The category table will track categories for the items in the catalog

    For the sake of simplicity in this example we will go with a 1:1 mapping
    In future projects, perhaps a link table would be good to add items to
    multiple categories

    Extends:
        Base

    Variables:
        __tablename__ {str} -- name of the table in the database
        name {str} -- friendly category name
        id {int} -- unique id (primary key)
        user_id {int} -- id of the user this category belongs to
    """
    __tablename__ = 'category'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    slug = Column(String(80), nullable=False)

    @property
    def serialize(self):
        """For developing an API endpoint

        Returns the item object for an API endpoint
        """

        # TODO: Fill out the endpiont information for the Category (api)
        return {
            'id': self.id,
            'name': self.name,
        }


class Item(Base):
    """Table of items within the catalog. Each item is assigned a category

    Extends:
        Base

    Variables:
        __tablename__ {str} -- name of the table in the database
        name {str} -- friendly item name
        id {int} -- unique id (primary key)
        category_id {int} -- id of the category this item belongs to
        user_id {int} -- id of the user this item belongs to
    """
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    slug = Column(String(80), nullable=False)
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        # TODO: Fill out the endpiont information for the Item (api)
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
        }


# End of File =============================================================== #
engine = create_engine('sqlite:///itemcatalog.db')


Base.metadata.create_all(engine)
