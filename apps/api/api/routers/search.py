from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user
from api.models.user import User
from api.schemas.document import AutocompleteItem, SearchResultItem
from api.services.search import autocomplete, hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResultItem])
def search(
    q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    return hybrid_search(db, user, q)


@router.get("/autocomplete", response_model=list[AutocompleteItem])
def search_autocomplete(
    q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    return autocomplete(db, user, q)
