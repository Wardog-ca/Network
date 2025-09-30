#!/usr/bin/env python3

import tkinter as tk
import subprocess
import platform
import time

def get_network_interfaces():
    """Version simplifiée de détection des interfaces"""
    interfaces = {}
    try:
        if platform.system() == "Darwin":
            output = subprocess.check_output(["ifconfig"], encoding="utf-8")
            current_interface = None
            
            for line in output.splitlines():
                if line and not line.startswith('\t') and ':' in line:
                    current_interface = line.split(':')[0]
                    interfaces[current_interface] = {
                        'ipv4': [],
                        'status': 'UP' if 'UP' in line else 'DOWN'
                    }
                elif current_interface and '\tinet ' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        interfaces[current_interface]['ipv4'].append(parts[1])
    except Exception as e:
        print(f"Erreur: {e}")
    
    return interfaces

def show_simple_dashboard():
    """Dashboard simplifié pour test"""
    print("Création du dashboard...")
    
    # Fenêtre principale
    root = tk.Tk()
    root.title("Test Dashboard Réseau")
    root.geometry("500x400")
    
    # Frame principal
    main_frame = tk.Frame(root, bg='#f0f0f0')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Titre
    title_label = tk.Label(main_frame, text="🌐 Interfaces Réseau", 
                          font=("Arial", 14, "bold"), bg='#f0f0f0')
    title_label.pack(pady=10)
    
    # Obtenir les interfaces
    interfaces = get_network_interfaces()
    print(f"Interfaces détectées: {len(interfaces)}")
    
    # Afficher les interfaces
    for name, data in interfaces.items():
        if name in ['lo0']:  # Ignorer loopback
            continue
            
        # Frame pour chaque interface
        if_frame = tk.Frame(main_frame, bg='white', relief='raised', bd=1)
        if_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Icône et nom
        if 'en' in name:
            icon = "🔌"
        elif 'bridge' in name:
            icon = "🐳"
        elif 'utun' in name:
            icon = "🔒"
        else:
            icon = "🌐"
            
        # Status
        status_icon = "🟢" if data['status'] == 'UP' else "🔴"
        
        # Label avec info
        info_text = f"{icon} {name} {status_icon}"
        if data['ipv4']:
            info_text += f" - {data['ipv4'][0]}"
        else:
            info_text += " - Pas d'IP"
            
        label = tk.Label(if_frame, text=info_text, font=("Arial", 10), 
                        bg='white', anchor='w')
        label.pack(fill=tk.X, padx=10, pady=5)
    
    print("Dashboard créé, démarrage de la boucle principale...")
    root.mainloop()
    print("Application fermée")

if __name__ == "__main__":
    show_simple_dashboard()