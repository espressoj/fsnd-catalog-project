#!/usr/bin/env Python
# Import classes from SqlAlchemy to create the database
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# Import class for password and token handling
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer,
                        BadSignature, SignatureExpired)
# Import additional libraries needed
import os
import sys
import random, string

# Construct the base class
Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for
                x in xrange(32))


# Create a class for the Employee table
class User(Base):
    '''This class will create the User table.'''
    # Declare the table name as a reference
    __tablename__ = 'user'
    # Define the columns in the table and their attributes
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    picture = Column(String)
    email = Column(String)
    password_hash = Column(String(64))

    # Hash the password
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)
    # Generate an authorization token that expires in 10 minutes
    def generate_auth_token(self, expiration=600):
    	s = Serializer(secret_key, expires_in = expiration)
    	return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
    	s = Serializer(secret_key)
    	try:
    		data = s.loads(token)
    	except SignatureExpired:
    		#Valid Token, but expired
    		return None
    	except BadSignature:
    		#Invalid Token
    		return None
    	user_id = data['id']
    	return user_id


# Create a class for the Items table
class Items(Base):
    '''This class will create the Items table.'''
    # Declare the table name as a reference
    __tablename__ = 'items'
    # Define the columns in the table and their attributes
    itemId = Column(Integer, primary_key = True)
    itemName = Column(String(100), nullable = False)
    itemDescription = Column(String(255), nullable = False)
    owner = Column(Integer, ForeignKey('user.id'))
    added = Column(DateTime, nullable = False)
    modified = Column(DateTime, nullable = False)
    status = Column(String(1), nullable = False)
    # Relationships with other classes
    # Relate to Items
    user = relationship(User)


# Create a class for the Categories table
class Categories(Base):
    '''This class will create the Categories table.'''
    # Declare the table name as a reference
    __tablename__ = 'categories'
    # Define the columns in the table and their attributes
    categoryId = Column(Integer, primary_key = True)
    categoryName = Column(String(255), nullable = False)


# Create a class for the Inventory table
class Inventory(Base):
    '''This class will create the Inventory table.'''
    # Declare the table name as a reference
    __tablename__ = 'inventory'
    # Define the columns in the table and their attributes
    itemId = Column(Integer, ForeignKey('items.itemId'), primary_key = True)
    inventoryCount = Column(Integer, nullable = False)
    itemPrice = Column(String(25), nullable = True)
    lastUpdated = Column(DateTime, nullable = False)
    # Relationships with other classes
    # Relate to Items
    items = relationship(Items)


# Create a class for the ItemCategories table
class ItemCategories(Base):
    '''This class will create the ItemCategories table.'''
    # Declare the table name as a reference
    __tablename__ = 'itemCategories'
    # Define the columns in the table and their attributes
    categoryId = Column(Integer, ForeignKey('categories.categoryId'))
    itemId = Column(Integer, ForeignKey('items.itemId'), primary_key = True)
    # Relationships with other classes
    # Relate to Items
    items = relationship(Items)
    # Relate to Categories
    categories = relationship(Categories)

# Create a class for the ItemTags table
class ItemTags(Base):
    '''This class will create the ItemTags table.'''
    # Declare the table name as a reference
    __tablename__ = 'itemTags'
    # Define the columns in the table and their attributes
    tagId = Column(Integer, primary_key = True)
    itemId = Column(Integer, ForeignKey('items.itemId'))
    tag = Column(String(80), nullable = False)
    # Relationships with other classes
    # Relate to Items
    items = relationship(Items)


# Create a class for the ItemPhotos table
class ItemPhotos(Base):
    '''This class will create the ItemPhotos table.'''
    # Declare the table name as a reference
    __tablename__ = 'itemPhotos'
    # Define the columns in the table and their attributes
    photoId = Column(Integer, primary_key = True)
    itemId = Column(Integer, ForeignKey('items.itemId'))
    photoUrl = Column(String(500), nullable = False)
    # Relationships with other classes
    # Relate to Items
    items = relationship(Items)

# Set the Dialect and Pool using SqlAlchemy's create_engine()
engine = create_engine('sqlite:///catalog.db')
# Create the tables using SqlAlchemy's metadata.create_all()
Base.metadata.create_all(engine)
