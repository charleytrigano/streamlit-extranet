@echo off
setlocal

set "APP_DIR=C:\Users\charl\Mon Drive\EXTRANET_STREAMLIT"
set "VENV_DIR=%APP_DIR%\venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

cd /d "%APP_DIR%"

REM Créer venv si manquant
if not exist "%VENV_ACTIVATE%" (
    echo [INFO] Création de l'environnement virtuel...
    python -m venv venv
)

REM Vérification
if not exist "%VENV_ACTIVATE%" (
    echo [ERREUR] Le fichier activate.bat est toujours introuvable.
    pause
    exit /b
)

REM Activation du venv
call "%VENV_ACTIVATE%"

REM Installer streamlit si manquant
where streamlit >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installation de streamlit...
    pip install streamlit
)

REM Lancer l'application
streamlit run app.py

pause
endlocal
