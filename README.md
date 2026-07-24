# Insta Tracker

Web app pour repérer les comptes que tu suis sur Instagram mais qui ne te
suivent pas en retour, avec un bouton unfollow en un clic.

## Stack
- **Backend** : FastAPI (Python)
- **Base de données** : SQLite (via SQLAlchemy)
- **Instagram** : instagrapi (récupération des données + actions follow/unfollow)
- **Frontend** : HTML/CSS/JS simple, servi directement par FastAPI
- **Conteneurisation** : Docker + docker-compose

## Mise en route

### 1. Configurer tes identifiants
```bash
cp .env.example .env
# puis édite .env avec ton pseudo/mot de passe Instagram
```

### 2. Construire l'image Docker
```bash
docker compose build
```
Ça lit le `Dockerfile`, installe Python + les dépendances (`requirements.txt`)
dans une image, et la nomme d'après le projet.

### 3. Lancer le container
```bash
docker compose up
```
- Lit `docker-compose.yml`
- Démarre le container `insta-tracker`
- Monte `./data` dans `/app/data` (donc ta base SQLite et ta session
  Instagram persistent même si tu recrées le container)
- Expose le port 8000 → accessible sur http://localhost:8000

Ajoute `-d` (`docker compose up -d`) pour le lancer en arrière-plan.

### 4. Voir les logs (si lancé en arrière-plan)
```bash
docker compose logs -f
```

### 5. Arrêter
```bash
docker compose down
```

### 6. Après une modification du code
Docker ne recharge pas automatiquement le code Python à chaud (pas de
hot-reload configuré ici). Après un changement :
```bash
docker compose up --build
```
Le flag `--build` force la reconstruction de l'image avec ton nouveau code.

## Commandes Docker utiles à connaître
| Commande | Effet |
|---|---|
| `docker ps` | Liste les containers en cours d'exécution |
| `docker compose logs -f` | Suit les logs en direct |
| `docker exec -it insta-tracker bash` | Ouvre un terminal DANS le container |
| `docker compose down -v` | Arrête et supprime aussi les volumes anonymes |
| `docker images` | Liste les images construites localement |

## Sécurité anti-détection Instagram
- Session réutilisée (`data/session.json`) plutôt que reconnexion à chaque fois
- `MAX_ACTIONS_PER_RUN` : plafonne le nombre d'unfollow par exécution
- `ACTION_DELAY_SECONDS` : délai entre deux actions
- Recommandé : teste d'abord sur un compte secondaire avant ton compte principal

## Endpoints API
- `POST /api/sync` — récupère l'état actuel followers/following, sauvegarde un snapshot
- `GET /api/non-mutual` — liste des comptes non-mutuels (dernier snapshot)
- `POST /api/unfollow/{username}` — unfollow un compte précis
- `GET /api/snapshots` — historique des synchronisations
