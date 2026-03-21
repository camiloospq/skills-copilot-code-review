"""
Announcement endpoints for the High School Management System API
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    start_date: Optional[str] = None
    expiration_date: str = Field(..., min_length=10, max_length=10)


def _require_authenticated_teacher(username: Optional[str]) -> Dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _parse_date(value: Optional[str], field_name: str) -> Optional[str]:
    if value in (None, ""):
        return None

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must use YYYY-MM-DD format"
        ) from exc

    return parsed.isoformat()


def _validate_payload(payload: AnnouncementPayload) -> Dict[str, Any]:
    start_date = _parse_date(payload.start_date, "start_date")
    expiration_date = _parse_date(payload.expiration_date, "expiration_date")

    if expiration_date is None:
        raise HTTPException(status_code=400, detail="expiration_date is required")

    if start_date and start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after expiration_date"
        )

    return {
        "title": payload.title.strip(),
        "message": payload.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
    }


def _status_for_announcement(announcement: Dict[str, Any]) -> str:
    today = date.today().isoformat()
    start_date = announcement.get("start_date")
    expiration_date = announcement["expiration_date"]

    if expiration_date < today:
        return "expired"

    if start_date and start_date > today:
        return "scheduled"

    return "active"


def _serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(announcement["_id"]),
        "title": announcement["title"],
        "message": announcement["message"],
        "start_date": announcement.get("start_date"),
        "expiration_date": announcement["expiration_date"],
        "created_at": announcement.get("created_at"),
        "updated_at": announcement.get("updated_at"),
        "status": _status_for_announcement(announcement),
    }


def _get_announcement_or_404(announcement_id: str) -> Dict[str, Any]:
    try:
        object_id = ObjectId(announcement_id)
    except InvalidId as exc:
        raise HTTPException(status_code=404, detail="Announcement not found") from exc

    announcement = announcements_collection.find_one({"_id": object_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return announcement


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all announcements that are currently active."""
    today = date.today().isoformat()
    announcements = announcements_collection.find(
        {
            "expiration_date": {"$gte": today},
            "$or": [
                {"start_date": None},
                {"start_date": {"$lte": today}},
            ],
        }
    )

    serialized = [_serialize_announcement(announcement) for announcement in announcements]
    return sorted(serialized, key=lambda announcement: (announcement["expiration_date"], announcement["title"].lower()))


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for announcement management."""
    _require_authenticated_teacher(teacher_username)

    announcements = [_serialize_announcement(announcement) for announcement in announcements_collection.find({})]
    status_order = {"active": 0, "scheduled": 1, "expired": 2}
    return sorted(
        announcements,
        key=lambda announcement: (
            status_order.get(announcement["status"], 99),
            announcement["expiration_date"],
            announcement["title"].lower(),
        )
    )


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement."""
    _require_authenticated_teacher(teacher_username)
    announcement_data = _validate_payload(payload)

    timestamp = datetime.now(timezone.utc).isoformat()
    announcement = {
        **announcement_data,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    result = announcements_collection.insert_one(announcement)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    return {"message": "Announcement created", "announcement": _serialize_announcement(created)}


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement."""
    _require_authenticated_teacher(teacher_username)
    announcement = _get_announcement_or_404(announcement_id)
    announcement_data = _validate_payload(payload)

    announcements_collection.update_one(
        {"_id": announcement["_id"]},
        {
            "$set": {
                **announcement_data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }
    )

    updated = announcements_collection.find_one({"_id": announcement["_id"]})
    return {"message": "Announcement updated", "announcement": _serialize_announcement(updated)}


@router.delete("/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Delete an announcement."""
    _require_authenticated_teacher(teacher_username)
    announcement = _get_announcement_or_404(announcement_id)

    announcements_collection.delete_one({"_id": announcement["_id"]})
    return {"message": "Announcement deleted"}