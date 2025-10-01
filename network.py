# Version simplifiée de l'application
import os
import platform
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
import logging

SYNC_FOLDER = "Network Team"

# Détecter si l'application est lancée depuis une clé USB
def detect_usb_launch():
    """Détecte si l'application est lancée depuis une clé USB"""
    script_path = Path(__file__).parent.absolute()
    
    # Vérifier si le script est dans un dossier "Network Team" sur USB
    if script_path.name == SYNC_FOLDER:
        return script_path
    
    # Vérifier si on trouve un dossier "Network Team" parent
    current = script_path
    for _ in range(3):  # Chercher 3 niveaux au-dessus
        parent_network_team = current / SYNC_FOLDER
        if parent_network_team.exists():
            return parent_network_team
        current = current.parent
    
    return None

# Déterminer le chemin de travail (USB ou local)
USB_PATH = detect_usb_launch()
if USB_PATH:
    LOCAL_PATH = USB_PATH
    log_location = "USB"
else:
    LOCAL_PATH = Path.home() / SYNC_FOLDER
    log_location = "Local"

LOCAL_PATH.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOCAL_PATH / "network_team.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

LANG = "en"

def set_language(lang):
    global LANG
    LANG = lang
    update_ui_language()

def tr(fr, en):
    return fr if LANG == "fr" else en

def eject_usb():
    usb_dir = find_usb_path()
    if not usb_dir:
        log(tr("Aucune clé USB détectée à éjecter.", "No USB key detected to eject."), level="ERROR")
        return
    try:
        if platform.system() == "Windows":
            drive_letter = os.path.splitdrive(usb_dir)[0]
            log(tr("Veuillez retirer la clé USB", "Please safely remove the USB key") + f" ({drive_letter}).")
        else:
            mount_point = os.path.dirname(usb_dir)
            os.system(f"umount '{mount_point}'")
            log(tr("Clé USB démontée : ", "USB key unmounted: ") + mount_point)
    except Exception as e:
        log(tr("Erreur lors de l'éjection : ", "Error during ejection: ") + str(e), level="ERROR")

def manual_sync():
    log(tr("Synchronisation manuelle demandée...", "Manual sync requested..."))
    sync()

def show_files():
    files = list(LOCAL_PATH.iterdir())
    if not files:
        log(tr("Aucun fichier dans Network Team.", "No files in Network Team."))
    else:
        log(tr("Fichiers dans Network Team :", "Files in Network Team:"))
        for f in files:
            if f.is_dir():
                log(f"[{tr('Dossier', 'Folder')}] {f.name}")
            else:
                dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(f.stat().st_mtime))
                log(f" - {f.name} ({tr('modifié le', 'modified on')} {dt})")

def add_file():
    file_path = filedialog.askopenfilename(title=tr("Sélectionner un fichier à ajouter", "Select a file to add"))
    if file_path:
        dest = LOCAL_PATH / Path(file_path).name
        try:
            shutil.copy2(file_path, dest)
            log(tr("Fichier ajouté : ", "File added: ") + dest.name)
            sync()
        except Exception as e:
            log(tr("Erreur ajout : ", "Error adding: ") + str(e), level="ERROR")

def delete_file():
    files = list(LOCAL_PATH.iterdir())
    if not files:
        log(tr("Aucun fichier à supprimer.", "No file to delete."))
        return
    filenames = [f.name for f in files]
    file_to_delete = simpledialog.askstring(tr("Supprimer fichier/dossier", "Delete file/folder"),
                                            tr("Nom à supprimer :", "Name to delete:") + "\n" + ", ".join(filenames))
    if file_to_delete:
        target = LOCAL_PATH / file_to_delete
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                    log(tr("Dossier supprimé : ", "Folder deleted: ") + file_to_delete)
                else:
                    target.unlink()
                    log(tr("Fichier supprimé : ", "File deleted: ") + file_to_delete)
                sync()
            except Exception as e:
                log(tr("Erreur suppression : ", "Error deleting: ") + str(e), level="ERROR")
        else:
            log(tr("Fichier ou dossier introuvable.", "File or folder not found."))

def get_tools_from_folder():
    """Récupère la liste des outils disponibles dans le dossier Tools"""
    tools_path = LOCAL_PATH / "Tools"
    tools = []
    
    if not tools_path.exists():
        # Créer le dossier Tools s'il n'existe pas
        tools_path.mkdir(exist_ok=True)
        log(tr("Dossier Tools créé dans Network Team", "Tools folder created in Network Team"))
        return tools
    
    try:
        for item in tools_path.iterdir():
            if item.is_file():
                # Vérifier si c'est un fichier exécutable
                file_ext = item.suffix.lower()
                executable_extensions = ['.exe', '.bat', '.cmd', '.sh', '.py', '.jar', '.app']
                
                if file_ext in executable_extensions or item.stat().st_mode & 0o111:  # Vérifier les permissions d'exécution
                    tools.append({
                        'name': item.stem,  # Nom sans extension
                        'path': str(item),
                        'extension': file_ext,
                        'full_name': item.name
                    })
                    
    except Exception as e:
        log(tr("Erreur lors de la lecture du dossier Tools:", "Error reading Tools folder:") + f" {str(e)}", level="ERROR")
    
    return tools

def launch_tool(tool_info):
    """Lance un outil spécifique"""
    tool_path = tool_info['path']
    tool_name = tool_info['name']
    tool_ext = tool_info['extension']
    
    try:
        log(tr("Lancement de l'outil:", "Launching tool:") + f" {tool_name}")
        
        system = platform.system()
        
        if system == "Windows":
            if tool_ext in ['.exe', '.bat', '.cmd']:
                os.system(f'start "" "{tool_path}"')
            elif tool_ext == '.py':
                os.system(f'start python "{tool_path}"')
            elif tool_ext == '.jar':
                os.system(f'start java -jar "{tool_path}"')
            else:
                os.system(f'start "" "{tool_path}"')
                
        elif system == "Darwin":  # macOS
            if tool_ext == '.app':
                os.system(f'open "{tool_path}"')
            elif tool_ext == '.py':
                os.system(f'python3 "{tool_path}" &')
            elif tool_ext == '.jar':
                os.system(f'java -jar "{tool_path}" &')
            elif tool_ext == '.sh':
                os.system(f'chmod +x "{tool_path}" && "{tool_path}" &')
            else:
                os.system(f'open "{tool_path}"')
                
        elif system == "Linux":
            if tool_ext == '.py':
                os.system(f'python3 "{tool_path}" &')
            elif tool_ext == '.jar':
                os.system(f'java -jar "{tool_path}" &')
            elif tool_ext == '.sh':
                os.system(f'chmod +x "{tool_path}" && "{tool_path}" &')
            else:
                # Essayer avec xdg-open
                os.system(f'xdg-open "{tool_path}" &')
        
        log(tr("Outil lancé:", "Tool launched:") + f" {tool_name}")
        
    except Exception as e:
        log(tr("Erreur lors du lancement de l'outil", "Error launching tool") + f" {tool_name}: {str(e)}", level="ERROR")

def show_tools_manager():
    """Affiche le gestionnaire d'outils"""
    tools_win = tk.Toplevel(root)
    tools_win.title(tr("Gestionnaire d'Outils", "Tools Manager"))
    tools_win.geometry("600x400")
    
    # Frame pour les boutons
    button_frame = tk.Frame(tools_win)
    button_frame.pack(pady=10)
    
    # Bouton actualiser
    refresh_btn = tk.Button(button_frame, text=tr("Actualiser", "Refresh"), 
                           command=lambda: refresh_tools_list())
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    # Bouton ouvrir dossier Tools
    open_folder_btn = tk.Button(button_frame, text=tr("Ouvrir dossier Tools", "Open Tools folder"), 
                               command=open_tools_folder)
    open_folder_btn.pack(side=tk.LEFT, padx=5)
    
    # Frame pour la liste des outils
    list_frame = tk.Frame(tools_win)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Listbox avec scrollbar
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    tools_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
    tools_listbox.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=tools_listbox.yview)
    
    # Stockage des informations des outils
    tools_data = []
    
    def refresh_tools_list():
        """Actualise la liste des outils"""
        nonlocal tools_data
        tools_data = get_tools_from_folder()
        
        tools_listbox.delete(0, tk.END)
        
        if not tools_data:
            tools_listbox.insert(tk.END, tr("Aucun outil trouvé dans le dossier Tools", "No tools found in Tools folder"))
            tools_listbox.insert(tk.END, tr("Placez vos outils (.exe, .py, .sh, .jar, etc.) dans:", "Place your tools (.exe, .py, .sh, .jar, etc.) in:"))
            tools_listbox.insert(tk.END, f"  {LOCAL_PATH / 'Tools'}")
        else:
            for i, tool in enumerate(tools_data):
                display_text = f"{tool['name']} ({tool['extension']})"
                tools_listbox.insert(tk.END, display_text)
    
    def on_tool_double_click(event):
        """Lance l'outil sélectionné lors d'un double-clic"""
        selection = tools_listbox.curselection()
        if selection and tools_data:
            index = selection[0]
            if index < len(tools_data):
                launch_tool(tools_data[index])
    
    # Bind double-click event
    tools_listbox.bind('<Double-1>', on_tool_double_click)
    
    # Bouton pour lancer l'outil sélectionné
    launch_frame = tk.Frame(tools_win)
    launch_frame.pack(pady=10)
    
    launch_btn = tk.Button(launch_frame, text=tr("Lancer l'outil sélectionné", "Launch selected tool"),
                          command=lambda: launch_selected_tool())
    launch_btn.pack()
    
    def launch_selected_tool():
        """Lance l'outil actuellement sélectionné"""
        selection = tools_listbox.curselection()
        if selection and tools_data:
            index = selection[0]
            if index < len(tools_data):
                launch_tool(tools_data[index])
        else:
            log(tr("Aucun outil sélectionné", "No tool selected"))
    
    # Actualisation initiale
    refresh_tools_list()

def open_tools_folder():
    """Ouvre le dossier Tools dans l'explorateur de fichiers"""
    tools_path = LOCAL_PATH / "Tools"
    
    # Créer le dossier s'il n'existe pas
    if not tools_path.exists():
        tools_path.mkdir(exist_ok=True)
    
    try:
        system = platform.system()
        if system == "Windows":
            os.system(f'explorer "{tools_path}"')
        elif system == "Darwin":  # macOS
            os.system(f'open "{tools_path}"')
        elif system == "Linux":
            os.system(f'xdg-open "{tools_path}"')
        
        log(tr("Dossier Tools ouvert:", "Tools folder opened:") + f" {tools_path}")
        
    except Exception as e:
        log(tr("Erreur lors de l'ouverture du dossier Tools:", "Error opening Tools folder:") + f" {str(e)}", level="ERROR")

def get_network_interfaces():
    """Récupère toutes les interfaces réseau et leurs adresses IP"""
    import subprocess
    system = platform.system()
    interfaces = {}
    
    try:
        if system == "Linux":
            # Linux - utiliser ip addr show
            output = subprocess.check_output(["ip", "addr", "show"], encoding="utf-8")
            current_interface = None
            
            for line in output.splitlines():
                line = line.strip()
                if line and line[0].isdigit():
                    # Nouvelle interface
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_interface = parts[1].strip()
                        interfaces[current_interface] = {
                            'ipv4': [],
                            'ipv6': [],
                            'status': 'DOWN'
                        }
                        if 'UP' in line:
                            interfaces[current_interface]['status'] = 'UP'
                elif current_interface and 'inet ' in line:
                    # Adresse IPv4
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1].split('/')[0]
                            interfaces[current_interface]['ipv4'].append(ip)
                elif current_interface and 'inet6' in line:
                    # Adresse IPv6
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'inet6' and i + 1 < len(parts):
                            ip = parts[i + 1].split('/')[0]
                            if not ip.startswith('fe80'):  # Ignorer les adresses link-local
                                interfaces[current_interface]['ipv6'].append(ip)
                                
        elif system == "Darwin":
            # macOS - utiliser ifconfig
            output = subprocess.check_output(["ifconfig"], encoding="utf-8")
            current_interface = None
            
            for line in output.splitlines():
                if line and not line.startswith('\t') and ':' in line:
                    # Nouvelle interface
                    current_interface = line.split(':')[0]
                    interfaces[current_interface] = {
                        'ipv4': [],
                        'ipv6': [],
                        'status': 'DOWN'
                    }
                    if 'UP' in line:
                        interfaces[current_interface]['status'] = 'UP'
                elif current_interface and '\tinet ' in line:
                    # Adresse IPv4
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        interfaces[current_interface]['ipv4'].append(parts[1])
                elif current_interface and '\tinet6 ' in line:
                    # Adresse IPv6
                    parts = line.strip().split()
                    if len(parts) >= 2 and not parts[1].startswith('fe80'):
                        interfaces[current_interface]['ipv6'].append(parts[1])
                        
        elif system == "Windows":
            # Windows - utiliser ipconfig
            output = subprocess.check_output(["ipconfig", "/all"], encoding="utf-8", shell=True)
            current_interface = None
            
            for line in output.splitlines():
                line = line.strip()
                if 'adapter' in line.lower() and line.endswith(':'):
                    # Nouvelle interface
                    current_interface = line.replace(':', '').strip()
                    interfaces[current_interface] = {
                        'ipv4': [],
                        'ipv6': [],
                        'status': 'DOWN'
                    }
                elif current_interface and 'IPv4 Address' in line:
                    # Adresse IPv4
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[1].strip().replace('(Preferred)', '')
                        interfaces[current_interface]['ipv4'].append(ip)
                        interfaces[current_interface]['status'] = 'UP'
                elif current_interface and 'IPv6 Address' in line:
                    # Adresse IPv6
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[1].strip().replace('(Preferred)', '')
                        if not ip.startswith('fe80'):
                            interfaces[current_interface]['ipv6'].append(ip)
                            
    except Exception as e:
        log(tr("Erreur lors de la récupération des interfaces:", "Error retrieving interfaces:") + f" {str(e)}", level="ERROR")
    
    return interfaces

def show_network_dashboard():
    """Affiche le dashboard des interfaces réseau avec interface graphique moderne et compact"""
    try:
        log(tr("🔍 Création de la fenêtre dashboard...", "🔍 Creating dashboard window..."))
        dashboard_win = tk.Toplevel(root)
        dashboard_win.title(tr("🌐 Dashboard Réseau", "🌐 Network Dashboard"))
        dashboard_win.geometry("400x500")
        dashboard_win.configure(bg='#f0f0f0')
        
        # Garder au premier plan et positionner à droite
        dashboard_win.attributes('-topmost', True)
        screen_width = dashboard_win.winfo_screenwidth()
        x_pos = screen_width - 420
        dashboard_win.geometry(f"400x500+{x_pos}+50")
        
        # Configurer la grille pour un contrôle total de la position
        dashboard_win.grid_rowconfigure(1, weight=1)
        dashboard_win.grid_columnconfigure(0, weight=1)
        
        # En-tête moderne - ROW 0 (en haut)
        header_frame = tk.Frame(dashboard_win, bg=COLORS['primary'], height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        
        title_label = tk.Label(header_frame, text="🌐 Network Dashboard Pro", 
                              font=("Arial", 16, "bold"), 
                              fg=COLORS['white'], bg=COLORS['primary'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Groupe de boutons dans l'en-tête
        btn_frame = tk.Frame(header_frame, bg=COLORS['primary'])
        btn_frame.pack(side=tk.RIGHT, padx=15, pady=10)
        
        refresh_btn = tk.Button(btn_frame, text="🔄", 
                               font=("Arial", 11), bg=COLORS['info'], fg=COLORS['white'],
                               relief='flat', padx=12, pady=6,
                               command=lambda: refresh_interfaces())
        refresh_btn.pack(side=tk.RIGHT, padx=3)
        
        pin_btn = tk.Button(btn_frame, text="📌", 
                           font=("Arial", 11), bg=COLORS['warning'], fg=COLORS['white'],
                           relief='flat', padx=12, pady=6,
                           command=lambda: dashboard_win.attributes('-topmost', 
                                   not dashboard_win.attributes('-topmost')))
        pin_btn.pack(side=tk.RIGHT, padx=3)
        
        # Frame principal - ROW 1 (en bas, expansible)
        main_frame = tk.Frame(dashboard_win, bg='#f0f0f0')
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Canvas avec scroll
        canvas = tk.Canvas(main_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def create_interface_card(parent, iface_name, iface_data):
            """Crée une carte moderne pour une interface"""
            # Carte avec style moderne
            card_frame = tk.Frame(parent, bg=COLORS['white'], relief='flat', bd=0)
            card_frame.pack(fill=tk.X, pady=4, padx=8)
            
            # Barre colorée sur le côté selon le statut
            status_color = COLORS['success'] if iface_data['status'] == 'UP' else COLORS['danger']
            status_bar = tk.Frame(card_frame, bg=status_color, width=4)
            status_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
            
            # Contenu de la carte
            content_frame = tk.Frame(card_frame, bg=COLORS['white'])
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=12)
            
            # En-tête avec icône et nom
            header_frame = tk.Frame(content_frame, bg=COLORS['white'])
            header_frame.pack(fill=tk.X, pady=(0, 8))
            
            # Icône selon le type avec couleurs
            if 'en' in iface_name.lower():
                icon = "🔌"
                type_color = COLORS['info']
            elif 'bridge' in iface_name.lower():
                icon = "🐳"
                type_color = COLORS['secondary']
            elif 'utun' in iface_name.lower():
                icon = "🔒"
                type_color = COLORS['warning']
            elif 'wlan' in iface_name.lower() or 'wifi' in iface_name.lower():
                icon = "📶"
                type_color = COLORS['success']
            else:
                icon = "🌐"
                type_color = COLORS['dark']
            
            # Nom avec style
            name_frame = tk.Frame(header_frame, bg=COLORS['white'])
            name_frame.pack(side=tk.LEFT)
            
            icon_label = tk.Label(name_frame, text=icon, 
                                 font=("Arial", 14), bg=COLORS['white'])
            icon_label.pack(side=tk.LEFT, padx=(0, 8))
            
            name_label = tk.Label(name_frame, text=iface_name, 
                                 font=("Arial", 12, "bold"), 
                                 fg=type_color, bg=COLORS['white'])
            name_label.pack(side=tk.LEFT)
            
            # Badge de statut moderne
            status_text = "ACTIF" if iface_data['status'] == 'UP' else "INACTIF"
            status_badge = tk.Label(header_frame, text=status_text, 
                                   font=("Arial", 9, "bold"), 
                                   fg=COLORS['white'], bg=status_color,
                                   padx=8, pady=2)
            status_badge.pack(side=tk.RIGHT)
            
            # Informations IP si disponibles
            if iface_data['ipv4']:
                ip_frame = tk.Frame(content_frame, bg=COLORS['white'])
                ip_frame.pack(fill=tk.X, pady=(0, 4))
                
                tk.Label(ip_frame, text="IPv4:", 
                        font=("Arial", 9), fg=COLORS['dark'], bg=COLORS['white']).pack(side=tk.LEFT)
                
                ip_label = tk.Label(ip_frame, text=iface_data['ipv4'][0], 
                                   font=("Arial", 10, "bold"), 
                                   fg=COLORS['info'], bg=COLORS['white'])
                ip_label.pack(side=tk.LEFT, padx=(5, 0))
                
                # Indicateur pour IPs multiples
                if len(iface_data['ipv4']) > 1:
                    multi_badge = tk.Label(ip_frame, text=f"+{len(iface_data['ipv4'])-1}", 
                                          font=("Arial", 8), 
                                          fg=COLORS['white'], bg=COLORS['secondary'],
                                          padx=4, pady=1)
                    multi_badge.pack(side=tk.LEFT, padx=(8, 0))
            
            # Ligne de séparation subtile
            separator = tk.Frame(parent, bg=COLORS['light'], height=1)
            separator.pack(fill=tk.X, padx=20)
        
        def refresh_interfaces():
            """Actualise les interfaces"""
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            interfaces = get_network_interfaces()
            
            # Stats
            stats_frame = tk.Frame(scrollable_frame, bg='white', relief='raised', bd=1)
            stats_frame.pack(fill=tk.X, pady=(0, 5), padx=2)
            
            stats_content = tk.Frame(stats_frame, bg='white')
            stats_content.pack(fill=tk.X, padx=10, pady=8)
            
            # Filtrer interfaces
            filtered = {k: v for k, v in interfaces.items() 
                       if k not in ['lo0'] and not k.startswith(('anpi', 'awdl', 'llw', 'gif', 'stf'))
                       and not (k.startswith('utun') and not v['ipv4'] and not v['ipv6'])}
            
            total = len(filtered)
            active = len([k for k, v in filtered.items() if v['status'] == 'UP'])
            
            stats_label = tk.Label(stats_content, text=f"{active}/{total} actives", 
                                  font=("Arial", 11, "bold"), fg='#27ae60', bg='white')
            stats_label.pack(side=tk.LEFT)
            
            time_label = tk.Label(stats_content, text=time.strftime('%H:%M:%S'), 
                                 font=("Arial", 9), fg='#7f8c8d', bg='white')
            time_label.pack(side=tk.RIGHT)
            
            for iface_name, iface_data in filtered.items():
                create_interface_card(scrollable_frame, iface_name, iface_data)
        
        refresh_interfaces()
        log(tr("✓ Dashboard créé avec succès", "✓ Dashboard created successfully"))
        
    except Exception as e:
        log(tr(f"❌ Erreur création dashboard: {e}", f"❌ Error creating dashboard: {e}"), level="ERROR")
    
    # Taille initiale plus petite, sera ajustée dynamiquement
    dashboard_win.geometry("400x300")
    dashboard_win.configure(bg='#f0f0f0')
    
    # Garder la fenêtre toujours au premier plan
    dashboard_win.attributes('-topmost', True)
    
    # Permettre le redimensionnement avec taille minimum plus petite
    dashboard_win.minsize(350, 250)
    
    # Icône de la fenêtre (si disponible)
    try:
        dashboard_win.iconname("Network Dashboard")
    except:
        pass
    
    # Style et couleurs
    colors = {
        'bg_main': '#f0f0f0',
        'bg_header': '#2c3e50',
        'bg_card': '#ffffff',
        'text_header': '#ffffff',
        'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'success': '#27ae60',
        'danger': '#e74c3c',
        'warning': '#f39c12',
        'info': '#3498db'
    }
    
    # En-tête compact avec titre et boutons
    header_frame = tk.Frame(dashboard_win, bg=colors['bg_header'], height=40)
    header_frame.pack(fill=tk.X, padx=0, pady=0)
    header_frame.pack_propagate(False)
    
    # Titre principal plus compact
    title_label = tk.Label(header_frame, text=tr("🌐 Réseau", "🌐 Network"),
                          font=("Arial", 12, "bold"), fg=colors['text_header'], bg=colors['bg_header'])
    title_label.pack(side=tk.LEFT, padx=10, pady=8)
    
    # Boutons dans l'en-tête plus compacts
    buttons_frame = tk.Frame(header_frame, bg=colors['bg_header'])
    buttons_frame.pack(side=tk.RIGHT, padx=10, pady=5)
    
    # Variable pour contrôler "always on top"
    topmost_enabled = tk.BooleanVar(value=True)
    
    def toggle_topmost():
        """Active/Désactive le mode 'toujours au premier plan'"""
        dashboard_win.attributes('-topmost', topmost_enabled.get())
        pin_btn.config(text="📌" if topmost_enabled.get() else "📍")
    
    # Boutons plus compacts
    pin_btn = tk.Button(buttons_frame, text="📌",
                       font=("Arial", 9, "bold"), bg=colors['warning'], fg='white',
                       relief='flat', padx=8, pady=2,
                       command=lambda: [topmost_enabled.set(not topmost_enabled.get()), toggle_topmost()])
    pin_btn.pack(side=tk.RIGHT, padx=2)
    
    refresh_btn = tk.Button(buttons_frame, text="🔄",
                           font=("Arial", 9, "bold"), bg=colors['info'], fg='white',
                           relief='flat', padx=8, pady=2,
                           command=lambda: refresh_interfaces())
    refresh_btn.pack(side=tk.RIGHT, padx=2)
    
    # Frame principal avec scroll
    main_frame = tk.Frame(dashboard_win, bg=colors['bg_main'])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Canvas et scrollbar pour le contenu
    canvas = tk.Canvas(main_frame, bg=colors['bg_main'], highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=colors['bg_main'])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Variables pour stocker les widgets
    interface_frames = []
    
    def create_interface_card(parent, iface_name, iface_data):
        """Crée une carte visuelle pour une interface réseau"""
        # Frame principal de la carte
        card_frame = tk.Frame(parent, bg=colors['bg_card'], relief='raised', bd=1)
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # En-tête de la carte avec nom et statut
        header_frame = tk.Frame(card_frame, bg=colors['bg_card'])
    # Canvas et scrollbar pour le contenu
    canvas = tk.Canvas(main_frame, bg=colors['bg_main'], highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=colors['bg_main'])
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def create_interface_card(parent, iface_name, iface_data):
        """Crée une carte visuelle compacte pour une interface réseau"""
        # Frame principal de la carte - plus compact
        card_frame = tk.Frame(parent, bg=colors['bg_card'], relief='raised', bd=1)
        card_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # En-tête de la carte avec nom et statut - hauteur réduite
        header_frame = tk.Frame(card_frame, bg=colors['bg_card'])
        header_frame.pack(fill=tk.X, padx=8, pady=(5, 2))
        
        # Choisir l'icône selon le type d'interface
        if 'wlan' in iface_name.lower() or 'wifi' in iface_name.lower() or 'wl' in iface_name.lower():
            type_icon = "📶"  # WiFi
        elif 'eth' in iface_name.lower() or 'enp' in iface_name.lower() or 'ens' in iface_name.lower():
            type_icon = "🔌"  # Ethernet
        elif 'ppp' in iface_name.lower() or 'tun' in iface_name.lower() or 'vpn' in iface_name.lower():
            type_icon = "🔒"  # VPN/Tunnel
        elif 'docker' in iface_name.lower() or 'br-' in iface_name.lower():
            type_icon = "🐳"  # Docker/Bridge
        else:
            type_icon = "🌐"  # Interface générique
        
        status_icon = "🟢" if iface_data['status'] == 'UP' else "🔴"
        
        # Nom d'interface tronqué pour économiser l'espace
        display_name = iface_name[:12] if len(iface_name) > 12 else iface_name
        
        iface_label = tk.Label(header_frame, 
                              text=f"{type_icon} {display_name}",
                              font=("Arial", 10, "bold"), 
                              fg=colors['text_primary'], 
                              bg=colors['bg_card'])
        iface_label.pack(side=tk.LEFT)
        
        # Badge de statut plus petit
        status_color = colors['success'] if iface_data['status'] == 'UP' else colors['danger']
        status_icon = "●" if iface_data['status'] == 'UP' else "○"
        
        status_label = tk.Label(header_frame, 
                               text=status_icon,
                               font=("Arial", 12, "bold"), 
                               fg=status_color, 
                               bg=colors['bg_card'])
        status_label.pack(side=tk.RIGHT)
        
        # Contenu compact
        if iface_data['ipv4']:
            content_frame = tk.Frame(card_frame, bg=colors['bg_card'])
            content_frame.pack(fill=tk.X, padx=8, pady=(0, 5))
            
            # Afficher seulement la première IPv4 pour économiser l'espace
            first_ipv4 = iface_data['ipv4'][0]
            ip_label = tk.Label(content_frame, text=first_ipv4, 
                               font=("Arial", 9), 
                               fg=colors['info'], 
                               bg=colors['bg_card'])
            ip_label.pack(side=tk.LEFT)
            
            # Indicateur s'il y a plusieurs IPs
            if len(iface_data['ipv4']) > 1:
                multi_label = tk.Label(content_frame, text=f"+{len(iface_data['ipv4'])-1}", 
                                      font=("Arial", 8), 
                                      fg=colors['text_secondary'], 
                                      bg=colors['bg_card'])
                multi_label.pack(side=tk.LEFT, padx=(5, 0))
        
        return card_frame

    def refresh_interfaces():
        """Actualise la liste des interfaces avec cartes graphiques compactes"""
        # Supprimer les anciennes cartes
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        # Récupérer les interfaces
        interfaces = get_network_interfaces()
        
        # En-tête compact avec statistiques essentielles
        stats_frame = tk.Frame(scrollable_frame, bg=colors['bg_card'], relief='raised', bd=1)
        stats_frame.pack(fill=tk.X, padx=2, pady=(0, 5))
        
        stats_content = tk.Frame(stats_frame, bg=colors['bg_card'])
        stats_content.pack(fill=tk.X, padx=8, pady=5)
        
        # Compter les interfaces en appliquant les mêmes filtres que l'affichage
        filtered_interfaces = {}
        for k, v in interfaces.items():
            if k in ['lo', 'lo0', 'Loopback']:
                continue
            if k.startswith(('anpi', 'awdl', 'llw', 'gif', 'stf')):
                continue
            if k.startswith('utun') and not v['ipv4'] and not v['ipv6']:
                continue
            filtered_interfaces[k] = v
        
        total_interfaces = len(filtered_interfaces)
        active_interfaces = len([k for k, v in filtered_interfaces.items() if v['status'] == 'UP'])
        
        # Statistiques en une ligne compacte
        stats_text = f"{active_interfaces}/{total_interfaces} " + tr("actives", "active")
        stats_label = tk.Label(stats_content, text=stats_text,
                              font=("Arial", 10, "bold"), 
                              fg=colors['success'], 
                              bg=colors['bg_card'])
        stats_label.pack(side=tk.LEFT)
        
        # Timestamp compact
        time_label = tk.Label(stats_content, 
                             text=time.strftime('%H:%M:%S'),
                             font=("Arial", 9), 
                             fg=colors['text_secondary'], 
                             bg=colors['bg_card'])
        time_label.pack(side=tk.RIGHT)
        
        # Créer les cartes d'interfaces compactes
        for iface_name, iface_data in interfaces.items():
            # Ignorer les interfaces système et loopback
            if iface_name in ['lo', 'lo0', 'Loopback']:
                continue
            # Ignorer les interfaces système macOS moins importantes
            if iface_name.startswith(('anpi', 'awdl', 'llw', 'gif', 'stf')):
                continue
            # Afficher seulement les utun qui ont des IPs (VPN actifs)
            if iface_name.startswith('utun') and not iface_data['ipv4'] and not iface_data['ipv6']:
                continue
            create_interface_card(scrollable_frame, iface_name, iface_data)
        
        # Ajuster la taille de la fenêtre selon le contenu
        dashboard_win.update_idletasks()
        
        # Calculer la hauteur nécessaire
        content_height = scrollable_frame.winfo_reqheight()
        header_height = 40
        padding = 20
        
        # Hauteur optimale (maximum 500px pour éviter débordement écran)
        optimal_height = min(content_height + header_height + padding, 500)
        
        # Largeur optimale basée sur le contenu
        optimal_width = min(max(350, scrollable_frame.winfo_reqwidth() + 50), 450)
        
        # Position dans le coin supérieur droit
        screen_width = dashboard_win.winfo_screenwidth()
        x_pos = screen_width - optimal_width - 50
        
        dashboard_win.geometry(f"{optimal_width}x{optimal_height}+{x_pos}+50")
    # Actualisation initiale
    refresh_interfaces()
    
    # Auto-actualisation toutes les 30 secondes
    def auto_refresh():
        try:
            refresh_interfaces()
            dashboard_win.after(30000, auto_refresh)  # 30 secondes
        except:
            pass  # Fenêtre fermée
    
    dashboard_win.after(30000, auto_refresh)
    
    # Bind mousewheel pour le scroll
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Bind scroll events
    canvas.bind("<MouseWheel>", on_mousewheel)  # Windows
    canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
    canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
    
    # Focus sur la fenêtre pour les événements clavier
    dashboard_win.focus_set()
    
    # Bind clavier pour actualisation (F5)
    dashboard_win.bind("<F5>", lambda e: refresh_interfaces())
    dashboard_win.bind("<Control-r>", lambda e: refresh_interfaces())

def set_ip():
    messagebox.showinfo(tr("IP", "IP"), tr("Fenêtre de configuration IP manuelle ouverte.", "Manual IP configuration window opened."))

def set_ip_device(device):
    win = tk.Toplevel(root)
    win.title(tr("Changer l'adresse IP", "Change IP address"))
    tk.Label(win, text=tr("Interface réseau :", "Network interface:")).pack(pady=5)
    import subprocess
    system = platform.system()
    interfaces = []
    if system == "Linux":
        try:
            output = subprocess.check_output(["ip", "-o", "link", "show"], encoding="utf-8")
            for line in output.splitlines():
                name = line.split(':')[1].strip()
                if name != "lo":
                    interfaces.append(name)
        except Exception:
            interfaces = ["eth0"]
    elif system == "Darwin":
        try:
            output = subprocess.check_output(["networksetup", "-listallhardwareports"], encoding="utf-8")
            for block in output.split("\n\n"):
                if "Device:" in block:
                    for l in block.splitlines():
                        if l.startswith("Device:"):
                            interfaces.append(l.split(":")[1].strip())
        except Exception:
            interfaces = ["en0"]
    elif system == "Windows":
        try:
            output = subprocess.check_output(["netsh", "interface", "show", "interface"], encoding="utf-8")
            for line in output.splitlines():
                if "Connected" in line or "Disconnected" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        interfaces.append(parts[-1])
        except Exception:
            interfaces = ["Ethernet"]
    else:
        interfaces = ["eth0"]

    var_iface = tk.StringVar(value=interfaces[0] if interfaces else "")
    tk.OptionMenu(win, var_iface, *interfaces).pack(pady=5)

    def apply_ip():
        iface = var_iface.get().strip()
        ip = DEVICE_IPS[device]
        system = platform.system()
        cmd = None
        if not iface:
            log(tr("Interface réseau non spécifiée.", "Network interface not specified."))
            return
        if system == "Windows":
            cmd = f'netsh interface ip set address name="{iface}" static {ip} 255.255.255.0 192.168.1.1'
        elif system == "Linux":
            cmd = f"sudo ip addr flush dev {iface} && sudo ip addr add {ip}/24 dev {iface} && sudo ip route add default via 192.168.1.1"
        elif system == "Darwin":
            cmd = f"sudo networksetup -setmanual {iface} {ip} 255.255.255.0 192.168.1.1"
        if cmd:
            result = os.system(cmd)
            if result == 0:
                log(tr("Configuration appliquée sur", "Configuration applied on") + f" {iface}")
            else:
                log(tr("Erreur lors de l'exécution de la commande pour l'interface", "Error executing command for interface") + f" '{iface}'.")
        else:
            log(tr("Système non supporté.", "Unsupported system."))
        win.destroy()

    tk.Button(win, text=tr("Appliquer", "Apply"), command=apply_ip).pack(pady=10)

def set_ip_manual():
    win = tk.Toplevel(root)
    win.title(tr("Configuration IP manuelle", "Manual IP configuration"))
    tk.Label(win, text=tr("Interface réseau :", "Network interface:")).pack(pady=5)
    import subprocess
    system = platform.system()
    interfaces = []
    if system == "Linux":
        try:
            output = subprocess.check_output(["ip", "-o", "link", "show"], encoding="utf-8")
            for line in output.splitlines():
                name = line.split(':')[1].strip()
                if name != "lo":
                    interfaces.append(name)
        except Exception:
            interfaces = ["eth0"]
    elif system == "Darwin":
        try:
            output = subprocess.check_output(["networksetup", "-listallhardwareports"], encoding="utf-8")
            for block in output.split("\n\n"):
                if "Device:" in block:
                    for l in block.splitlines():
                        if l.startswith("Device:"):
                            interfaces.append(l.split(":")[1].strip())
        except Exception:
            interfaces = ["en0"]
    elif system == "Windows":
        try:
            output = subprocess.check_output(["netsh", "interface", "show", "interface"], encoding="utf-8")
            for line in output.splitlines():
                if "Connected" in line or "Disconnected" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        interfaces.append(parts[-1])
        except Exception:
            interfaces = ["Ethernet"]
    else:
        interfaces = ["eth0"]

    var_iface = tk.StringVar(value=interfaces[0] if interfaces else "")
    tk.OptionMenu(win, var_iface, *interfaces).pack(pady=5)

    # Option pour choisir entre IP statique et DHCP
    tk.Label(win, text=tr("Type de configuration :", "Configuration type:")).pack(pady=5)
    config_type = tk.StringVar(value="static")
    tk.Radiobutton(win, text=tr("IP Statique", "Static IP"), variable=config_type, value="static").pack()
    tk.Radiobutton(win, text="DHCP", variable=config_type, value="dhcp").pack()

    tk.Label(win, text=tr("Adresse IP :", "IP address:")).pack(pady=5)
    ip_entry = tk.Entry(win)
    ip_entry.pack(pady=5)
    ip_entry.insert(0, "192.168.1.100")

    def apply_ip():
        iface = var_iface.get().strip()
        system = platform.system()
        cmd = None
        
        if not iface:
            log(tr("Interface réseau non spécifiée.", "Network interface not specified."))
            return
            
        if config_type.get() == "dhcp":
            # Configuration DHCP
            if system == "Windows":
                cmd = f'netsh interface ip set address name="{iface}" dhcp'
                result = os.system(cmd)
                if result == 0:
                    log(tr("Configuration DHCP appliquée sur", "DHCP configuration applied on") + f" {iface}")
                else:
                    log(tr("Erreur lors de l'application du DHCP sur l'interface", "Error applying DHCP on interface") + f" '{iface}'.")
            elif system == "Linux":
                # Détecter la distribution Linux pour optimiser l'approche
                import subprocess
                distro = ""
                try:
                    # Essayer de détecter la distribution
                    if os.path.exists("/etc/redhat-release"):
                        with open("/etc/redhat-release", "r") as f:
                            distro = f.read().lower()
                    elif os.path.exists("/etc/os-release"):
                        with open("/etc/os-release", "r") as f:
                            content = f.read().lower()
                            if "ubuntu" in content or "debian" in content:
                                distro = "ubuntu"
                            elif "red hat" in content or "rhel" in content or "centos" in content:
                                distro = "rhel"
                except:
                    distro = ""
                
                log(tr("Configuration DHCP en cours sur", "Configuring DHCP on") + f" {iface}...")
                
                # Approche optimisée selon la distribution
                if "rhel" in distro or "red hat" in distro or "centos" in distro:
                    # RHEL 8/9 - NetworkManager est le standard
                    log(tr("Distribution RHEL détectée, utilisation de NetworkManager...", "RHEL distribution detected, using NetworkManager..."))
                    
                    # Méthode 1: nmcli (NetworkManager) - Standard RHEL 8
                    nm_cmd = f"sudo nmcli con mod {iface} ipv4.method auto && sudo nmcli con down {iface} && sudo nmcli con up {iface}"
                    result1 = os.system(nm_cmd)
                    
                    if result1 != 0:
                        # Méthode 2: Créer une nouvelle connexion NetworkManager
                        log(tr("Création d'une nouvelle connexion NetworkManager...", "Creating new NetworkManager connection..."))
                        delete_cmd = f"sudo nmcli con delete {iface} 2>/dev/null || true"
                        os.system(delete_cmd)
                        create_cmd = f"sudo nmcli con add type ethernet con-name {iface} ifname {iface} && sudo nmcli con mod {iface} ipv4.method auto && sudo nmcli con up {iface}"
                        result2 = os.system(create_cmd)
                        
                        if result2 == 0:
                            log(tr("Configuration DHCP appliquée via NetworkManager (nouvelle connexion) sur", "DHCP configuration applied via NetworkManager (new connection) on") + f" {iface}")
                        else:
                            # Méthode 3: dhclient en dernier recours
                            log(tr("Tentative avec dhclient...", "Trying with dhclient..."))
                            release_cmd = f"sudo ip addr flush dev {iface}"
                            os.system(release_cmd)
                            dhcp_cmd = f"sudo dhclient -r {iface} 2>/dev/null || true && sudo dhclient {iface}"
                            result3 = os.system(dhcp_cmd)
                            
                            if result3 == 0:
                                log(tr("Configuration DHCP appliquée via dhclient sur", "DHCP configuration applied via dhclient on") + f" {iface}")
                            else:
                                log(tr("Erreur: Toutes les méthodes DHCP ont échoué sur", "Error: All DHCP methods failed on") + f" {iface}", level="ERROR")
                    else:
                        log(tr("Configuration DHCP appliquée via NetworkManager sur", "DHCP configuration applied via NetworkManager on") + f" {iface}")
                        
                else:
                    # Ubuntu/Debian - Détection de version pour Ubuntu 25.04+
                    ubuntu_version = ""
                    try:
                        with open("/etc/os-release", "r") as f:
                            content = f.read()
                            for line in content.splitlines():
                                if line.startswith("VERSION_ID="):
                                    ubuntu_version = line.split("=")[1].strip('"')
                                    break
                    except:
                        ubuntu_version = ""
                    
                    log(tr("Distribution Ubuntu/Debian détectée", "Ubuntu/Debian distribution detected") + f" (version: {ubuntu_version})...")
                    
                    # Pour Ubuntu 25.04+, NetworkManager est souvent prioritaire
                    if ubuntu_version and float(ubuntu_version.split('.')[0]) >= 25:
                        log(tr("Ubuntu 25.04+ détecté, priorité à NetworkManager...", "Ubuntu 25.04+ detected, NetworkManager priority..."))
                        
                        # Méthode 1: systemd-networkd avec network-online (Ubuntu 25.04+ moderne)
                        log(tr("Tentative avec systemd-networkd et network-online...", "Trying with systemd-networkd and network-online..."))
                        
                        # Créer la configuration systemd-networkd
                        networkd_config = f"""[Match]
Name={iface}

[Network]
DHCP=ipv4
LinkLocalAddressing=ipv6

[DHCP]
RouteMetric=100
UseMTU=true"""
                        
                        networkd_file = f"/tmp/25-{iface}.network"
                        try:
                            with open(networkd_file, "w") as f:
                                f.write(networkd_config)
                            
                            # Appliquer la configuration systemd-networkd
                            networkd_cmd = f"""sudo cp {networkd_file} /etc/systemd/network/ && 
                                             sudo systemctl enable systemd-networkd && 
                                             sudo systemctl restart systemd-networkd && 
                                             sudo systemctl restart systemd-networkd-wait-online"""
                            
                            result1 = os.system(networkd_cmd.replace('\n', ''))
                            os.remove(networkd_file)
                            
                            if result1 == 0:
                                # Attendre que network-online soit actif
                                wait_cmd = "sudo systemctl is-active --wait network-online.target"
                                os.system(wait_cmd)
                                log(tr("Configuration DHCP appliquée via systemd-networkd sur", "DHCP configuration applied via systemd-networkd on") + f" {iface}")
                            
                        except Exception as e:
                            log(tr("Erreur systemd-networkd:", "systemd-networkd error:") + f" {str(e)}", level="ERROR")
                            result1 = 1
                        
                        if result1 != 0:
                            # Méthode 2: NetworkManager (fallback)
                            log(tr("Tentative avec NetworkManager...", "Trying with NetworkManager..."))
                            
                            # S'assurer que l'interface est gérée par NetworkManager
                            unmanaged_cmd = f"sudo nmcli dev set {iface} managed yes"
                            os.system(unmanaged_cmd)
                            
                            # Supprimer les connexions existantes qui pourraient causer des conflits
                            cleanup_cmd = f"sudo nmcli con show | grep {iface} | awk '{{print $1}}' | xargs -r sudo nmcli con delete"
                            os.system(cleanup_cmd)
                            
                            # Créer une nouvelle connexion DHCP
                            nm_cmd = f"sudo nmcli con add type ethernet con-name 'dhcp-{iface}' ifname {iface} && sudo nmcli con mod 'dhcp-{iface}' ipv4.method auto && sudo nmcli con up 'dhcp-{iface}'"
                            result1 = os.system(nm_cmd)
                        
                        if result1 != 0:
                            # Méthode 3: Netplan avec network-online.target
                            log(tr("Tentative avec Netplan et network-online.target...", "Trying with Netplan and network-online.target..."))
                            
                            netplan_config = f"""network:
  version: 2
  renderer: networkd
  ethernets:
    {iface}:
      dhcp4: true
      dhcp6: false
      dhcp4-overrides:
        use-routes: true
        use-dns: true"""
                            
                            # Créer un fichier de configuration temporaire
                            config_file = f"/tmp/99-{iface}-dhcp.yaml"
                            try:
                                with open(config_file, "w") as f:
                                    f.write(netplan_config)
                                
                                # Copier la configuration et appliquer avec network-online
                                copy_cmd = f"""sudo cp {config_file} /etc/netplan/ && 
                                             sudo netplan apply && 
                                             sudo systemctl restart systemd-networkd-wait-online && 
                                             sudo systemctl --wait is-system-running"""
                                result2 = os.system(copy_cmd.replace('\n', ''))
                                os.remove(config_file)  # Nettoyer le fichier temporaire
                                
                                if result2 != 0:
                                    # Méthode 3: systemd-networkd (Ubuntu moderne)
                                    log(tr("Tentative avec systemd-networkd...", "Trying with systemd-networkd..."))
                                    
                                    networkd_config = f"""[Match]
Name={iface}

[Network]
DHCP=ipv4"""
                                    
                                    networkd_file = f"/tmp/25-{iface}.network"
                                    try:
                                        with open(networkd_file, "w") as f:
                                            f.write(networkd_config)
                                        
                                        networkd_cmd = f"sudo cp {networkd_file} /etc/systemd/network/ && sudo systemctl restart systemd-networkd"
                                        result3 = os.system(networkd_cmd)
                                        os.remove(networkd_file)
                                        
                                        if result3 == 0:
                                            log(tr("Configuration DHCP appliquée via systemd-networkd sur", "DHCP configuration applied via systemd-networkd on") + f" {iface}")
                                        else:
                                            # Méthode 4: dhclient en dernier recours
                                            log(tr("Tentative avec dhclient (méthode de secours)...", "Trying with dhclient (fallback method)..."))
                                            release_cmd = f"sudo ip addr flush dev {iface} && sudo ip link set {iface} down && sudo ip link set {iface} up"
                                            os.system(release_cmd)
                                            dhcp_cmd = f"sudo dhclient -v {iface}"
                                            result4 = os.system(dhcp_cmd)
                                            
                                            if result4 == 0:
                                                log(tr("Configuration DHCP appliquée via dhclient sur", "DHCP configuration applied via dhclient on") + f" {iface}")
                                            else:
                                                log(tr("Erreur: Toutes les méthodes DHCP ont échoué sur", "Error: All DHCP methods failed on") + f" {iface}", level="ERROR")
                                    except Exception as e:
                                        log(tr("Erreur systemd-networkd:", "systemd-networkd error:") + f" {str(e)}", level="ERROR")
                                        result3 = 1
                                        
                                else:
                                    log(tr("Configuration DHCP appliquée via Netplan (fichier) sur", "DHCP configuration applied via Netplan (file) on") + f" {iface}")
                                    
                            except Exception as e:
                                log(tr("Erreur Netplan:", "Netplan error:") + f" {str(e)}", level="ERROR")
                                result2 = 1
                        else:
                            log(tr("Configuration DHCP appliquée via NetworkManager sur", "DHCP configuration applied via NetworkManager on") + f" {iface}")
                    
                    else:
                        # Ubuntu < 25.04 - Méthode classique
                        log(tr("Ubuntu classique, utilisation de Netplan puis NetworkManager...", "Classic Ubuntu, using Netplan then NetworkManager..."))
                        
                        # Méthode 1: Netplan (Ubuntu moderne)
                        netplan_cmd = f"sudo netplan set ethernets.{iface}.dhcp4=true && sudo netplan apply"
                        result1 = os.system(netplan_cmd)
                        
                        if result1 != 0:
                            # Méthode 2: NetworkManager
                            log(tr("Tentative avec NetworkManager...", "Trying with NetworkManager..."))
                            nm_cmd = f"sudo nmcli con mod {iface} ipv4.method auto && sudo nmcli con up {iface}"
                            result2 = os.system(nm_cmd)
                            
                            if result2 != 0:
                                # Méthode 3: dhclient classique
                                log(tr("Tentative avec dhclient...", "Trying with dhclient..."))
                                release_cmd = f"sudo ip addr flush dev {iface}"
                                os.system(release_cmd)
                                dhcp_cmd = f"sudo dhclient -r {iface} && sudo dhclient {iface}"
                                result3 = os.system(dhcp_cmd)
                                
                                if result3 == 0:
                                    log(tr("Configuration DHCP appliquée via dhclient sur", "DHCP configuration applied via dhclient on") + f" {iface}")
                                else:
                                    log(tr("Erreur: Toutes les méthodes DHCP ont échoué sur", "Error: All DHCP methods failed on") + f" {iface}", level="ERROR")
                            else:
                                log(tr("Configuration DHCP appliquée via NetworkManager sur", "DHCP configuration applied via NetworkManager on") + f" {iface}")
                        else:
                            log(tr("Configuration DHCP appliquée via Netplan sur", "DHCP configuration applied via Netplan on") + f" {iface}")
                    
            elif system == "Darwin":
                cmd = f"sudo networksetup -setdhcp {iface}"
                result = os.system(cmd)
                if result == 0:
                    log(tr("Configuration DHCP appliquée sur", "DHCP configuration applied on") + f" {iface}")
                else:
                    log(tr("Erreur lors de l'application du DHCP sur l'interface", "Error applying DHCP on interface") + f" '{iface}'.")
            else:
                log(tr("Système non supporté.", "Unsupported system."))
        else:
            # Configuration IP statique
            ip = ip_entry.get().strip()
            if not ip:
                log(tr("Adresse IP non spécifiée.", "IP address not specified."))
                return
                
            if system == "Windows":
                cmd = f'netsh interface ip set address name="{iface}" static {ip} 255.255.255.0 192.168.1.1'
            elif system == "Linux":
                cmd = f"sudo ip addr flush dev {iface} && sudo ip addr add {ip}/24 dev {iface} && sudo ip route add default via 192.168.1.1"
            elif system == "Darwin":
                cmd = f"sudo networksetup -setmanual {iface} {ip} 255.255.255.0 192.168.1.1"
            
            if cmd:
                result = os.system(cmd)
                if result == 0:
                    log(tr("Configuration IP statique appliquée sur", "Static IP configuration applied on") + f" {iface}")
                else:
                    log(tr("Erreur lors de l'exécution de la commande pour l'interface", "Error executing command for interface") + f" '{iface}'.")
            else:
                log(tr("Système non supporté.", "Unsupported system."))
        
        win.destroy()

    tk.Button(win, text=tr("Appliquer", "Apply"), command=apply_ip).pack(pady=10)

def find_usb_path():
    if platform.system() == "Windows":
        try:
            import psutil
            for part in psutil.disk_partitions():
                if "removable" in part.opts:
                    candidate = os.path.join(part.mountpoint, SYNC_FOLDER)
                    if os.path.exists(candidate):
                        return candidate
        except ImportError:
            pass
    else:
        media_path = f"/media/{os.getlogin()}"
        if os.path.exists(media_path):
            for d in os.listdir(media_path):
                candidate = os.path.join(media_path, d, SYNC_FOLDER)
                if os.path.exists(candidate):
                    return candidate
    return None

def get_latest(src, dst):
    def latest_mtime(path):
        if not os.path.exists(path):
            return 0
        mtimes = []
        for root, _, files in os.walk(path):
            for f in files:
                mtimes.append(os.path.getmtime(os.path.join(root, f)))
        return max(mtimes) if mtimes else 0
    src_time = latest_mtime(src)
    dst_time = latest_mtime(dst)
    if src_time > dst_time: return "SRC"
    elif dst_time > src_time: return "DST"
    else: return "EQUAL"

def log(msg, level="INFO"):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_text.configure(state='normal')
    log_text.insert(tk.END, f"{timestamp} [{level}] {msg}\n")
    log_text.see(tk.END)
    log_text.configure(state='disabled')
    if level == "ERROR":
        logging.error(msg)
    else:
        logging.info(msg)

def sync():
    usb_dir = find_usb_path()
    if not usb_dir:
        log(tr("Aucune clé USB avec dossier", "No USB key with folder") + f" '{SYNC_FOLDER}' " + tr("détectée.", "detected."), level="ERROR")
        return False

    # --- Synchronisation Laptop → USB : suppression ---
    for root, dirs, files in os.walk(usb_dir, topdown=False):
        rel_root = os.path.relpath(root, usb_dir)
        local_root = os.path.join(str(LOCAL_PATH), rel_root) if rel_root != '.' else str(LOCAL_PATH)
        for f in files:
            usb_file = os.path.join(root, f)
            local_file = os.path.join(local_root, f)
            if not os.path.exists(local_file):
                try:
                    os.remove(usb_file)
                    log(tr("Supprimé sur USB : ", "Deleted on USB: ") + os.path.relpath(usb_file, usb_dir))
                except Exception as e:
                    log(tr("Erreur suppression USB : ", "Error deleting on USB: ") + str(e), level="ERROR")
        for d in dirs:
            usb_subdir = os.path.join(root, d)
            local_subdir = os.path.join(local_root, d)
            if not os.path.exists(local_subdir):
                try:
                    shutil.rmtree(usb_subdir)
                    log(tr("Dossier supprimé sur USB : ", "Folder deleted on USB: ") + os.path.relpath(usb_subdir, usb_dir))
                except Exception as e:
                    log(tr("Erreur suppression dossier USB : ", "Error deleting folder on USB: ") + str(e), level="ERROR")

    # --- Synchronisation Laptop → USB : ajout/modif ---
    for root, dirs, _ in os.walk(str(LOCAL_PATH)):
        for d in dirs:
            src_dir = os.path.join(root, d)
            rel_path = os.path.relpath(src_dir, str(LOCAL_PATH))
            dst_dir = os.path.join(usb_dir, rel_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)

    files_to_usb = []
    for root, _, file_names in os.walk(str(LOCAL_PATH)):
        for f in file_names:
            src_file = os.path.join(root, f)
            rel_path = os.path.relpath(src_file, str(LOCAL_PATH))
            dst_file = os.path.join(usb_dir, rel_path)
            if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                files_to_usb.append((src_file, dst_file, rel_path))
    if files_to_usb:
        log(tr("Laptop → USB : fichiers à synchroniser :", "Laptop → USB: files to sync:"))
        for _, _, rel_path in files_to_usb:
            log(f"  - {rel_path}")
        for src_file, dst_file, _ in files_to_usb:
            shutil.copy2(src_file, dst_file)
        log(tr("Synchronisation Laptop → USB terminée", "Laptop → USB sync completed"))
    else:
        log(tr("Laptop → USB : aucun fichier à synchroniser.", "Laptop → USB: no files to sync."))

    # --- Synchronisation USB → Laptop : suppression ---
    for root, dirs, files in os.walk(str(LOCAL_PATH), topdown=False):
        rel_root = os.path.relpath(root, str(LOCAL_PATH))
        usb_root = os.path.join(usb_dir, rel_root) if rel_root != '.' else usb_dir
        for f in files:
            local_file = os.path.join(root, f)
            usb_file = os.path.join(usb_root, f)
            if not os.path.exists(usb_file):
                try:
                    os.remove(local_file)
                    log(tr("Supprimé en local : ", "Deleted locally: ") + os.path.relpath(local_file, str(LOCAL_PATH)))
                except Exception as e:
                    log(tr("Erreur suppression locale : ", "Error deleting locally: ") + str(e), level="ERROR")
        for d in dirs:
            local_subdir = os.path.join(root, d)
            usb_subdir = os.path.join(usb_root, d)
            if not os.path.exists(usb_subdir):
                try:
                    shutil.rmtree(local_subdir)
                    log(tr("Dossier supprimé en local : ", "Folder deleted locally: ") + os.path.relpath(local_subdir, str(LOCAL_PATH)))
                except Exception as e:
                    log(tr("Erreur suppression dossier locale : ", "Error deleting folder locally: ") + str(e), level="ERROR")

    # --- Synchronisation USB → Laptop : ajout/modif ---
    for root, dirs, _ in os.walk(usb_dir):
        for d in dirs:
            src_dir = os.path.join(root, d)
            rel_path = os.path.relpath(src_dir, usb_dir)
            dst_dir = os.path.join(str(LOCAL_PATH), rel_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)

    files_to_local = []
    for root, _, file_names in os.walk(usb_dir):
        for f in file_names:
            src_file = os.path.join(root, f)
            rel_path = os.path.relpath(src_file, usb_dir)
            dst_file = os.path.join(str(LOCAL_PATH), rel_path)
            if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                files_to_local.append((src_file, dst_file, rel_path))
    if files_to_local:
        log(tr("USB → Laptop : fichiers à synchroniser :", "USB → Laptop: files to sync:"))
        for _, _, rel_path in files_to_local:
            log(f"  - {rel_path}")
        for src_file, dst_file, _ in files_to_local:
            shutil.copy2(src_file, dst_file)
        log(tr("Synchronisation USB → Laptop terminée", "USB → Laptop sync completed"))
    else:
        log(tr("USB → Laptop : aucun fichier à synchroniser.", "USB → Laptop: no files to sync."))

    return True

def auto_sync():
    while True:
        sync()
        time.sleep(180)  # 3 minutes

# Liste des équipements et IP associées
DEVICE_IPS = {
    "Switch Cisco": "192.168.1.10",
    "Firewall Palo Alto": "192.168.1.20",
    "AP Ubiquiti": "192.168.1.30"
}

root = tk.Tk()
root.title("🌐 Network Team Professional")
root.geometry("800x600")

# Couleurs modernes
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e', 
    'success': '#27ae60',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#3498db',
    'light': '#ecf0f1',
    'dark': '#2c3e50',
    'white': '#ffffff'
}

# Style moderne pour la fenêtre
root.configure(bg=COLORS['light'])

# Positionner la fenêtre principale à gauche pour laisser la place au dashboard
root.geometry("800x600+50+50")

# Création des menus AVANT les autres widgets
menubar = tk.Menu(root, bg=COLORS['primary'], fg=COLORS['white'])

# Language menu
menu_lang = tk.Menu(menubar, tearoff=0)
menu_lang.add_command(label="Français", command=lambda: set_language("fr"))
menu_lang.add_command(label="English", command=lambda: set_language("en"))
menubar.add_cascade(label="Langue / Language", menu=menu_lang)

# Network/IP management menu
menu_network = tk.Menu(menubar, tearoff=0)
menu_network.add_command(label=tr("Dashboard Réseau", "Network Dashboard"), command=show_network_dashboard)
menu_network.add_separator()
for device in DEVICE_IPS:
    menu_network.add_command(
        label=f"{device} ({DEVICE_IPS[device]})",
        command=lambda dev=device: set_ip_device(dev)
    )
menu_network.add_command(label=tr("Manuel", "Manual"), command=set_ip_manual)
menubar.add_cascade(label=tr("Réseau", "Network"), menu=menu_network)

# File management menu
menu_file = tk.Menu(menubar, tearoff=0)
menu_file.add_command(label=tr("Afficher fichiers", "Show files"), command=show_files)
menu_file.add_command(label=tr("Ajouter fichier", "Add file"), command=add_file)
menu_file.add_command(label=tr("Supprimer fichier", "Delete file"), command=delete_file)
menubar.add_cascade(label=tr("Gestion fichiers", "File Management / Gestion fichiers"), menu=menu_file)

# Tools menu
menu_tools = tk.Menu(menubar, tearoff=0)
menu_tools.add_command(label=tr("Gestionnaire d'Outils", "Tools Manager"), command=show_tools_manager)
menu_tools.add_command(label=tr("Ouvrir dossier Tools", "Open Tools folder"), command=open_tools_folder)
menu_tools.add_separator()

# Ajouter dynamiquement les outils disponibles
def populate_tools_menu():
    """Remplit le menu outils avec les outils disponibles"""
    # Supprimer les anciens outils du menu (après le séparateur)
    try:
        # Compter les éléments fixes (Gestionnaire, Ouvrir dossier, séparateur)
        fixed_items = 3
        menu_size = menu_tools.index(tk.END)
        if menu_size is not None:
            for i in range(menu_size, fixed_items - 1, -1):
                try:
                    menu_tools.delete(i)
                except:
                    break
    except:
        pass
    
    # Ajouter les outils disponibles
    tools = get_tools_from_folder()
    if tools:
        for tool in tools[:10]:  # Limiter à 10 outils pour éviter un menu trop long
            menu_tools.add_command(
                label=f"{tool['name']} ({tool['extension']})",
                command=lambda t=tool: launch_tool(t)
            )
    else:
        menu_tools.add_command(
            label=tr("Aucun outil disponible", "No tools available"),
            state='disabled'
        )

# Peupler le menu outils au démarrage
populate_tools_menu()

menubar.add_cascade(label=tr("Outils", "Tools"), menu=menu_tools)

# Sync & USB menu
menu_sync = tk.Menu(menubar, tearoff=0)
menu_sync.add_command(label=tr("Sync", "Sync"), command=manual_sync)
menu_sync.add_command(label=tr("Ejecter USB", "Eject USB"), command=eject_usb)
menubar.add_cascade(label=tr("Synchronisation / USB", "Sync / USB"), menu=menu_sync)

# Configurer le menu sur la fenêtre AVANT d'ajouter d'autres widgets
root.config(menu=menubar)

# Interface principale moderne avec sections
main_container = tk.Frame(root, bg=COLORS['light'])
main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

# En-tête avec titre et informations
header_frame = tk.Frame(main_container, bg=COLORS['primary'], height=80)
header_frame.pack(fill=tk.X, pady=(0, 15))
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="🌐 Network Team Professional", 
                      font=("Arial", 18, "bold"), 
                      fg=COLORS['white'], bg=COLORS['primary'])
title_label.pack(side=tk.LEFT, padx=20, pady=25)

status_label = tk.Label(header_frame, text="🟢 Ready", 
                       font=("Arial", 12), 
                       fg=COLORS['success'], bg=COLORS['primary'])
status_label.pack(side=tk.RIGHT, padx=20, pady=25)

# Section des outils rapides
tools_frame = tk.LabelFrame(main_container, text="🛠️ Outils Rapides", 
                           font=("Arial", 12, "bold"),
                           bg=COLORS['light'], fg=COLORS['dark'],
                           padx=10, pady=10)
tools_frame.pack(fill=tk.X, pady=(0, 15))

# Boutons d'outils dans une grille
tools_grid = tk.Frame(tools_frame, bg=COLORS['light'])
tools_grid.pack(fill=tk.X)

# Section des logs
log_frame = tk.LabelFrame(main_container, text="📝 Journal d'activité", 
                         font=("Arial", 12, "bold"),
                         bg=COLORS['light'], fg=COLORS['dark'],
                         padx=10, pady=10)
log_frame.pack(fill=tk.BOTH, expand=True)

log_text = tk.Text(log_frame, height=12, state='disabled',
                  bg=COLORS['white'], fg=COLORS['dark'],
                  font=("Consolas", 10), relief='flat',
                  wrap=tk.WORD)
log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Scrollbar pour les logs
log_scrollbar = tk.Scrollbar(log_text)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.config(yscrollcommand=log_scrollbar.set)
log_scrollbar.config(command=log_text.yview)



def create_professional_tools():
    """Crée les boutons pour les outils professionnels"""
    
    # Outils réseau professionnels
    tools_data = [
        {
            'name': 'Wireshark',
            'icon': '🦈',
            'description': 'Analyseur de protocoles réseau',
            'command': ['wireshark'] if platform.system() != 'Windows' else ['C:/Program Files/Wireshark/Wireshark.exe'],
            'color': COLORS['info']
        },
        {
            'name': 'TFTP Server',
            'icon': '📁',
            'description': 'Serveur TFTP pour transferts',
            'command': ['python3', '-m', 'http.server', '69'],  # Sera remplacé par un vrai serveur TFTP
            'color': COLORS['success']
        },
        {
            'name': 'Rufus',
            'icon': '💾',
            'description': 'Création de clés USB bootables',
            'command': ['rufus'] if platform.system() == 'Windows' else ['balenaetcher'],
            'color': COLORS['warning']
        },
        {
            'name': 'Network Scanner',
            'icon': '🔍',
            'description': 'Scanner réseau (nmap)',
            'command': ['nmap', '-sn'],  # Scan ping
            'color': COLORS['secondary']
        },
        {
            'name': 'SSH Client',
            'icon': '🔐',
            'description': 'Client SSH intégré',
            'command': 'builtin_ssh',
            'color': COLORS['dark']
        },
        {
            'name': 'IP Calculator',
            'icon': '🧮',
            'description': 'Calculateur IP/Subnets',
            'command': 'builtin_ipcalc',
            'color': COLORS['info']
        }
    ]
    
    # Créer les boutons dans une grille 3x2
    row = 0
    col = 0
    for tool in tools_data:
        tool_btn = tk.Button(tools_grid, 
                           text=f"{tool['icon']}\n{tool['name']}", 
                           font=("Arial", 10, "bold"),
                           bg=tool['color'], fg=COLORS['white'],
                           relief='flat', padx=15, pady=10,
                           width=12, height=3,
                           command=lambda t=tool: launch_professional_tool(t))
        tool_btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Tooltip au survol
        create_tooltip(tool_btn, tool['description'])
        
        col += 1
        if col > 2:  # 3 colonnes max
            col = 0
            row += 1
    
    # Configurer les colonnes pour qu'elles s'étendent
    for i in range(3):
        tools_grid.grid_columnconfigure(i, weight=1)

def create_tooltip(widget, text):
    """Crée un tooltip pour un widget"""
    def on_enter(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(tooltip, text=text, background=COLORS['dark'], 
                        foreground=COLORS['white'], font=("Arial", 9))
        label.pack()
        widget.tooltip = tooltip
    
    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def launch_professional_tool(tool):
    """Lance un outil professionnel"""
    try:
        log(f"🚀 Lancement de {tool['name']}...")
        
        if tool['command'] == 'builtin_ssh':
            show_ssh_client()
        elif tool['command'] == 'builtin_ipcalc':
            show_ip_calculator()
        elif isinstance(tool['command'], list):
            if tool['name'] == 'TFTP Server':
                start_tftp_server()
            elif tool['name'] == 'Network Scanner':
                show_network_scanner()
            else:
                # Lancer l'application externe
                subprocess.Popen(tool['command'])
                log(f"✅ {tool['name']} lancé avec succès")
        
    except FileNotFoundError:
        log(f"❌ {tool['name']} n'est pas installé sur ce système", level="ERROR")
        show_install_instructions(tool)
    except Exception as e:
        log(f"❌ Erreur lors du lancement de {tool['name']}: {e}", level="ERROR")

def show_install_instructions(tool):
    """Affiche les instructions d'installation pour un outil"""
    install_win = tk.Toplevel(root)
    install_win.title(f"Installation - {tool['name']}")
    install_win.geometry("500x300")
    install_win.configure(bg=COLORS['light'])
    
    title = tk.Label(install_win, text=f"Installation de {tool['name']}", 
                    font=("Arial", 14, "bold"), bg=COLORS['light'])
    title.pack(pady=20)
    
    instructions = get_install_instructions(tool['name'])
    
    text_widget = tk.Text(install_win, wrap=tk.WORD, bg=COLORS['white'])
    text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    text_widget.insert(tk.END, instructions)
    text_widget.config(state='disabled')

def get_install_instructions(tool_name):
    """Retourne les instructions d'installation pour un outil"""
    instructions = {
        'Wireshark': """
Pour installer Wireshark:

macOS:
• brew install wireshark
• ou télécharger depuis https://www.wireshark.org/

Windows:
• Télécharger depuis https://www.wireshark.org/
• Exécuter l'installateur en tant qu'administrateur

Linux:
• Ubuntu/Debian: sudo apt install wireshark
• CentOS/RHEL: sudo yum install wireshark
        """,
        'Rufus': """
Pour installer Rufus/BalenaEtcher:

macOS:
• brew install balenaetcher
• ou télécharger depuis https://www.balena.io/etcher/

Windows:
• Télécharger Rufus depuis https://rufus.ie/
• Portable, pas d'installation requise

Linux:
• AppImage disponible sur https://www.balena.io/etcher/
        """,
        'Network Scanner': """
Pour installer nmap:

macOS:
• brew install nmap

Windows:
• Télécharger depuis https://nmap.org/download.html

Linux:
• Ubuntu/Debian: sudo apt install nmap
• CentOS/RHEL: sudo yum install nmap
        """
    }
    
    return instructions.get(tool_name, f"Instructions d'installation non disponibles pour {tool_name}")

def show_ssh_client():
    """Affiche un client SSH intégré"""
    ssh_win = tk.Toplevel(root)
    ssh_win.title("🔐 Client SSH")
    ssh_win.geometry("600x500")
    ssh_win.configure(bg=COLORS['light'])
    
    # Frame de connexion
    conn_frame = tk.LabelFrame(ssh_win, text="Connexion SSH", bg=COLORS['light'])
    conn_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(conn_frame, text="Hôte:", bg=COLORS['light']).grid(row=0, column=0, sticky='w', padx=5, pady=5)
    host_entry = tk.Entry(conn_frame, width=30)
    host_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(conn_frame, text="Utilisateur:", bg=COLORS['light']).grid(row=0, column=2, sticky='w', padx=5, pady=5)
    user_entry = tk.Entry(conn_frame, width=20)
    user_entry.grid(row=0, column=3, padx=5, pady=5)
    
    def connect_ssh():
        host = host_entry.get()
        user = user_entry.get()
        if host and user:
            log(f"🔐 Connexion SSH à {user}@{host}...")
            # Ouvrir terminal SSH externe
            if platform.system() == "Darwin":
                subprocess.Popen(['osascript', '-e', f'tell app "Terminal" to do script "ssh {user}@{host}"'])
            elif platform.system() == "Windows":
                subprocess.Popen(['cmd', '/c', 'start', 'ssh', f'{user}@{host}'])
            else:
                subprocess.Popen(['gnome-terminal', '--', 'ssh', f'{user}@{host}'])
    
    tk.Button(conn_frame, text="Connecter", command=connect_ssh, 
             bg=COLORS['success'], fg=COLORS['white']).grid(row=0, column=4, padx=10, pady=5)

def show_ip_calculator():
    """Calculateur IP/Subnets"""
    calc_win = tk.Toplevel(root)
    calc_win.title("🧮 Calculateur IP")
    calc_win.geometry("500x400")
    calc_win.configure(bg=COLORS['light'])
    
    # Interface de calcul
    input_frame = tk.LabelFrame(calc_win, text="Entrée", bg=COLORS['light'])
    input_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(input_frame, text="IP/CIDR:", bg=COLORS['light']).grid(row=0, column=0, sticky='w', padx=5, pady=5)
    ip_entry = tk.Entry(input_frame, width=20)
    ip_entry.grid(row=0, column=1, padx=5, pady=5)
    ip_entry.insert(0, "192.168.1.1/24")
    
    result_text = tk.Text(calc_win, height=15, bg=COLORS['white'])
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def calculate_subnet():
        try:
            ip_cidr = ip_entry.get()
            import ipaddress
            network = ipaddress.IPv4Network(ip_cidr, strict=False)
            
            result = f"""
Réseau: {network}
Adresse réseau: {network.network_address}
Masque de sous-réseau: {network.netmask}
Adresse de broadcast: {network.broadcast_address}
Nombre d'hôtes: {network.num_addresses - 2}
Première adresse utilisable: {list(network.hosts())[0] if network.num_addresses > 2 else 'N/A'}
Dernière adresse utilisable: {list(network.hosts())[-1] if network.num_addresses > 2 else 'N/A'}

Plages d'adresses:
"""
            for i, addr in enumerate(network.hosts()):
                if i < 10:  # Afficher les 10 premières
                    result += f"  {addr}\n"
                elif i == 10:
                    result += f"  ... et {network.num_addresses - 12} autres\n"
                    break
            
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, result)
            
        except Exception as e:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Erreur: {e}")
    
    tk.Button(input_frame, text="Calculer", command=calculate_subnet,
             bg=COLORS['info'], fg=COLORS['white']).grid(row=0, column=2, padx=10, pady=5)

def start_tftp_server():
    """Démarre un serveur TFTP simple"""
    log("🚀 Démarrage du serveur TFTP...")
    # Pour l'instant, un serveur HTTP simple
    try:
        import threading
        import http.server
        import socketserver
        
        PORT = 8069  # Port TFTP alternatif
        
        def run_server():
            with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
                log(f"✅ Serveur TFTP/HTTP démarré sur le port {PORT}")
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
    except Exception as e:
        log(f"❌ Erreur serveur TFTP: {e}", level="ERROR")

def show_network_scanner():
    """Scanner réseau intégré"""
    scanner_win = tk.Toplevel(root)
    scanner_win.title("🔍 Scanner Réseau")
    scanner_win.geometry("600x500")
    scanner_win.configure(bg=COLORS['light'])
    
    # Interface de scan
    scan_frame = tk.LabelFrame(scanner_win, text="Configuration du scan", bg=COLORS['light'])
    scan_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(scan_frame, text="Réseau:", bg=COLORS['light']).grid(row=0, column=0, sticky='w', padx=5, pady=5)
    network_entry = tk.Entry(scan_frame, width=20)
    network_entry.grid(row=0, column=1, padx=5, pady=5)
    network_entry.insert(0, "192.168.1.0/24")
    
    result_text = tk.Text(scanner_win, height=20, bg=COLORS['white'], font=("Consolas", 9))
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def scan_network():
        network = network_entry.get()
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"🔍 Scan du réseau {network}...\n\n")
        result_text.update()
        
        try:
            import ipaddress
            net = ipaddress.IPv4Network(network, strict=False)
            
            # Scan ping simple
            import concurrent.futures
            import subprocess
            
            def ping_host(ip):
                try:
                    if platform.system() == "Windows":
                        result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)], 
                                              capture_output=True, text=True, timeout=2)
                    else:
                        result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)], 
                                              capture_output=True, text=True, timeout=2)
                    
                    if result.returncode == 0:
                        return str(ip)
                    return None
                except:
                    return None
            
            active_hosts = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(ping_host, ip) for ip in net.hosts()]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        active_hosts.append(result)
                        result_text.insert(tk.END, f"🟢 {result} - ACTIF\n")
                        result_text.see(tk.END)
                        result_text.update()
            
            result_text.insert(tk.END, f"\n✅ Scan terminé. {len(active_hosts)} hôtes actifs trouvés.\n")
            
        except Exception as e:
            result_text.insert(tk.END, f"❌ Erreur: {e}\n")
    
    tk.Button(scan_frame, text="Scanner", command=scan_network,
             bg=COLORS['info'], fg=COLORS['white']).grid(row=0, column=2, padx=10, pady=5)

def update_ui_language():
    # Mise à jour des sous-menus seulement
    menu_network.entryconfig(0, label=tr("Dashboard Réseau", "Network Dashboard"))
    for i, device in enumerate(DEVICE_IPS):
        menu_network.entryconfig(i + 2, label=f"{device} ({DEVICE_IPS[device]})")  # +2 pour Dashboard et separator
    menu_network.entryconfig(len(DEVICE_IPS) + 2, label=tr("Manuel", "Manual"))
    menu_file.entryconfig(0, label=tr("Afficher fichiers", "Show files"))
    menu_file.entryconfig(1, label=tr("Ajouter fichier", "Add file"))
    menu_file.entryconfig(2, label=tr("Supprimer fichier", "Delete file"))
    # Menu outils
    menu_tools.entryconfig(0, label=tr("Gestionnaire d'Outils", "Tools Manager"))
    menu_tools.entryconfig(1, label=tr("Ouvrir dossier Tools", "Open Tools folder"))
    # Re-peupler le menu outils pour la traduction
    populate_tools_menu()
    menu_sync.entryconfig(0, label=tr("Sync", "Sync"))
    menu_sync.entryconfig(1, label=tr("Ejecter USB", "Eject USB"))
    menu_lang.entryconfig(0, label="Français")
    menu_lang.entryconfig(1, label="English")

# Appel initial pour afficher la langue courante
update_ui_language()

# Message de démarrage indiquant la source de lancement
if USB_PATH:
    log(tr("🚀 Application lancée depuis USB:", "🚀 Application launched from USB:") + f" {USB_PATH}")
    log(tr("📁 Dossier de travail:", "📁 Working folder:") + f" {LOCAL_PATH}")
else:
    log(tr("🏠 Application lancée en mode local", "🏠 Application launched in local mode"))
    log(tr("📁 Dossier de travail:", "📁 Working folder:") + f" {LOCAL_PATH}")

log(tr("✅ Network Team Application démarrée", "✅ Network Team Application started"))

# --- Créer les outils professionnels ---
create_professional_tools()

# --- Lancer la synchronisation automatique ---
threading.Thread(target=auto_sync, daemon=True).start()

# --- Ouvrir automatiquement le dashboard après un court délai ---
def open_dashboard_auto():
    """Ouvre automatiquement le dashboard au démarrage"""
    try:
        log(tr("🌐 Ouverture automatique du dashboard réseau...", "🌐 Automatically opening network dashboard..."))
        log(tr("✓ Root window créée, tentative d'ouverture du dashboard", "✓ Root window created, attempting to open dashboard"))
        show_network_dashboard()
        log(tr("✓ Dashboard ouvert avec succès", "✓ Dashboard opened successfully"))
    except Exception as e:
        log(tr(f"❌ Erreur lors de l'ouverture du dashboard: {e}", f"❌ Error opening dashboard: {e}"), level="ERROR")

# Délai de 1 seconde pour permettre à la fenêtre principale de se charger
root.after(1000, open_dashboard_auto)

root.mainloop()
