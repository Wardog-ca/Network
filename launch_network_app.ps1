# PowerShell script pour lancer Network Team Application
# Version moderne avec interface colorée et gestion d'erreurs avancée

param(
    [switch]$NoWait,
    [switch]$Debug
)

# Configuration des couleurs
$Host.UI.RawUI.WindowTitle = "Network Team - Application Launcher"

function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Show-Banner {
    Clear-Host
    Write-ColorText "========================================" "Green"
    Write-ColorText "   Network Team Application Launcher   " "Cyan"
    Write-ColorText "========================================" "Green"
    Write-Host ""
}

function Test-PythonInstallation {
    $pythonCommands = @("python", "py", "python3")
    
    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                return @{
                    Command = $cmd
                    Version = $version
                    Found = $true
                }
            }
        }
        catch {
            continue
        }
    }
    
    return @{ Found = $false }
}

function Start-Application {
    Show-Banner
    
    # Obtenir le répertoire du script
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $pythonScript = Join-Path $scriptDir "network.py"
    
    # Vérifier si le fichier Python existe
    if (-not (Test-Path $pythonScript)) {
        Write-ColorText "❌ Erreur: Le fichier network.py n'a pas été trouvé!" "Red"
        Write-ColorText "Répertoire attendu: $pythonScript" "Yellow"
        Write-Host ""
        if (-not $NoWait) {
            Read-Host "Appuyez sur Entrée pour continuer"
        }
        exit 1
    }
    
    Write-ColorText "🔍 Vérification de l'installation Python..." "Yellow"
    $pythonInfo = Test-PythonInstallation
    
    if (-not $pythonInfo.Found) {
        Write-ColorText "❌ Erreur: Python n'est pas installé ou non accessible!" "Red"
        Write-Host ""
        Write-ColorText "Solutions possibles:" "Yellow"
        Write-ColorText "1. Installer Python depuis https://python.org" "White"
        Write-ColorText "2. Cocher 'Add Python to PATH' lors de l'installation" "White"
        Write-ColorText "3. Redémarrer l'ordinateur après installation" "White"
        Write-Host ""
        if (-not $NoWait) {
            Read-Host "Appuyez sur Entrée pour continuer"
        }
        exit 1
    }
    
    Write-ColorText "✅ Python détecté: $($pythonInfo.Version)" "Green"
    Write-ColorText "🚀 Lancement de l'application..." "Cyan"
    Write-ColorText "Fichier: $pythonScript" "Gray"
    Write-Host ""
    
    try {
        # Lancer l'application Python
        if ($Debug) {
            Write-ColorText "Mode debug activé - sortie détaillée:" "Magenta"
            & $pythonInfo.Command $pythonScript
        } else {
            & $pythonInfo.Command $pythonScript
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorText "✅ Application fermée normalement." "Green"
        } else {
            Write-Host ""
            Write-ColorText "⚠️  L'application s'est fermée avec une erreur (code: $LASTEXITCODE)" "Red"
            Write-Host ""
            Write-ColorText "Conseils de dépannage:" "Yellow"
            Write-ColorText "- Vérifiez que toutes les dépendances Python sont installées" "White"
            Write-ColorText "- Vérifiez les permissions du dossier" "White"
            Write-ColorText "- Relancez en mode debug: .\launch_network_app.ps1 -Debug" "White"
        }
    }
    catch {
        Write-ColorText "❌ Erreur lors du lancement: $($_.Exception.Message)" "Red"
        if ($Debug) {
            Write-ColorText "Détails de l'erreur:" "Yellow"
            Write-ColorText $_.Exception.ToString() "Gray"
        }
    }
    
    if (-not $NoWait) {
        Write-Host ""
        Read-Host "Appuyez sur Entrée pour fermer"
    }
}

# Point d'entrée principal
Start-Application