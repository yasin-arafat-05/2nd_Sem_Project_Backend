from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum, JSON, LargeBinary, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from eApp.database import Base

# Enums for different user types and business categories
class UserType(PyEnum):
    NORMAL = "normal"
    SELLER = "seller"
    ADMIN = "admin"

class BusinessCategory(PyEnum):
    GROCERY = "grocery"
    MEDICINE = "medicine"
    RESTAURANT = "restaurant"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKSTORE = "bookstore"
    HARDWARE = "hardware"
    OTHER = "other"

class ProductStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class OrderStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# User table with priority system
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    user_type = Column(Enum(UserType), default=UserType.NORMAL, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    profile_image = Column(String(500), default="default.jpg")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False)
    addresses = relationship("UserAddress", back_populates="user")
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    reviews = relationship("ProductReview", back_populates="user")

# Seller Profile with location information
class SellerProfile(Base):
    __tablename__ = "seller_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_name = Column(String(100), nullable=False)
    business_description = Column(Text)
    business_category = Column(Enum(BusinessCategory), nullable=False)
    business_license = Column(String(100), nullable=True)
    tax_id = Column(String(50), nullable=True)
    
    # Location information (Google Maps integration)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=True)
    google_place_id = Column(String(255), nullable=True)
    
    # Business hours
    business_hours = Column(JSON, nullable=True)  # Store as JSON: {"monday": {"open": "09:00", "close": "18:00"}}
    
    # Contact information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verification_documents = Column(JSON, nullable=True)  # Store document paths
    
    # Social media and marketing
    facebook_page = Column(String(255), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    marketing_preferences = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller")
    orders = relationship("Order", back_populates="seller")
    
    # Index for location-based queries
    __table_args__ = (
        Index('idx_location', 'latitude', 'longitude'),
    )

# User Address for delivery
class UserAddress(Base):
    __tablename__ = "user_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_type = Column(String(50), nullable=False)  # home, work, other
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="addresses")

# Product Categories
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    parent = relationship("Category", remote_side=[id])
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

# Products with comprehensive information
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    
    # Category and seller information
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"), nullable=False)
    
    # Pricing
    original_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0)
    
    # Product details (like Star Tech product specifications)
    specifications = Column(JSON, nullable=True)  # Store detailed specs as JSON
    features = Column(JSON, nullable=True)  # Store product features
    dimensions = Column(JSON, nullable=True)  # Store dimensions
    weight = Column(Float, nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True, unique=True)
    
    # Inventory
    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    
    # SEO and Marketing
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Store tags as JSON array
    
    # AI and Automation
    ai_generated_content = Column(JSON, nullable=True)  # Store AI-generated marketing content
    chatbot_product_id = Column(String(100), nullable=True, unique=True)  # For chatbot integration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    seller = relationship("SellerProfile", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")
    
    # Indexes for search optimization
    __table_args__ = (
        Index('idx_product_search', 'name', 'description'),
        Index('idx_product_category', 'category_id'),
        Index('idx_product_seller', 'seller_id'),
    )

# Product Images
class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(50), default="product")  # product, thumbnail, gallery
    alt_text = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="images")

# Shopping Cart
class CartItem(Base):
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    
    # Unique constraint to prevent duplicate cart items
    __table_args__ = (
        Index('idx_cart_user_product', 'user_id', 'product_id', unique=True),
    )

# Favorites/Wishlist
class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (
        Index('idx_favorite_user_product', 'user_id', 'product_id', unique=True),
    )

# Orders
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"), nullable=False)
    
    # Order details
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    final_amount = Column(Float, nullable=False)
    
    # Delivery information
    delivery_address = Column(JSON, nullable=False)  # Store address as JSON
    delivery_instructions = Column(Text, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    
    # Order status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(String(50), default="pending")
    payment_method = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    seller = relationship("SellerProfile", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

# Order Items
class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

# Product Reviews
class ProductReview(Base):
    __tablename__ = "product_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

# AI Chatbot Sessions
class ChatbotSession(Base):
    __tablename__ = "chatbot_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be anonymous
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    conversation_data = Column(JSON, nullable=True)  # Store conversation history
    ai_generated_content = Column(JSON, nullable=True)  # Store AI responses
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")

# Social Media API Keys for Marketing
class SocialMediaAPI(Base):
    __tablename__ = "social_media_apis"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # facebook, instagram, twitter, etc.
    api_key = Column(Text, nullable=False)
    api_secret = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("SellerProfile")

# AI Marketing Campaigns
class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # facebook, instagram, etc.
    content = Column(Text, nullable=False)
    ai_generated_content = Column(JSON, nullable=True)
    target_audience = Column(JSON, nullable=True)
    budget = Column(Float, nullable=True)
    status = Column(String(50), default="draft")
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    seller = relationship("SellerProfile")
    product = relationship("Product")

# Search History for AI Recommendations
class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be anonymous
    search_query = Column(String(255), nullable=False)
    search_location = Column(JSON, nullable=True)  # Store lat, lng, radius
    search_results = Column(JSON, nullable=True)  # Store search results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Notification System
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # order, promotion, system
    is_read = Column(Boolean, default=False)
    data = Column(JSON, nullable=True)  # Store additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# System Settings
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
