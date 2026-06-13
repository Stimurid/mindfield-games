from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GameSession
from ..services.operator_profile import build_operator_profile

router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.get("/me")
def get_my_operator_profile(
    db: Session = Depends(get_db),
    x_player_token: str | None = Header(default=None, alias="X-Player-Token"),
):
    if not x_player_token:
        raise HTTPException(400, "X-Player-Token header required")
    sessions = (
        db.query(GameSession)
        .filter(GameSession.player_token == x_player_token)
        .all()
    )
    return build_operator_profile(x_player_token, sessions)


@router.get("/{token}")
def get_operator_profile(token: str, db: Session = Depends(get_db)):
    sessions = db.query(GameSession).filter(GameSession.player_token == token).all()
    return build_operator_profile(token, sessions)
