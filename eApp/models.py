from database import Base,db_dependency
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,Boolean,ForeignKey,String,Text,Numeric,DateTime
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String(20),nullable=False)
    email = Column(String(200),nullable=False,unique=True)
    password = Column(String(100),nullable=False)
    is_verified = Column(Boolean,default=0)
    join_date = Column(DateTime, func.now,default=datetime.now)

    #one to many relationship with(Business)
    business = relationship("Business",back_populates="user")
    
class Business(Base):
    __tablename__ = "business"
    id = Column(Integer,primary_key=True,index=True)
    business_name = Column(String(20),nullable=False)
    city = Column(String(100),default="Unspecified")
    region = Column(String(100),default="Unspecified")
    business_description = Column(Text,nullable=True,default="No Business Description")
    logo = Column(String(200),nullable=False,default="default.jpg")
    owner = Column(Integer,ForeignKey('users.id'))

    #many to one relationship with(User)
    user = relationship("User",back_populates="business")

    #one to many relationship with(Product)
    prd = relationship("Product",back_populates="busn_rel")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(100),nullable=False,index=True)
    category = Column(String(30),index=True)
    original_price = Column(Numeric(precision=10,scale=2)) #Column(Float(precision=2))
    new_price = Column(Numeric(precision=10,scale=2))
    percentage_discount = Column(Integer)
    offer_expiration_date = Column(String(200),nullable=False, default=datetime.utcnow().date())
    product_details = Column(Text,nullable=False,default="No Product Details Found")
    product_image = Column(String(200),nullable=False,default="productDefault.jpg")
    business_id = Column(Integer,ForeignKey('business.id'))

    #many to one relationship with (Business)
    busn_rel = relationship("Business",back_populates="prd")

