from eApp.database import Base,db_dependency
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,Boolean,ForeignKey,String,Text,Numeric,DateTime,Index
from sqlalchemy.sql import func
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_access_control",'paid_status','is_active','free_count'),
    )
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String(20),nullable=False)
    email = Column(String(200),nullable=False,unique=True,index=True)
    password = Column(String(100),nullable=False)
    is_verified = Column(Boolean,default=0)
    join_date = Column(DateTime, func.now,default=datetime.now)
    
    # Subscription related fields
    free_count = Column(Integer,nullable=False,default=3)
    paid_status = Column(Boolean,default=False)  # status: have subscription=True else False
    role = Column(String(20),default="user")  # role: user,admin
    is_active = Column(Boolean,default=True)
    last_login = Column(DateTime,nullable=True)

    #one to many relationship with(Business)
    business = relationship("Business",back_populates="user")
    # Relationship with SocialMediaToken
    social_media_tokens = relationship("SocialMediaToken",back_populates="user",cascade="all, delete-orphan")
    # Subscription relationships
    subscriptions = relationship("Subscription",back_populates="user",cascade="all, delete-orphan")
    conversations = relationship("Conversation",back_populates="user",cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod",back_populates="user",cascade="all, delete-orphan")
    
    
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
    is_favourite = Column(Boolean,nullable=False,default=False)
    add_to_cart = Column(Boolean,nullable=False,default=False)
    business_id = Column(Integer,ForeignKey('business.id'))
    # For chatbot/social media integration - unique ID for each product
    chatbot_product_id = Column(String(100),nullable=True,unique=True,index=True)

    #many to one relationship with (Business)
    busn_rel = relationship("Business",back_populates="prd")

class SocialMediaToken(Base):
    __tablename__ = "social_media_tokens"
    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey('users.id'),nullable=False,index=True)
    facebook = Column(String(512),nullable=True)
    instagram = Column(String(512),nullable=True)
    linkedin = Column(String(512),nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with User
    user = relationship("User",back_populates="social_media_tokens")


# ==================== Subscription & Payment Models ====================

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("idx_active_subscriptions",'status','subscription_expires_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    currency = Column(String(10), default='dollar')
    status = Column(String(20), default='inactive', index=True)  # pending,active,expired,cancelled
    subscription_type = Column(String(10), default='free', index=True)  # free,monthly,yearly
    subscription_expires_at = Column(DateTime, nullable=True, index=True)
    payment_transaction_id = Column(String(100), nullable=True, index=True)  # SSLCommerz trans ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with user
    user = relationship("User", back_populates="subscriptions")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        Index('idx_user_payment_methods', 'user_id', 'is_default'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Token from payment gateway: From SSLCommerz
    gateway_token = Column(String(255), unique=True, index=True)
    gateway_name = Column(String(50), default="sslcommerz")
    
    # Safe to store - Masked card info for display
    card_last_4 = Column(String(4), nullable=False)  # Last 4 digits only
    card_brand = Column(String(20), nullable=False)  # visa, mastercard, amex
    card_type = Column(String(20), nullable=False)  # credit, debit
    expiry_month = Column(Integer, nullable=False)  # 1-12
    expiry_year = Column(Integer, nullable=False)  # 2025
    
    # Billing address (safe)
    billing_name = Column(String(100), nullable=False)
    billing_address = Column(String(255), nullable=False)
    billing_city = Column(String(100), nullable=False)
    billing_country = Column(String(100), nullable=False)
    billing_postcode = Column(String(20), nullable=False)
    billing_phone = Column(String(20), nullable=False)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="payment_methods")


class PricingConfig(Base):
    __tablename__ = "pricing_config"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String(20), unique=True)  # monthly, yearly, half-yearly, 5min etc.
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String(10), default='Dollar')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== Conversation & Message Models ====================

class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index('idx_conversation_thread', 'thread_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    thread_id = Column(Text, nullable=False, unique=True)  # checkpoints
    title = Column(Text)  # for frontend maintain chat history side bar
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with user, messageHistory
    user = relationship("User", back_populates="conversations")
    messages = relationship("MessageHistory", back_populates="conversation", cascade="all, delete-orphan")


class MessageHistory(Base):
    __tablename__ = "message_history"
    __table_args__ = (
        Index('idx_conversation_id', 'conversation_id', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete="CASCADE"), nullable=False)
    thread_id = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    sender_role = Column(String(10), nullable=False)  # human, ai
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

