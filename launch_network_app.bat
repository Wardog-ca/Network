@echo off
REM Batch script pour lancer Network Team Application
REM Ce script lance l'application Python avec gestion d'erreurs

title Network Team - Application Launcher

REM Couleurs pour le terminal
echo [32m========================================[0m
echo [36m   Network Team Application Launcher   [0m
echo [32m========================================[0m
echo.

REM Obtenir le répertoire du script
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%network.py"

REM Vérifier si le fichier Python existe
if not exist "%PYTHON_SCRIPT%" (
    echo [31mErreur: Le fichier network.py n'a pas ete trouve![0m
    echo Repertoire attendu: %PYTHON_SCRIPT%
    echo.
    pause
    exit /b 1
)

echo [33mLancement de l'application...[0m
echo Fichier: %PYTHON_SCRIPT%
echo.

REM Essayer Python3 d'abord
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [32mPython detecte, lancement en cours...[0m
    echo.
    python "%PYTHON_SCRIPT%"
) else (
    REM Essayer py launcher
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [32mPy launcher detecte, lancement en cours...[0m
        echo.
        py "%PYTHON_SCRIPT%"
    ) else (
        echo [31mErreur: Python n'est pas installe ou non accessible![0m
        echo.
        echo Solutions possibles:
        echo 1. Installer Python depuis https://python.org
        echo 2. Ajouter Python au PATH Windows
        echo 3. Redemarrer l'ordinateur apres installation
        echo.
        pause
        exit /b 1
    )
)

REM Si l'application se ferme avec une erreur
if %errorlevel% neq 0 (
    echo.
    echo [31mL'application s'est fermee avec une erreur (code: %errorlevel%)[0m
    echo.
    echo Conseils de depannage:
    echo - Verifiez que toutes les dependances Python sont installees
    echo - Executez: pip install tkinter (si necessaire)
    echo - Verifiez les permissions du dossier
    echo.
    pause
) else (
    echo.
    echo [32mApplication fermee normalement.[0m
)

REM Garder la fenêtre ouverte pour voir les messages
echo.
echo Appuyez sur une touche pour fermer...
pause >nul