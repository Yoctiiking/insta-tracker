# --- Dockerfile ---
# Cette image contient Python + toutes nos dépendances.
# On part d'une image officielle Python "slim" (légère) plutôt que l'image
# complète, pour garder le container petit et rapide à construire.
FROM python:3.12-slim

# Dossier de travail à l'intérieur du container
WORKDIR /app

# On copie D'ABORD requirements.txt (et pas tout le code) pour profiter
# du cache Docker : si le code change mais pas les dépendances,
# Docker ne réinstalle pas tout à chaque build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Maintenant on copie le reste du code de l'application
COPY app/ ./app/
COPY static/ ./static/

# Le port sur lequel FastAPI (via uvicorn) va écouter à l'intérieur du container
EXPOSE 8000

# Commande lancée au démarrage du container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
