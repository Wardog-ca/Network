# Version simplifiée de l'application
import os
import platform
import shutil
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
    """Affiche le dashboard des interfaces réseau"""
    dashboard_win = tk.Toplevel(root)
    dashboard_win.title(tr("Dashboard Réseau", "Network Dashboard"))
    dashboard_win.geometry("600x350")
    
    # Frame pour les boutons
    button_frame = tk.Frame(dashboard_win)
    button_frame.pack(pady=10)
    
    # Bouton actualiser
    refresh_btn = tk.Button(button_frame, text=tr("Actualiser", "Refresh"), 
                           command=lambda: refresh_interfaces())
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    # Frame pour le tableau avec scrollbar
    table_frame = tk.Frame(dashboard_win)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Scrollbar
    scrollbar = tk.Scrollbar(table_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Text widget pour afficher le tableau (police plus petite)
    table_text = tk.Text(table_frame, yscrollcommand=scrollbar.set, 
                        font=("Courier", 9), state='disabled', height=12)
    table_text.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=table_text.yview)
    
    def refresh_interfaces():
        """Actualise la liste des interfaces"""
        interfaces = get_network_interfaces()
        
        table_text.configure(state='normal')
        table_text.delete(1.0, tk.END)
        
        # En-tête du tableau (version compacte)
        header = f"{'Interface':<15} {'St':<3} {'IPv4':<15} {'IPv6':<25}\n"
        header += "=" * 60 + "\n"
        table_text.insert(tk.END, header)
        
        # Données des interfaces
        for iface, data in interfaces.items():
            if iface == 'lo' or iface == 'Loopback':  # Ignorer loopback sauf si demandé
                continue
                
            status = "UP" if data['status'] == 'UP' else "DN"  # Status abrégé
            ipv4_list = data['ipv4'] if data['ipv4'] else [tr('---', '---')]
            ipv6_list = data['ipv6'] if data['ipv6'] else []  # Ignorer IPv6 vide pour compacité
            
            # Première ligne avec le nom de l'interface
            first_ipv4 = ipv4_list[0] if ipv4_list else tr('---', '---')
            first_ipv6 = ipv6_list[0][:25] if ipv6_list else ''  # Tronquer IPv6
            
            # Tronquer le nom d'interface si trop long
            iface_short = iface[:14] if len(iface) > 14 else iface
            
            line = f"{iface_short:<15} {status:<3} {first_ipv4:<15} {first_ipv6:<25}\n"
            table_text.insert(tk.END, line)
            
            # Lignes supplémentaires seulement pour les IPv4 multiples (ignorer IPv6 pour compacité)
            for i in range(1, len(ipv4_list)):
                ipv4 = ipv4_list[i]
                line = f"{'':<15} {'':<3} {ipv4:<15} {'':<25}\n"
                table_text.insert(tk.END, line)
        
        # Informations supplémentaires (version compacte)
        table_text.insert(tk.END, "\n" + "=" * 60 + "\n")
        table_text.insert(tk.END, tr("Actualisé: ", "Updated: ") + 
                         time.strftime('%H:%M:%S') + "\n")
        
        table_text.configure(state='disabled')
    
    # Actualisation initiale
    refresh_interfaces()
    
    # Auto-actualisation toutes les 30 secondes
    def auto_refresh():
        refresh_interfaces()
        dashboard_win.after(30000, auto_refresh)  # 30 secondes
    
    dashboard_win.after(30000, auto_refresh)

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
root.title("Network Team - Simple")
root.geometry("600x400")

log_text = tk.Text(root, height=15, state='disabled')
log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Création des menus
menubar = tk.Menu(root)

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

root.config(menu=menubar)

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

# --- Lancer la synchronisation automatique ---
threading.Thread(target=auto_sync, daemon=True).start()

root.mainloop()
