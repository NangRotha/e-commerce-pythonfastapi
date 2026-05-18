from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    image_url: str
    category: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItem(CartItemBase):
    id: int
    user_id: int
    product: Product

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItem(OrderItemBase):
    id: int
    order_id: int

class OrderBase(BaseModel):
    shipping_address: str

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItem]
    
    class Config:
        from_attributes = True