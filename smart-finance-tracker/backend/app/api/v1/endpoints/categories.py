"""app/api/v1/endpoints/categories.py"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Category
import uuid

router = APIRouter()


@router.get("")
async def list_categories(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Category).where(or_(Category.user_id == user.id, Category.is_default == True))
    )
    cats = result.scalars().all()
    return [{"id": str(c.id), "name": c.name, "icon": c.icon, "color": c.color, "type": c.type} for c in cats]


@router.post("", status_code=201)
async def create_category(
    name: str, icon: str = "📦", color: str = "#6366f1", type: str = "expense",
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    cat = Category(user_id=user.id, name=name, icon=icon, color=color, type=type)
    db.add(cat)
    await db.flush()
    return {"id": str(cat.id), "name": cat.name, "icon": cat.icon, "color": cat.color}
