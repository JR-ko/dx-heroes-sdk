from uuid import UUID

from pydantic import BaseModel


class Product(BaseModel):
    id: UUID
    name: str
    description: str


class ProductRegistered(BaseModel):
    id: UUID


class Offer(BaseModel):
    id: UUID
    price: int
    items_in_stock: int
