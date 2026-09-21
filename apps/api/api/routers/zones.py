import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import get_current_user, require_super_admin
from api.models.user import User
from api.models.zone_project import Zone
from api.schemas.zone_project import ZoneCreate, ZoneOut, ZoneUpdate

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
def list_zones(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Zone]:
    return db.query(Zone).order_by(Zone.name).all()


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(
    payload: ZoneCreate, db: Session = Depends(get_db), _: User = Depends(require_super_admin)
) -> Zone:
    zone = Zone(name=payload.name, code=payload.code)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.patch("/{zone_id}", response_model=ZoneOut)
def update_zone(
    zone_id: uuid.UUID,
    payload: ZoneUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> Zone:
    zone = db.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")
    if payload.name is not None:
        zone.name = payload.name
    if payload.code is not None:
        zone.code = payload.code
    db.commit()
    db.refresh(zone)
    return zone
