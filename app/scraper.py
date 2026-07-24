"""
Toute l'interaction avec Instagram passe par ici, via instagrapi.

Points importants pour éviter un ban/challenge Instagram :
- On réutilise une session sauvegardée sur disque (settings.json) plutôt que
  de se reconnecter à chaque fois -> moins suspect qu'un nouveau login répété.
- On ajoute un délai entre chaque action (follow/unfollow).
- On plafonne le nombre d'actions par exécution (MAX_ACTIONS_PER_RUN).
"""
import os
import time
from instagrapi import Client

SESSION_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "session.json")

MAX_ACTIONS_PER_RUN = int(os.getenv("MAX_ACTIONS_PER_RUN", "15"))
ACTION_DELAY_SECONDS = int(os.getenv("ACTION_DELAY_SECONDS", "8"))


def get_client() -> Client:
    """Retourne un client instagrapi connecté, en réutilisant la session si possible."""
    cl = Client()

    username = os.environ["IG_USERNAME"]
    password = os.environ["IG_PASSWORD"]

    if os.path.exists(SESSION_PATH):
        cl.load_settings(SESSION_PATH)
        try:
            cl.login(username, password)
            cl.get_timeline_feed()  # vérifie que la session est toujours valide
        except Exception:
            # Session expirée ou invalide -> reconnexion propre
            cl = Client()
            cl.login(username, password)
            cl.dump_settings(SESSION_PATH)
    else:
        cl.login(username, password)
        cl.dump_settings(SESSION_PATH)

    return cl


def fetch_followers_and_following(cl: Client):
    """Récupère la liste complète des followers et followings du compte connecté."""
    user_id = cl.user_id
    followers = cl.user_followers(user_id)   # dict {user_id: UserShort}
    following = cl.user_following(user_id)
    return followers, following


def compute_non_mutual(followers: dict, following: dict) -> list:
    """
    Retourne la liste des comptes que TU suis mais qui ne te suivent PAS en retour
    (les "non-mutuals" à potentiellement unfollow).
    """
    follower_ids = set(followers.keys())
    non_mutual = [
        user for uid, user in following.items() if uid not in follower_ids
    ]
    return non_mutual


def unfollow_users(cl: Client, user_ids: list) -> list:
    """
    Unfollow une liste d'IDs, avec plafond et délai de sécurité.
    Retourne la liste des IDs effectivement unfollow.
    """
    to_process = user_ids[:MAX_ACTIONS_PER_RUN]
    done = []
    for uid in to_process:
        cl.user_unfollow(uid)
        done.append(uid)
        time.sleep(ACTION_DELAY_SECONDS)
    return done
