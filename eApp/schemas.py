from typing import Optional
from pydantic import BaseModel,field_validator
from datetime import datetime,timezone
##_______________________Creating Purpouse____________________##
class User(BaseModel):
    id : int 
    username : str 
    email : str
    password : str 
    trail_remain : int
    paid : bool
    role : str 
    is_verified: bool 
    
    

class Business(BaseModel):
    business_name : str 
    city : str 
    region : str 
    business_description : str 
    logo : str 
    owner : int 

class Product(BaseModel):
    id : int
    name : str 
    category : str 
    original_price : float
    new_price : float
    percentage_discount : int 
    offer_expiration_date : str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    product_image : str 
    business_id : int
    add_to_cart : bool 
    is_favourite : bool 
    @field_validator('offer_expiration_date', mode='before')
    @classmethod
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            # If offer_expiration_date is not provided, set it to the current date
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return value


# Token model
class Token(BaseModel):
    access_token: str
    token_type: str
    

#upload product
class UploadProduct(BaseModel):
    name : str 
    category : str 
    original_price : float
    new_price : float
    product_details : str
    offer_expiration_date : str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    @field_validator('offer_expiration_date', mode='before')
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            # If offer_expiration_date is not provided, set it to the current date
            return datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        return value

#updated product model:
class UpdatedProduct(BaseModel):
    name : str 
    category : str 
    product_details : str 
    original_price : float
    new_price : float
    offer_expiration_date : str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    @field_validator('offer_expiration_date', mode='before')
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            return datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        return value


class InputMessage(BaseModel):
    message: str
    checkpoint_id: Optional[str] = None





#<--------------- app/schema/social_media_schema.py ------------------>

class SocialMediaTokenBase(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    expires_at: Optional[datetime] = None
class TokenCreate(SocialMediaTokenBase):
    pass


class TokenUpdate(SocialMediaTokenBase):
    pass


class TokenResponse(SocialMediaTokenBase):
    id: int
    
    class Config:
        from_attributes = True
        



class FacebookPostBase(BaseModel):
    text: str


class FacebookTextPost(BaseModel):
    generate_content : str 
    current_user_id : int 


class FacebookPhotoPost(FacebookPostBase):
    photo_url: str
    

class FacebookVideoPost(FacebookPostBase):
    video_url: str
