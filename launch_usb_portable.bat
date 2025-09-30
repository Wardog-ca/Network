@echo off
REM Script batch optimisé pour lancement depuis clé USB
REM Version portable - Network Team Application

title Network Team USB - Portable Application

REM Couleurs pour le terminal
color 0A
echo ==========================================
echo    Network Team - Application Portable   
echo ==========================================
echo.

REM Obtenir le répertoire du script (clé USB)
set "USB_DIR=%~dp0"
set "PYTHON_SCRIPT=%USB_DIR%network.py"

echo [USB] Repertoire de la cle USB: %USB_DIR%
echo [USB] Script Python: %PYTHON_SCRIPT%
echo.

REM Vérifier si le fichier Python existe sur USB
if not exist "%PYTHON_SCRIPT%" (
    echo [ERREUR] Le fichier network.py n'a pas ete trouve sur la cle USB!
    echo Emplacement attendu: %PYTHON_SCRIPT%
    echo.
    echo Assurez-vous que les fichiers suivants sont sur la cle USB:
    echo - network.py
    echo - launch_network_app.bat
    echo - dossier "Network Team" (optionnel)
    echo.
    pause
    exit /b 1
)

REM Créer le dossier Network Team sur USB s'il n'existe pas
if not exist "%USB_DIR%Network Team" (
    echo [USB] Creation du dossier "Network Team" sur la cle USB...
    mkdir "%USB_DIR%Network Team"
    echo [OK] Dossier cree: %USB_DIR%Network Team
    echo.
)

REM Afficher l'espace disponible sur USB
for /f "tokens=3" %%a in ('dir /-c "%USB_DIR%" ^| find "bytes free"') do set "FREE_SPACE=%%a"
echo [INFO] Espace libre sur USB: %FREE_SPACE% bytes
echo.

echo [LANCEMENT] Demarrage de l'application portable...
echo.

REM Essayer Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python detecte - Lancement en mode portable
    echo [INFO] L'application utilisera la cle USB comme dossier de travail
    echo.
    REM Changer vers le répertoire USB pour l'exécution
    cd /d "%USB_DIR%"
    python "%PYTHON_SCRIPT%"
) else (
    REM Essayer py launcher
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Py launcher detecte - Lancement en mode portable
        echo [INFO] L'application utilisera la cle USB comme dossier de travail
        echo.
        cd /d "%USB_DIR%"
        py "%PYTHON_SCRIPT%"
    ) else (
        echo [ERREUR] Python n'est pas installe sur cet ordinateur!
        echo.
        echo Pour utiliser l'application portable:
        echo 1. Installer Python sur l'ordinateur hote
        echo 2. OU utiliser une version Python portable sur USB
        echo 3. OU lancer depuis un ordinateur avec Python
        echo.
        echo Telechargement Python: https://python.org
        echo.
        pause
        exit /b 1
    )
)

REM Vérifier le code de sortie
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] L'application portable s'est fermee avec une erreur
    echo Code d'erreur: %errorlevel%
    echo.
    echo Conseils:
    echo - Verifiez que la cle USB n'est pas protegee en ecriture
    echo - Assurez-vous d'avoir les permissions sur cet ordinateur
    echo - Verifiez l'espace libre sur la cle USB
    echo.
    pause
) else (
    echo.
    echo [OK] Application portable fermee normalement
    echo [INFO] Vos donnees sont sauvegardees sur la cle USB
)

echo.
echo Vous pouvez retirer la cle USB en toute securite
echo.
pause