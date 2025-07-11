@echo off
echo [INFO] Ouverture du dossier du projet...
cd /d "C:\Users\charl\Mon Drive\EXTRANET_STREAMLIT"

if not exist "docker-compose.yml" (
    echo [ERREUR] Le fichier docker-compose.yml est introuvable.
    pause
    exit /b
)

echo [INFO] Lancement de Docker Compose avec reconstruction de l'image...
docker compose up --build

pause
