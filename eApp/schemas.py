from pydantic import BaseModel
from pydantic import BaseModel, validator
from datetime import datetime
##_______________________Creating Purpouse____________________##
class User(BaseModel):
    username : str 
    email : str
    password : str 
    

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
    offer_expiration_date : str = datetime.utcnow().strftime("%Y-%m-%d")
    product_image : str 
    business_id : int
    add_to_cart : bool 
    is_favourite : bool 
    @validator('offer_expiration_date', pre=True, always=True)
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            # If offer_expiration_date is not provided, set it to the current date
            return datetime.utcnow().date().strftime("%Y-%m-%d")
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
    offer_expiration_date : str = datetime.utcnow().strftime("%Y-%m-%d")
    @validator('offer_expiration_date', pre=True, always=True)
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            # If offer_expiration_date is not provided, set it to the current date
            return datetime.utcnow().date().strftime("%Y-%m-%d")
        return value

#updated product model:
class UpdatedProduct(BaseModel):
    name : str 
    category : str 
    product_details : str 
    original_price : float
    new_price : float
    offer_expiration_date : str = datetime.utcnow().strftime("%Y-%m-%d")
    @validator('offer_expiration_date', pre=True, always=True)
    def set_default_offer_expiration_date(cls, value):
        if value == "string" or None:
            return datetime.utcnow().date().strftime("%Y-%m-%d")
        return value


