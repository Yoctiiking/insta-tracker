from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RelationOut(BaseModel):
    username: str
    full_name: Optional[str] = None
    is_follower: bool
    is_following: bool

    class Config:
        from_attributes = True


class SnapshotOut(BaseModel):
    id: int
    created_at: datetime
    followers_count: int
    following_count: int

    class Config:
        from_attributes = True


class SyncResult(BaseModel):
    snapshot_id: int
    followers_count: int
    following_count: int
    non_mutual_count: int
