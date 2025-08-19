from __future__ import annotations
from typing import Iterable, Sequence, Optional, Tuple, Annotated
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from app.crud_schemas import *
from app.models import (
    User, Language, Word, UserWordProgress, LearningProfile,
    Dictionary, Translation, Definition, Example, Text
)
from app.database import get_db

db_dependency = Annotated[Session, Depends(get_db)]


def create_learning_profile(db: db_dependency, learning_profile: LearningProfileBase)-> LearningProfileRead:
    learning_profile_db = db.query(LearningProfile).filter(LearningProfile.user_id == learning_profile.user_id &
                                     LearningProfile.primary_language_id == learning_profile.primary_language_id &
                                     LearningProfile.foreign_language_id == learning_profile.foreign_language_id).first()
    if learning_profile_db:
        raise HTTPException(status_code=400, detail="Profile already exists")
    created_lp = LearningProfile(user_id=learning_profile.user_id, 
                                 primary_language_id=learning_profile.primary_language_id,
                                 foreign_language_id=learning_profile.foreign_language_id,
                                 is_active=learning_profile.is_active)
    db.add(created_lp)
    db.commit()
    db.refresh(created_lp)
    return created_lp