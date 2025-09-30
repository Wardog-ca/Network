#!/usr/bin/env python3
"""
Dashboard Réseau Indépendant
Version simplifiée qui peut être lancée séparément
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import platform
import time
import threading

def get_network_interfaces():
    """Récupère toutes les interfaces réseau et leurs adresses IP"""
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
                        'ipv6': [],
                        'status': 'DOWN'
                    }
                    if 'UP' in line:
                        interfaces[current_interface]['status'] = 'UP'
                elif current_interface and '\tinet ' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        interfaces[current_interface]['ipv4'].append(parts[1])
                elif current_interface and '\tinet6 ' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2 and not parts[1].startswith('fe80'):
                        interfaces[current_interface]['ipv6'].append(parts[1])
    except Exception as e:
        print(f"Erreur lors de la récupération des interfaces: {e}")
    
    return interfaces

class NetworkDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌐 Dashboard Réseau")
        self.root.geometry("400x500")
        self.root.configure(bg='#f0f0f0')
        
        # Garder au premier plan
        self.root.attributes('-topmost', True)
        
        # Position dans le coin supérieur droit
        screen_width = self.root.winfo_screenwidth()
        x_pos = screen_width - 420
        self.root.geometry(f"400x500+{x_pos}+50")
        
        self.setup_ui()
        self.refresh_interfaces()
        
        # Auto-refresh toutes les 30 secondes
        self.auto_refresh()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # En-tête
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🌐 Réseau", 
                              font=("Arial", 14, "bold"), 
                              fg='white', bg='#2c3e50')
        title_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        # Bouton refresh
        refresh_btn = tk.Button(header_frame, text="🔄", 
                               font=("Arial", 10), bg='#3498db', fg='white',
                               relief='flat', padx=10, pady=5,
                               command=self.refresh_interfaces)
        refresh_btn.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # Frame principal avec scroll
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas avec scrollbar
        self.canvas = tk.Canvas(main_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f0f0f0')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_interface_card(self, iface_name, iface_data):
        """Crée une carte pour une interface"""
        # Frame de la carte
        card_frame = tk.Frame(self.scrollable_frame, bg='white', relief='raised', bd=1)
        card_frame.pack(fill=tk.X, pady=3, padx=2)
        
        # En-tête de la carte
        header_frame = tk.Frame(card_frame, bg='white')
        header_frame.pack(fill=tk.X, padx=10, pady=(8, 4))
        
        # Icône selon le type
        if 'en' in iface_name.lower():
            icon = "🔌"
        elif 'bridge' in iface_name.lower():
            icon = "🐳"
        elif 'utun' in iface_name.lower() or 'vpn' in iface_name.lower():
            icon = "🔒"
        elif 'wlan' in iface_name.lower() or 'wifi' in iface_name.lower():
            icon = "📶"
        else:
            icon = "🌐"
        
        # Nom et status
        status_color = '#27ae60' if iface_data['status'] == 'UP' else '#e74c3c'
        status_icon = "●" if iface_data['status'] == 'UP' else "○"
        
        name_label = tk.Label(header_frame, text=f"{icon} {iface_name}", 
                             font=("Arial", 11, "bold"), bg='white')
        name_label.pack(side=tk.LEFT)
        
        status_label = tk.Label(header_frame, text=status_icon, 
                               font=("Arial", 12), fg=status_color, bg='white')
        status_label.pack(side=tk.RIGHT)
        
        # Contenu IP
        if iface_data['ipv4']:
            content_frame = tk.Frame(card_frame, bg='white')
            content_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
            
            ip_label = tk.Label(content_frame, text=iface_data['ipv4'][0], 
                               font=("Arial", 10), fg='#3498db', bg='white')
            ip_label.pack(side=tk.LEFT)
            
            if len(iface_data['ipv4']) > 1:
                more_label = tk.Label(content_frame, text=f"+{len(iface_data['ipv4'])-1}", 
                                     font=("Arial", 9), fg='#7f8c8d', bg='white')
                more_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def refresh_interfaces(self):
        """Actualise la liste des interfaces"""
        # Supprimer les anciennes cartes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Récupérer les interfaces
        interfaces = get_network_interfaces()
        
        # Statistiques
        filtered_interfaces = {}
        for k, v in interfaces.items():
            if k in ['lo0']:  # Ignorer loopback
                continue
            if k.startswith(('anpi', 'awdl', 'llw', 'gif', 'stf')):  # Ignorer interfaces système
                continue
            if k.startswith('utun') and not v['ipv4'] and not v['ipv6']:  # Ignorer VPN vides
                continue
            filtered_interfaces[k] = v
        
        # En-tête de stats
        stats_frame = tk.Frame(self.scrollable_frame, bg='white', relief='raised', bd=1)
        stats_frame.pack(fill=tk.X, pady=(0, 5), padx=2)
        
        stats_content = tk.Frame(stats_frame, bg='white')
        stats_content.pack(fill=tk.X, padx=10, pady=8)
        
        total = len(filtered_interfaces)
        active = len([k for k, v in filtered_interfaces.items() if v['status'] == 'UP'])
        
        stats_text = f"{active}/{total} actives"
        stats_label = tk.Label(stats_content, text=stats_text, 
                              font=("Arial", 11, "bold"), fg='#27ae60', bg='white')
        stats_label.pack(side=tk.LEFT)
        
        time_label = tk.Label(stats_content, text=time.strftime('%H:%M:%S'), 
                             font=("Arial", 9), fg='#7f8c8d', bg='white')
        time_label.pack(side=tk.RIGHT)
        
        # Créer les cartes
        for iface_name, iface_data in filtered_interfaces.items():
            self.create_interface_card(iface_name, iface_data)
    
    def auto_refresh(self):
        """Auto-actualisation"""
        try:
            self.refresh_interfaces()
            self.root.after(30000, self.auto_refresh)  # 30 secondes
        except:
            pass
    
    def run(self):
        """Lance le dashboard"""
        print("🌐 Lancement du Dashboard Réseau...")
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = NetworkDashboard()
    dashboard.run()