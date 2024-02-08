from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Book])
def read_books(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve books.
    """
    if crud.user.is_superuser(current_user):
        books = crud.book.get_multi(db, skip=skip, limit=limit)
    else:
        books = crud.book.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return books


@router.post("/", response_model=schemas.Book)
def create_book(
    *,  
    db: Session = Depends(deps.get_db),
    book_in: schemas.BookCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new book.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    book = crud.book.create_with_owner(db=db, obj_in=book_in, author=current_user.email)
    return book


@router.put("/{id}", response_model=schemas.Book)
def update_book(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    book_in: schemas.BookUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an book.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    book = crud.book.get(db=db, id=id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book = crud.book.update(db=db, db_obj=book, obj_in=book_in)
    return book


@router.get("/{id}", response_model=schemas.Book)
def read_book(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get book by ID.
    """
    book = crud.book.get(db=db, id=id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not crud.user.is_superuser(current_user) and (book.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return book


@router.delete("/{id}", response_model=schemas.Book)
def delete_book(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an book.
    """
    book = crud.book.get(db=db, id=id)
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book = crud.book.remove(db=db, id=id)
    return book


@router.put("/{book_id}/borrow", response_model=schemas.Book)
def borrow_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Borrow a book.
    """
    book = crud.book.get(db=db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.count <= 0:
        raise HTTPException(status_code=400, detail="No copies available for borrowing")

    # Update book count and create borrow history entry
    book = crud.book.update(db=db, db_obj=book, obj_in={"count": book.count - 1})
    borrow_history_entry = schemas.BorrowHistoryCreate(book_id=book.id, user_id=current_user.id)
    crud.history.create_borrow_history(db=db, obj_in=borrow_history_entry)

    return book

@router.put("/{book_id}/return", response_model=schemas.Book)
def return_book(
    *,
    db: Session = Depends(deps.get_db),
    book_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Return a book.
    """
    book = crud.book.get(db=db, id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    borrow_history_entry = crud.history.get_last_borrow(db=db, book_id=book_id, user_id=current_user.id)
    if not borrow_history_entry:
        raise HTTPException(status_code=400, detail="You have not borrowed this book")

    # Update book count and mark borrow history entry as returned
    book = crud.book.update(db=db, db_obj=book, obj_in={"count": book.count + 1})
    crud.history.update_return(db=db, db_obj=borrow_history_entry, return_date=datetime.utcnow())

    return book

@router.get("/history/", response_model=List[schemas.BorrowHistoryRes])
def retrieve_user_book_history(
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_active_user),
) -> List[schemas.BorrowHistory]:
    """
    Retrieve the borrow history of the current user.
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    borrow_history = crud.history.get_user_borrow_history(db=db, user_id=current_user.id)
    if not borrow_history:
        raise HTTPException(status_code=404, detail="No borrow history found")
    return borrow_history