# CRÉATION D'UN RACCOURCI WINDOWS POUR NETWORK TEAM APPLICATION

## Méthode 1: Raccourci vers le fichier Batch (RECOMMANDÉE)

### Étapes pour créer un raccourci:

1. **Clic droit** sur le fichier `launch_network_app.bat`
2. Sélectionner **"Créer un raccourci"**
3. **Glisser le raccourci** sur le Bureau ou dans le menu Démarrer
4. **Clic droit** sur le raccourci → **"Propriétés"**
5. Dans l'onglet **"Raccourci"**, modifier:
   - **Nom**: `Network Team Application`
   - **Commentaire**: `Lance l'application de gestion réseau`

### Personnalisation avancée du raccourci:

1. **Clic droit** sur le raccourci → **"Propriétés"**
2. Cliquer sur **"Changer d'icône..."**
3. Choisir une icône réseau/ordinateur ou parcourir pour un fichier .ico personnalisé
4. Dans **"Démarrer dans"**, s'assurer que c'est le dossier contenant network.py
5. **Appliquer** et **OK**

---

## Méthode 2: Raccourci PowerShell (AVANCÉE)

### Pour les utilisateurs PowerShell:

1. **Clic droit** sur le fichier `launch_network_app.ps1`
2. Sélectionner **"Créer un raccourci"**
3. **Clic droit** sur le raccourci → **"Propriétés"**
4. Dans **"Cible"**, remplacer par:
   ```
   powershell.exe -ExecutionPolicy Bypass -File "CHEMIN_COMPLET\launch_network_app.ps1"
   ```
5. Remplacer `CHEMIN_COMPLET` par le chemin réel vers votre dossier

---

## Méthode 3: Raccourci Direct Python

### Création manuelle d'un raccourci:

1. **Clic droit** sur le Bureau → **"Nouveau"** → **"Raccourci"**
2. Dans **"Emplacement"**, saisir:
   ```
   python "CHEMIN_COMPLET\network.py"
   ```
3. **Suivant** → Nommer le raccourci: `Network Team App`
4. **Terminer**

### Si Python n'est pas dans le PATH:
```
"C:\Python39\python.exe" "CHEMIN_COMPLET\network.py"
```
(Adapter le chemin Python selon votre installation)

---

## Méthode 4: Ajout au Menu Démarrer

### Pour Windows 10/11:

1. Créer le raccourci avec une des méthodes ci-dessus
2. **Couper** (Ctrl+X) le raccourci
3. Appuyer sur **Win+R**, taper: `shell:programs`
4. **Coller** le raccourci dans ce dossier
5. Le raccourci apparaîtra dans le menu Démarrer

---

## Méthode 5: Raccourci avec Variables d'Environnement

### Création d'un raccourci universel:

1. **Clic droit** sur le Bureau → **"Nouveau"** → **"Raccourci"**
2. **Cible**:
   ```
   cmd /c "cd /d "%~dp0" && launch_network_app.bat"
   ```
3. **Démarrer dans**: Dossier contenant les fichiers
4. **Nom**: `Network Team Application`

---

## Dépannage

### Si le raccourci ne fonctionne pas:

1. **Vérifier que Python est installé**:
   - Ouvrir CMD → taper `python --version`
   - Si erreur: Installer Python depuis python.org

2. **Vérifier les chemins**:
   - S'assurer que tous les fichiers sont dans le même dossier
   - Vérifier les chemins absolus dans les propriétés du raccourci

3. **Permissions**:
   - **Clic droit** sur le dossier → **"Propriétés"** → **"Sécurité"**
   - S'assurer d'avoir les droits de lecture/exécution

4. **Test en ligne de commande**:
   - Ouvrir CMD dans le dossier de l'application
   - Taper: `launch_network_app.bat`
   - Vérifier les messages d'erreur

---

## Options Avancées

### Lancement silencieux (sans fenêtre CMD):
Créer un fichier `.vbs`:

```vbscript
Set objShell = CreateObject("WScript.Shell")
objShell.Run "cmd /c launch_network_app.bat", 0, False
```

### Lancement automatique au démarrage:
1. **Win+R** → `shell:startup`
2. Copier le raccourci dans ce dossier

### Raccourci clavier global:
1. **Clic droit** sur le raccourci → **"Propriétés"**
2. Cliquer dans **"Touche de raccourci"**
3. Appuyer sur la combinaison souhaitée (ex: Ctrl+Alt+N)

---

## Fichiers créés:

- ✅ `launch_network_app.bat` - Script batch principal
- ✅ `launch_network_app.ps1` - Script PowerShell avancé  
- ✅ `SHORTCUT_INSTRUCTIONS.md` - Ce fichier d'instructions

**Recommandation**: Utilisez la **Méthode 1** (fichier .bat) pour la simplicité et la compatibilité.