import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.config import settings
from app.db.database import get_db
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/github")
async def github_login() -> RedirectResponse:
    params = (
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=read:user"
    )
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/github/callback")
async def github_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )

    token_data = token_resp.json()
    gh_access_token = token_data.get("access_token")
    if not gh_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain GitHub access token",
        )

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {gh_access_token}",
                "Accept": "application/json",
            },
        )

    gh_user = user_resp.json()
    github_id: int | None = gh_user.get("id")
    if not github_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch GitHub user info",
        )

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=github_id,
            github_username=gh_user.get("login"),
            github_avatar_url=gh_user.get("avatar_url"),
        )
        db.add(user)
        await db.flush()
    else:
        user.github_username = gh_user.get("login")
        user.github_avatar_url = gh_user.get("avatar_url")

    jwt_token = create_access_token(user.id)
    return {"access_token": jwt_token, "token_type": "bearer"}