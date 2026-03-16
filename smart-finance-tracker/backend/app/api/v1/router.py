"""app/api/v1/router.py"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, transactions, categories, budgets, analytics, export

api_router = APIRouter()
api_router.include_router(auth.router,         prefix="/auth",         tags=["Authentication"])
api_router.include_router(transactions.router, prefix="/transactions",  tags=["Transactions"])
api_router.include_router(categories.router,   prefix="/categories",   tags=["Categories"])
api_router.include_router(budgets.router,      prefix="/budgets",      tags=["Budgets"])
api_router.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics & AI"])
api_router.include_router(export.router,       prefix="/export",       tags=["Export"])
