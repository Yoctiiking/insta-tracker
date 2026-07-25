from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import os

from .database import engine, get_db, Base
from . import models, schemas
from .scraper import get_client, fetch_followers_and_following, compute_non_mutual, unfollow_users

# Crée les tables SQLite si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Insta Tracker")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/sync", response_model=schemas.SyncResult)
def sync(db: Session = Depends(get_db)):
    """
    Se connecte à Instagram, récupère l'état actuel des abonnés/abonnements,
    et sauvegarde un nouveau snapshot en base.
    """
    try:
        cl = get_client()
        followers, following = fetch_followers_and_following(cl)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur Instagram: {e}")

    snapshot = models.Snapshot(
        followers_count=len(followers),
        following_count=len(following),
    )
    db.add(snapshot)
    db.flush()  # pour obtenir snapshot.id avant le commit

    follower_ids = set(followers.keys())
    for uid, user in following.items():
        db.add(models.Relation(
            snapshot_id=snapshot.id,
            username=user.username,
            full_name=user.full_name,
            is_follower=uid in follower_ids,
            is_following=True,
            profile_pic_url=str(user.profile_pic_url) if user.profile_pic_url else None,
        ))
    # Ajoute aussi les followers qui ne sont pas suivis en retour par toi
    following_ids = set(following.keys())
    for uid, user in followers.items():
        if uid not in following_ids:
            db.add(models.Relation(
                snapshot_id=snapshot.id,
                username=user.username,
                full_name=user.full_name,
                is_follower=True,
                is_following=False,
                profile_pic_url=str(user.profile_pic_url) if user.profile_pic_url else None,
            ))

    db.commit()

    non_mutual = compute_non_mutual(followers, following)

    return schemas.SyncResult(
        snapshot_id=snapshot.id,
        followers_count=len(followers),
        following_count=len(following),
        non_mutual_count=len(non_mutual),
    )


@app.get("/api/snapshots", response_model=List[schemas.SnapshotOut])
def list_snapshots(db: Session = Depends(get_db)):
    return db.query(models.Snapshot).order_by(desc(models.Snapshot.created_at)).all()


@app.get("/api/non-mutual", response_model=List[schemas.RelationOut])
def get_non_mutual(db: Session = Depends(get_db)):
    """Retourne, pour le dernier snapshot, les comptes que tu suis mais qui ne te suivent pas."""
    latest = db.query(models.Snapshot).order_by(desc(models.Snapshot.created_at)).first()
    if not latest:
        raise HTTPException(status_code=404, detail="Aucun snapshot. Lance /api/sync d'abord.")

    return (
        db.query(models.Relation)
        .filter(
            models.Relation.snapshot_id == latest.id,
            models.Relation.is_following == True,
            models.Relation.is_follower == False,
        )
        .all()
    )


@app.post("/api/unfollow/{username}")
def unfollow_one(username: str, db: Session = Depends(get_db)):
    """Unfollow un compte précis (bouton 'unfollow' du frontend)."""
    try:
        cl = get_client()
        user_id = cl.user_id_from_username(username)
        unfollow_users(cl, [user_id])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur Instagram: {e}")
    return {"unfollowed": username}


# Sert le frontend statique (index.html, app.js, style.css)
@app.get("/api/proxy-image")
def proxy_image(url: str):
    """
    Récupère une image côté serveur (pas de restriction cross-origin ici,
    contrairement au navigateur) et la renvoie au frontend comme si elle
    venait de notre propre domaine.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Impossible de charger l'image: {e}")
    return Response(content=resp.content, media_type=resp.headers.get("content-type", "image/jpeg"))
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))
