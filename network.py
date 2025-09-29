import os
import shutil
import logging
import platform
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog
import threading
import time

# --- CONFIG ---
SYNC_FOLDER = "Network Team"
LOCAL_PATH = os.path.expanduser("~/Network Team")
FIRMWARE_DIR = os.path.join(LOCAL_PATH, "Firmware")
TOOL_NAME = "tool.exe"  # ou tool.sh/mac
YUM_REPO_PATH = "/var/www/html/yumrepo"
SYNC_INTERVAL = 5
LOG_FILE = os.path.join("/tmp" if platform.system() != "Windows" else LOCAL_PATH, "network_team.log")

DEVICE_IPS = {
    "Switch Cisco": "192.168.1.10",
    "Firewall Palo Alto": "192.168.1.20",
    "AP Ubiquiti": "192.168.1.30"
}

# --- Setup logging ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Créer dossiers locaux si absent ---
os.makedirs(FIRMWARE_DIR, exist_ok=True)

# --- Log GUI ---
def log(msg):
    log_text.configure(state='normal')
    log_text.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    log_text.see(tk.END)
    log_text.configure(state='disabled')
    logging.info(msg)

# --- Détection clé USB multiplateforme ---
def find_usb_path():
    system = platform.system()
    if system == "Windows":
        # Hardcoder lettre de clé si pas psutil
        usb_path = r"E:\Network Team"
        if os.path.exists(usb_path):
            return usb_path
    elif system == "Linux":
        media_path = f"/media/{os.getlogin()}"
        if os.path.exists(media_path):
            for d in os.listdir(media_path):
                candidate = os.path.join(media_path, d, SYNC_FOLDER)
                if os.path.exists(candidate):
                    return candidate
    elif system == "Darwin":  # macOS
        media_path = "/Volumes"
        if os.path.exists(media_path):
            for d in os.listdir(media_path):
                candidate = os.path.join(media_path, d, SYNC_FOLDER)
                if os.path.exists(candidate):
                    return candidate
    return None

# --- Synchronisation automatique ---
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

def sync():
    usb_dir = find_usb_path()
    if not usb_dir:
        log(f"Aucune clé USB avec dossier '{SYNC_FOLDER}' détectée.")
        return False
    latest = get_latest(LOCAL_PATH, usb_dir)
    try:
        if latest == "SRC":
            shutil.copytree(LOCAL_PATH, usb_dir, dirs_exist_ok=True)
            log("Synchronisation Laptop → USB")
        elif latest == "DST":
            shutil.copytree(usb_dir, LOCAL_PATH, dirs_exist_ok=True)
            log("Synchronisation USB → Laptop")
        else:
            log("Déjà synchronisé")
    except Exception as e:
        log(f"Erreur sync : {e}")
    return True

def auto_sync():
    while True:
        sync()
        time.sleep(SYNC_INTERVAL)

# --- IP Management ---
def set_ip(ip_addr):
    try:
        system = platform.system()
        if system == "Windows":
            os.system(f'netsh interface ip set address name="Ethernet" static {ip_addr} 255.255.255.0 192.168.1.1')
        elif system == "Linux":
            os.system(f"sudo ip addr flush dev eth0")
            os.system(f"sudo ip addr add {ip_addr}/24 dev eth0")
            os.system(f"sudo ip route add default via 192.168.1.1")
        elif system == "Darwin":
            interface = "en0"
            os.system(f"sudo networksetup -setmanual {interface} {ip_addr} 255.255.255.0 192.168.1.1")
        log(f"IP changée : {ip_addr}")
    except Exception as e:
        log(f"Erreur IP : {e}")

def choose_device():
    win = tk.Toplevel(root)
    win.title("Choisir un device")
    row = 0
    for device, ip in DEVICE_IPS.items():
        tk.Button(win, text=f"{device} → {ip}", command=lambda ip=ip: set_ip_and_close(ip, win)).grid(row=row, column=0)
        row += 1
    tk.Button(win, text="IP manuelle", command=lambda: manual_ip(win)).grid(row=row, column=0)

def set_ip_and_close(ip, win):
    set_ip(ip)
    win.destroy()

def manual_ip(win):
    ip = simpledialog.askstring("IP manuelle", "Entrer l'adresse IP :")
    if ip:
        set_ip(ip)
    win.destroy()

# --- Lancer outil externe ---
def launch_tool():
    tool_path = os.path.join(LOCAL_PATH, TOOL_NAME)
    if os.path.exists(tool_path):
        try:
            if platform.system() == "Windows":
                os.startfile(tool_path)
            else:
                subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", tool_path])
            log(f"Outil lancé : {TOOL_NAME}")
        except Exception as e:
            log(f"Erreur outil : {e}")
    else:
        log(f"Outil non trouvé : {TOOL_NAME}")

# --- Upload firmware ---
def upload_firmware():
    fw_file = filedialog.askopenfilename(title="Sélectionner firmware")
    if fw_file:
        shutil.copy2(fw_file, FIRMWARE_DIR)
        log(f"Firmware ajouté : {os.path.basename(fw_file)}")
        sync()
        # Si Linux/macOS serveur, mettre à jour YUM
        if platform.system() != "Windows" and os.path.exists(YUM_REPO_PATH):
            update_yum()

def update_yum():
    try:
        for f in os.listdir(FIRMWARE_DIR):
            src = os.path.join(FIRMWARE_DIR, f)
            dst = os.path.join(YUM_REPO_PATH, f)
            shutil.copy2(src, dst)
            log(f"Firmware copié dans YUM : {f}")
        subprocess.run(["createrepo", "--update", YUM_REPO_PATH], check=True)
        log("Dépôt YUM mis à jour")
    except Exception as e:
        log(f"Erreur YUM : {e}")

# --- GUI ---
root = tk.Tk()
root.title("Network Team Tool")
root.geometry("700x500")

log_text = scrolledtext.ScrolledText(root, width=90, height=25, state='disabled')
log_text.pack(padx=10, pady=10)

is_linux_mac = platform.system() != "Windows"
usb_detected = find_usb_path() is not None

if not is_linux_mac or usb_detected:
    tk.Button(root, text="Configurer IP", command=choose_device, width=30).pack(pady=5)
    tk.Button(root, text=f"Lancer {TOOL_NAME}", command=launch_tool, width=30).pack(pady=5)
    tk.Button(root, text="Uploader Firmware", command=upload_firmware, width=30).pack(pady=5)
    tk.Button(root, text="Mettre à jour YUM", command=update_yum, width=30).pack(pady=5)

log_text = scrolledtext.ScrolledText(root, width=90, height=25, state='disabled')
log_text.pack(padx=10, pady=10)

# Auto-sync background
threading.Thread(target=auto_sync, daemon=True).start()

# Liste firmwares à l'ouverture si clé détectée
if is_linux_mac and usb_detected:
    fw_dir = os.path.join(find_usb_path(), "Firmware")
    if os.path.exists(fw_dir):
        fw_list = os.listdir(fw_dir)
        if fw_list:
            log("Firmwares sur la clé :")
            for f in fw_list:
                log(f" - {f}")
        else:
            log("Aucun firmware sur la clé")
    else:
        log("Pas de dossier Firmware sur la clé")

root.mainloop()
