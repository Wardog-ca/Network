# Version simplifiée de l'application
import os
import platform
import tkinter as tk
from tkinter import filedialog, simpledialog
from pathlib import Path


SYNC_FOLDER = "Network Team"
LOCAL_PATH = Path.home() / SYNC_FOLDER
LOCAL_PATH.mkdir(parents=True, exist_ok=True)

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

def log(msg):
    log_text.configure(state='normal')
    log_text.insert(tk.END, msg + "\n")
    log_text.see(tk.END)
    log_text.configure(state='disabled')


# Nouvelle fonction pour choisir équipement et interface
def set_ip():
    win = tk.Toplevel(root)
    win.title("Changer l'adresse IP")
    tk.Label(win, text="Choisir l'équipement :").pack(pady=5)
    var_device = tk.StringVar(value=list(DEVICE_IPS.keys())[0])
    for device in DEVICE_IPS:
        tk.Radiobutton(win, text=f"{device} ({DEVICE_IPS[device]})", variable=var_device, value=device).pack(anchor='w')

    # Détection automatique des interfaces réseau
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

    tk.Label(win, text="Choisir l'interface réseau :").pack(pady=5)
    var_iface = tk.StringVar(value=interfaces[0] if interfaces else "")
    tk.OptionMenu(win, var_iface, *interfaces).pack(pady=5)

    # Option pour mode manuel ou DHCP
    mode_var = tk.StringVar(value="manuel")
    tk.Label(win, text="Mode d'attribution IP :").pack(pady=5)
    tk.Radiobutton(win, text="Manuel", variable=mode_var, value="manuel").pack(anchor='w')
    tk.Radiobutton(win, text="DHCP", variable=mode_var, value="dhcp").pack(anchor='w')

    # Champ pour IP manuelle
    ip_entry = tk.Entry(win)
    ip_entry.pack(pady=5)
    ip_entry.insert(0, DEVICE_IPS[list(DEVICE_IPS.keys())[0]])
    def update_ip_entry(*_):
        ip_entry.delete(0, tk.END)
        ip_entry.insert(0, DEVICE_IPS[var_device.get()])
    var_device.trace("w", update_ip_entry)

    def apply_ip():
        device = var_device.get()
        iface = var_iface.get().strip()
        mode = mode_var.get()
        ip = ip_entry.get().strip()
        system = platform.system()
        cmd = None
        if not iface:
            log("Interface réseau non spécifiée.")
            return
        if mode == "dhcp":
            if system == "Windows":
                cmd = f'netsh interface ip set address name="{iface}" source=dhcp'
            elif system == "Linux":
                cmd = f"sudo dhclient {iface}"
            elif system == "Darwin":
                cmd = f"sudo ipconfig set {iface} DHCP"
        else:
            if not ip:
                log("Adresse IP manuelle non spécifiée.")
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
                log(f"Configuration appliquée ({mode}) sur {iface}")
            else:
                log(f"Erreur lors de l'exécution de la commande pour l'interface '{iface}'.")
        else:
            log("Système non supporté.")
        win.destroy()

    tk.Button(win, text="Appliquer", command=apply_ip).pack(pady=10)

def show_files():
    files = list(LOCAL_PATH.iterdir())
    if not files:
        log("Aucun fichier dans Network Team.")
    else:
        log("Fichiers dans Network Team :")
        for f in files:
            log(f" - {f.name}")

def add_file():
    file_path = filedialog.askopenfilename(title="Sélectionner un fichier à ajouter")
    if file_path:
        dest = LOCAL_PATH / Path(file_path).name
        try:
            with open(file_path, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())
            log(f"Fichier ajouté : {dest.name}")
        except Exception as e:
            log(f"Erreur ajout : {e}")

def delete_file():
    files = list(LOCAL_PATH.iterdir())
    if not files:
        log("Aucun fichier à supprimer.")
        return
    filenames = [f.name for f in files]
    file_to_delete = simpledialog.askstring("Supprimer fichier", f"Nom du fichier à supprimer :\n{', '.join(filenames)}")
    if file_to_delete:
        target = LOCAL_PATH / file_to_delete
        if target.exists():
            try:
                target.unlink()
                log(f"Fichier supprimé : {file_to_delete}")
            except Exception as e:
                log(f"Erreur suppression : {e}")
        else:
            log("Fichier non trouvé.")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(frame, text="Changer IP", command=set_ip, width=20).pack(side=tk.LEFT, padx=5)
tk.Button(frame, text="Afficher fichiers", command=show_files, width=20).pack(side=tk.LEFT, padx=5)
tk.Button(frame, text="Ajouter fichier", command=add_file, width=20).pack(side=tk.LEFT, padx=5)
tk.Button(frame, text="Supprimer fichier", command=delete_file, width=20).pack(side=tk.LEFT, padx=5)

root.mainloop()
