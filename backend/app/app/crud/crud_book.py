from typing import List, Optional
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.book import Book, BorrowHistory
from app.schemas.book import BookCreate, BookUpdate, BorrowHistoryCreate, BorrowHistoryUpdate


class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):

    def create_with_owner(
        self, db: Session, *, obj_in: BookCreate, author: int
    ) -> Book:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, author=author)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, author: str, skip: int = 0, limit: int = 100
    ) -> List[Book]:
        return (
            db.query(self.model)
            .filter(Book.author == author)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDBorrowHistory(CRUDBase[BorrowHistory, BorrowHistoryCreate, BorrowHistoryCreate]):
    
    def create_borrow_history(self, db: Session, obj_in: BorrowHistoryCreate):
        obj_in_data = jsonable_encoder(obj_in)
        db_borrow_history = BorrowHistory(**obj_in_data)
        db.add(db_borrow_history)
        db.commit()
        db.refresh(db_borrow_history)
        return db_borrow_history
    
    def get_last_borrow(self, db: Session, book_id: int, user_id: int) -> Optional[BorrowHistory]:
        """
        Retrieve the last borrow history entry for a specific book and user.
        """
        return db.query(BorrowHistory).filter(
            BorrowHistory.book_id == book_id,
            BorrowHistory.user_id == user_id
        ).order_by(BorrowHistory.id.desc()).first()
    
    def update_return(self, db: Session, db_obj: BorrowHistory, return_date: datetime) -> BorrowHistory:
        """
        Update the return date of a borrow history entry.
        """
        db_obj.return_date = return_date
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_user_borrow_history(self, db: Session, user_id: int) -> List[BorrowHistory]:
        """
        Retrieve the borrow history of a user.
        """
        return db.query(BorrowHistory).filter(
            BorrowHistory.user_id == user_id
        ).all()

book = CRUDBook(Book)
history = CRUDBorrowHistory(BorrowHistory)
