from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List

from utils.database import get_db
from models.user import (
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    UserLoginMethod
)

from config.settings import settings
from utils.hateoas import hateoas_user
from security.auth import issue_tokens_and_set_cookies
from security.password import hash_password, verify_password


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# =============================================================================
# Users Endpoints
# =============================================================================


# -----------------------------------------------------------------------------
# POST Endpoint
# -----------------------------------------------------------------------------

# Create new user ( with credentials aka manual )
@router.post("/", response_model=UserRead, status_code=201, name="create_user")
async def create_user(
    request: Request,
    response: Response,
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):

    new_user = User(
        last_name=user.last_name,
        first_name=user.first_name,
        email=user.email,
        hashed_password=hash_password(user.plaintext_password),
        is_active=True
    )
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)

        ### Need to add JWT logic here
        await issue_tokens_and_set_cookies(
            response=response,
            db=db,
            user=new_user,
        )

        return hateoas_user(request=request, user=new_user)
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create new user. {e}")


# -----------------------------------------------------------------------------
# GET Endpoints
# -----------------------------------------------------------------------------

# List all current users (with query and pagination) (no user required)
@router.get("/", response_model=List[UserRead], status_code=200, name="list_users")
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[datetime] = Query(None, description="Filter users created after this date"),
    created_before: Optional[datetime] = Query(None, description="Filter users created before this date"),
    sort_by: str = Query("created_at", regex="^(created_at|email|first_name|last_name)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    
    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if is_active is not None:
        filters.append(User.is_active == is_active)
    
    if created_after:
        filters.append(User.created_at >= created_after)
    
    if created_before:
        filters.append(User.created_at <= created_before)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply sorting
    sort_column = getattr(User, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    resources: List[UserRead] = []
    
    for user in users:
        resources.append(
            hateoas_user(request, user)
        )
    
    return resources
    

# Get specific user via id
@router.get("/{user_id}", response_model=UserRead, status_code=200, name="get_user")
async def get_user(
    request: Request,
    user_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive users in search"),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.id == user_id)
    
    if not include_inactive:
        query = query.where(User.is_active == True)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return hateoas_user(request, user)

# -----------------------------------------------------------------------------
# PATCH Endpoint
# -----------------------------------------------------------------------------

# Update specific user record via id
@router.patch("/{user_id}", response_model=UserRead, status_code=200, name="update_user")
async def update_user(
    request: Request,
    user_id: UUID, 
    user_update: UserUpdate,
    force_update: bool = Query(False, description="Force update even if user is inactive"),
    db: AsyncSession = Depends(get_db)
):
    """Update user information"""
    
    # Fetch user
    query = select(User).where(User.id == user_id)
    
    if not force_update:
        query = query.where(User.is_active == True)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=404, 
            detail="User not found or inactive"
        )
    
    # Update basic fields
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    
    # Email update - only for CREDENTIALS users
    if user_update.email is not None:
        if user.login_method != UserLoginMethod.CREDENTIALS:
            raise HTTPException(
                status_code=400,
                detail="Email cannot be updated for OAuth users"
            )
        
        # Check if email is already taken
        email_check = await db.execute(
            select(User).where(User.email == user_update.email, User.id != user_id)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Email already in use"
            )
        
        user.email = user_update.email
    
    # Password update - only for CREDENTIALS users
    if user_update.current_password is not None and user_update.new_password is not None:
        if user.login_method != UserLoginMethod.CREDENTIALS:
            raise HTTPException(
                status_code=400,
                detail="Password cannot be updated for OAuth users"
            )
        
        # Verify current password
        if user.hashed_password and not verify_password(user_update.current_password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Current password is incorrect"
            )
        
        # Update to new password
        user.hashed_password = hash_password(user_update.new_password)
    
    user.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(user)
    
    return hateoas_user(request, user)

# -----------------------------------------------------------------------------
# DELETE Endpoint
# -----------------------------------------------------------------------------

# Delete specific user record via id
@router.delete("/{user_id}", status_code=204, name="delete_user")
async def delete_user(
    user_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (deactivate) instead of hard delete"),
    force_delete: bool = Query(False, description="Allow deletion of inactive users"),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.id == user_id)
    
    if not force_delete:
        query = query.where(User.is_active == True)
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found or already inactive")
    
    if soft_delete:
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
    else:
        await db.delete(user)
        await db.commit()