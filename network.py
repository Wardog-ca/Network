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
LOCAL_PATH = Path.home() / SYNC_FOLDER
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
                        
                        # Méthode 1: NetworkManager (prioritaire pour Ubuntu 25.04+)
                        # D'abord, s'assurer que l'interface est gérée par NetworkManager
                        unmanaged_cmd = f"sudo nmcli dev set {iface} managed yes"
                        os.system(unmanaged_cmd)
                        
                        # Supprimer les connexions existantes qui pourraient causer des conflits
                        cleanup_cmd = f"sudo nmcli con show | grep {iface} | awk '{{print $1}}' | xargs -r sudo nmcli con delete"
                        os.system(cleanup_cmd)
                        
                        # Créer une nouvelle connexion DHCP
                        nm_cmd = f"sudo nmcli con add type ethernet con-name 'dhcp-{iface}' ifname {iface} && sudo nmcli con mod 'dhcp-{iface}' ipv4.method auto && sudo nmcli con up 'dhcp-{iface}'"
                        result1 = os.system(nm_cmd)
                        
                        if result1 != 0:
                            # Méthode 2: Netplan avec configuration explicite
                            log(tr("Tentative avec Netplan (configuration fichier)...", "Trying with Netplan (file configuration)..."))
                            
                            netplan_config = f"""network:
  version: 2
  ethernets:
    {iface}:
      dhcp4: true
      dhcp6: false"""
                            
                            # Créer un fichier de configuration temporaire
                            config_file = f"/tmp/99-{iface}-dhcp.yaml"
                            try:
                                with open(config_file, "w") as f:
                                    f.write(netplan_config)
                                
                                # Copier la configuration et appliquer
                                copy_cmd = f"sudo cp {config_file} /etc/netplan/ && sudo netplan apply"
                                result2 = os.system(copy_cmd)
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
for device in DEVICE_IPS:
    menu_network.add_command(
        label=f"{device} ({DEVICE_IPS[device]})",
        command=lambda dev=device: set_ip_device(dev)
    )
menu_network.add_command(label=tr("Manuel", "Manual"), command=set_ip_manual)
menubar.add_cascade(label=tr("Réseau", "Network / Réseau"), menu=menu_network)

# File management menu
menu_file = tk.Menu(menubar, tearoff=0)
menu_file.add_command(label=tr("Afficher fichiers", "Show files"), command=show_files)
menu_file.add_command(label=tr("Ajouter fichier", "Add file"), command=add_file)
menu_file.add_command(label=tr("Supprimer fichier", "Delete file"), command=delete_file)
menubar.add_cascade(label=tr("Gestion fichiers", "File Management / Gestion fichiers"), menu=menu_file)

# Sync & USB menu
menu_sync = tk.Menu(menubar, tearoff=0)
menu_sync.add_command(label=tr("Sync", "Sync"), command=manual_sync)
menu_sync.add_command(label=tr("Ejecter USB", "Eject USB"), command=eject_usb)
menubar.add_cascade(label=tr("Synchronisation / USB", "Sync / USB"), menu=menu_sync)

root.config(menu=menubar)

def update_ui_language():
    # Mise à jour des sous-menus seulement
    for i, device in enumerate(DEVICE_IPS):
        menu_network.entryconfig(i, label=f"{device} ({DEVICE_IPS[device]})")
    menu_network.entryconfig(len(DEVICE_IPS), label=tr("Manuel", "Manual"))
    menu_file.entryconfig(0, label=tr("Afficher fichiers", "Show files"))
    menu_file.entryconfig(1, label=tr("Ajouter fichier", "Add file"))
    menu_file.entryconfig(2, label=tr("Supprimer fichier", "Delete file"))
    menu_sync.entryconfig(0, label=tr("Sync", "Sync"))
    menu_sync.entryconfig(1, label=tr("Ejecter USB", "Eject USB"))
    menu_lang.entryconfig(0, label="Français")
    menu_lang.entryconfig(1, label="English")

# Appel initial pour afficher la langue courante
update_ui_language()

# --- Lancer la synchronisation automatique ---
threading.Thread(target=auto_sync, daemon=True).start()

root.mainloop()
