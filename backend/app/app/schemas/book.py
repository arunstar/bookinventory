from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# Shared properties
class BookBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    count: Optional[int] = None


# Properties to receive on item creation
class BookCreate(BookBase):
    title: str


# Properties to receive on item update
class BookUpdate(BookBase):
    pass


# Properties shared by models stored in DB
class BookInDBBase(BookBase):
    id: int
    title: str
    author: str

    class Config:
        orm_mode = True


# Properties to return to client
class Book(BookInDBBase):
    pass


# Properties properties stored in DB
class BookInDB(BookInDBBase):
    pass

class BorrowHistoryBase(BaseModel):
    user_id: int
    book_id: int


class BorrowHistory(BorrowHistoryBase):
    pass


class BorrowHistoryCreate(BorrowHistoryBase):
    pass

class BorrowHistoryUpdate(BorrowHistoryBase):
    pass


class BorrowHistoryUpdate(BaseModel):
    return_date: Optional[datetime]

class BorrowHistoryInDB(BorrowHistoryBase):
    id: int
    return_date: Optional[datetime]

    class Config:
        orm_mode = True

class BorrowHistoryRes(BorrowHistoryInDB):
    id: int
    borrow_date: datetime
    return_date: Optional[datetime]