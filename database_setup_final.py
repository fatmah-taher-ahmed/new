import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

 
Base = declarative_base()
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
 
class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    cname = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

class Item (Base):
    __tablename__ = 'item'


    iname =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category) 
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

#We added this serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
       
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
           'category' :self.category,
           
           
       }
 

engine = create_engine('postgresql://catalog:password@localhost/catalog') 

Base.metadata.create_all(engine)
