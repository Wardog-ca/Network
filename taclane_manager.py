#!/usr/bin/env python3
"""
Outil de gestion Taclane - Interface spécialisée pour les équipements Taclane
Adresse IP par défaut: 172.16.0.1
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import socket
import time
import os
import webbrowser

def create_taclane_interface(parent, colors, log_func):
    """Crée l'interface de gestion Taclane"""
    
    taclane_win = tk.Toplevel(parent)
    taclane_win.title("🛡️ Gestionnaire Taclane")
    taclane_win.geometry("800x700")
    taclane_win.configure(bg=colors['light'])
    taclane_win.resizable(True, True)
    
    # En-tête
    header = tk.Frame(taclane_win, bg=colors['primary'], height=70)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    title_frame = tk.Frame(header, bg=colors['primary'])
    title_frame.pack(expand=True)
    
    tk.Label(title_frame, text="🛡️ Gestionnaire Taclane", 
            font=("Arial", 18, "bold"), 
            fg=colors['white'], bg=colors['primary']).pack(pady=10)
    
    tk.Label(title_frame, text="Outil spécialisé pour équipements de chiffrement Taclane", 
            font=("Arial", 10), 
            fg='#ecf0f1', bg=colors['primary']).pack()
    
    # Configuration principale
    config_frame = tk.LabelFrame(taclane_win, text="🔧 Configuration Taclane", 
                                bg=colors['light'], font=("Arial", 11, "bold"))
    config_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # Adresse IP Taclane
    ip_frame = tk.Frame(config_frame, bg=colors['light'])
    ip_frame.pack(fill=tk.X, padx=10, pady=8)
    
    tk.Label(ip_frame, text="🌐 Adresse IP Taclane:", 
            font=("Arial", 10, "bold"), bg=colors['light']).pack(side=tk.LEFT)
    
    ip_var = tk.StringVar(value="172.16.0.1")
    ip_entry = tk.Entry(ip_frame, textvariable=ip_var, width=15, font=("Arial", 10))
    ip_entry.pack(side=tk.LEFT, padx=10)
    
    # Statut de connexion
    status_label = tk.Label(ip_frame, text="⚪ Non testé", 
                           font=("Arial", 10, "bold"), fg=colors['secondary'])
    status_label.pack(side=tk.LEFT, padx=20)
    
    def test_connection():
        """Test de connectivité vers le Taclane"""
        ip = ip_var.get()
        status_label.config(text="🟡 Test en cours...", fg=colors['warning'])
        taclane_win.update()
        
        def ping_test():
            try:
                # Test ping
                result = subprocess.run(['ping', '-c', '3', '-W', '2000', ip], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    status_label.config(text="🟢 Connecté", fg=colors['success'])
                    log_func(f"✅ Taclane {ip} accessible")
                    
                    # Test des ports communs Taclane
                    test_ports([80, 443, 22, 23, 161], ip)
                else:
                    status_label.config(text="🔴 Hors ligne", fg=colors['danger'])
                    log_func(f"❌ Taclane {ip} non accessible")
                    
            except Exception as e:
                status_label.config(text="🔴 Erreur", fg=colors['danger'])
                log_func(f"❌ Erreur test Taclane: {e}")
        
        threading.Thread(target=ping_test, daemon=True).start()
    
    def test_ports(ports, ip):
        """Test des ports sur le Taclane"""
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        if open_ports:
            log_func(f"🔓 Ports ouverts sur {ip}: {', '.join(map(str, open_ports))}")
            update_port_status(open_ports)
    
    tk.Button(ip_frame, text="🔍 Tester", command=test_connection,
             bg=colors['info'], fg=colors['white'], padx=10).pack(side=tk.LEFT, padx=5)
    
    # Outils de diagnostic
    diagnostic_frame = tk.LabelFrame(taclane_win, text="🔍 Outils de Diagnostic", 
                                   bg=colors['light'], font=("Arial", 11, "bold"))
    diagnostic_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # Grille d'outils de diagnostic
    diag_grid = tk.Frame(diagnostic_frame, bg=colors['light'])
    diag_grid.pack(padx=10, pady=10)
    
    diagnostic_tools = [
        ("🏓 Ping Continu", lambda: start_continuous_ping(ip_var.get())),
        ("📊 Traceroute", lambda: run_traceroute(ip_var.get())),
        ("🔌 Scan Ports", lambda: run_port_scan(ip_var.get())),
        ("📈 Monitoring", lambda: start_monitoring(ip_var.get())),
        ("🌐 Interface Web", lambda: open_web_interface(ip_var.get())),
        ("📋 ARP Table", lambda: show_arp_info(ip_var.get()))
    ]
    
    for i, (name, command) in enumerate(diagnostic_tools):
        row, col = i // 3, i % 3
        btn = tk.Button(diag_grid, text=name, command=command,
                       bg=colors['info'], fg=colors['white'], 
                       width=15, pady=5, font=("Arial", 9))
        btn.grid(row=row, column=col, padx=5, pady=5)
    
    # Informations système
    info_frame = tk.LabelFrame(taclane_win, text="📊 Informations Système", 
                              bg=colors['light'], font=("Arial", 11, "bold"))
    info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
    # Notebook pour organiser les informations
    notebook = ttk.Notebook(info_frame)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Onglet Statut
    status_tab = tk.Frame(notebook, bg=colors['white'])
    notebook.add(status_tab, text="📊 Statut")
    
    status_text = tk.Text(status_tab, height=8, bg=colors['white'], 
                         font=("Consolas", 9), wrap=tk.WORD)
    status_scroll = tk.Scrollbar(status_tab, orient=tk.VERTICAL, command=status_text.yview)
    status_text.configure(yscrollcommand=status_scroll.set)
    
    status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Onglet Logs
    logs_tab = tk.Frame(notebook, bg=colors['white'])
    notebook.add(logs_tab, text="📝 Logs")
    
    logs_text = tk.Text(logs_tab, height=8, bg=colors['white'], 
                       font=("Consolas", 9), wrap=tk.WORD)
    logs_scroll = tk.Scrollbar(logs_tab, orient=tk.VERTICAL, command=logs_text.yview)
    logs_text.configure(yscrollcommand=logs_scroll.set)
    
    logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    logs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Onglet Configuration
    config_tab = tk.Frame(notebook, bg=colors['white'])
    notebook.add(config_tab, text="⚙️ Config")
    
    config_text = tk.Text(config_tab, height=8, bg=colors['white'], 
                         font=("Consolas", 9), wrap=tk.WORD)
    config_scroll = tk.Scrollbar(config_tab, orient=tk.VERTICAL, command=config_text.yview)
    config_text.configure(yscrollcommand=config_scroll.set)
    
    config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    config_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Variables globales pour les fonctions
    monitoring_active = [False]
    port_status = {}
    
    def update_port_status(open_ports):
        """Met à jour le statut des ports"""
        nonlocal port_status
        port_status = {port: True for port in open_ports}
        
        port_info = "🔓 Ports ouverts détectés:\n"
        port_descriptions = {
            80: "HTTP - Interface web",
            443: "HTTPS - Interface web sécurisée", 
            22: "SSH - Administration à distance",
            23: "Telnet - Console d'administration",
            161: "SNMP - Monitoring réseau"
        }
        
        for port in open_ports:
            desc = port_descriptions.get(port, "Service inconnu")
            port_info += f"  • Port {port}: {desc}\n"
        
        status_text.delete(1.0, tk.END)
        status_text.insert(tk.END, port_info)
    
    def start_continuous_ping(ip):
        """Lance un ping continu"""
        def continuous_ping():
            try:
                log_func(f"🏓 Ping continu vers {ip} démarré")
                process = subprocess.Popen(['ping', ip], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE,
                                         text=True, universal_newlines=True)
                
                ping_win = tk.Toplevel(taclane_win)
                ping_win.title(f"🏓 Ping continu - {ip}")
                ping_win.geometry("600x400")
                
                ping_text = tk.Text(ping_win, bg='black', fg='green', 
                                   font=("Consolas", 10))
                ping_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                def update_ping():
                    if process.poll() is None:
                        line = process.stdout.readline()
                        if line:
                            ping_text.insert(tk.END, line)
                            ping_text.see(tk.END)
                        ping_win.after(100, update_ping)
                
                update_ping()
                
                def stop_ping():
                    process.terminate()
                    ping_win.destroy()
                
                tk.Button(ping_win, text="⏹️ Arrêter", command=stop_ping,
                         bg=colors['danger'], fg=colors['white']).pack(pady=5)
                
            except Exception as e:
                log_func(f"❌ Erreur ping: {e}")
        
        threading.Thread(target=continuous_ping, daemon=True).start()
    
    def run_traceroute(ip):
        """Exécute un traceroute"""
        def traceroute():
            try:
                log_func(f"📊 Traceroute vers {ip}")
                result = subprocess.run(['traceroute', ip], 
                                      capture_output=True, text=True, timeout=30)
                
                trace_win = tk.Toplevel(taclane_win)
                trace_win.title(f"📊 Traceroute - {ip}")
                trace_win.geometry("700x500")
                
                trace_text = tk.Text(trace_win, bg=colors['white'], 
                                   font=("Consolas", 9))
                trace_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                trace_text.insert(tk.END, result.stdout)
                if result.stderr:
                    trace_text.insert(tk.END, f"\nErreurs:\n{result.stderr}")
                
            except Exception as e:
                log_func(f"❌ Erreur traceroute: {e}")
        
        threading.Thread(target=traceroute, daemon=True).start()
    
    def run_port_scan(ip):
        """Scan complet des ports"""
        def port_scan():
            try:
                log_func(f"🔌 Scan des ports sur {ip}")
                common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 161, 162, 8080, 8443]
                
                scan_results = []
                for port in common_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, port))
                        if result == 0:
                            scan_results.append(f"🟢 Port {port}: OUVERT")
                        else:
                            scan_results.append(f"🔴 Port {port}: FERMÉ")
                        sock.close()
                    except:
                        scan_results.append(f"❓ Port {port}: ERREUR")
                
                # Afficher les résultats
                scan_info = f"🔌 Résultats du scan pour {ip}:\n\n"
                scan_info += "\n".join(scan_results)
                
                logs_text.delete(1.0, tk.END)
                logs_text.insert(tk.END, scan_info)
                
                log_func(f"✅ Scan terminé pour {ip}")
                
            except Exception as e:
                log_func(f"❌ Erreur scan ports: {e}")
        
        threading.Thread(target=port_scan, daemon=True).start()
    
    def start_monitoring(ip):
        """Démarre le monitoring continu"""
        if monitoring_active[0]:
            monitoring_active[0] = False
            log_func("🛑 Monitoring arrêté")
            return
        
        monitoring_active[0] = True
        log_func(f"📈 Monitoring démarré pour {ip}")
        
        def monitor():
            ping_count = 0
            success_count = 0
            
            while monitoring_active[0]:
                try:
                    # Test ping
                    result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                          capture_output=True, timeout=5)
                    
                    ping_count += 1
                    if result.returncode == 0:
                        success_count += 1
                        status = "🟢 ACTIF"
                    else:
                        status = "🔴 INACTIF"
                    
                    # Calculer la disponibilité
                    availability = (success_count / ping_count) * 100 if ping_count > 0 else 0
                    
                    # Mettre à jour l'affichage
                    monitor_info = f"📈 Monitoring Taclane {ip}\n"
                    monitor_info += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    monitor_info += f"Statut actuel: {status}\n"
                    monitor_info += f"Tests effectués: {ping_count}\n"
                    monitor_info += f"Succès: {success_count}\n"
                    monitor_info += f"Disponibilité: {availability:.1f}%\n"
                    monitor_info += f"Dernière vérification: {time.strftime('%H:%M:%S')}\n"
                    
                    if ping_count > 1:
                        monitor_info += f"\n📊 Historique des 10 derniers tests:\n"
                    
                    config_text.delete(1.0, tk.END)
                    config_text.insert(tk.END, monitor_info)
                    
                    time.sleep(5)  # Attendre 5 secondes
                    
                except Exception as e:
                    log_func(f"❌ Erreur monitoring: {e}")
                    break
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def open_web_interface(ip):
        """Ouvre l'interface web du Taclane"""
        try:
            # Essayer HTTPS d'abord, puis HTTP
            urls = [f"https://{ip}", f"http://{ip}"]
            
            for url in urls:
                try:
                    webbrowser.open(url)
                    log_func(f"🌐 Interface web ouverte: {url}")
                    break
                except:
                    continue
                    
        except Exception as e:
            log_func(f"❌ Erreur ouverture interface web: {e}")
    
    def show_arp_info(ip):
        """Affiche les informations ARP"""
        def get_arp():
            try:
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
                
                arp_win = tk.Toplevel(taclane_win)
                arp_win.title("📋 Table ARP")
                arp_win.geometry("600x400")
                
                arp_text = tk.Text(arp_win, bg=colors['white'], font=("Consolas", 9))
                arp_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                arp_text.insert(tk.END, f"📋 Table ARP - Recherche de {ip}\n")
                arp_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
                arp_text.insert(tk.END, result.stdout)
                
                # Rechercher spécifiquement l'IP Taclane
                if ip in result.stdout:
                    arp_text.insert(tk.END, f"\n✅ Entrée ARP trouvée pour {ip}")
                else:
                    arp_text.insert(tk.END, f"\n❌ Aucune entrée ARP pour {ip}")
                
            except Exception as e:
                log_func(f"❌ Erreur ARP: {e}")
        
        threading.Thread(target=get_arp, daemon=True).start()
    
    # Initialiser les informations par défaut
    default_info = """🛡️ Gestionnaire Taclane - Informations par défaut

📋 Configuration typique Taclane:
• Adresse IP: 172.16.0.1 (réseau privé)
• Ports communs: 80 (HTTP), 443 (HTTPS), 22 (SSH)
• Interface: Web-based management
• Protocoles: SNMP, SSH, Telnet possible

🔧 Outils disponibles:
• Test de connectivité ping
• Scan des ports de service
• Monitoring de disponibilité
• Accès interface web administrative
• Diagnostic réseau avancé

⚠️ Note de sécurité:
Les équipements Taclane sont des dispositifs de chiffrement sensibles.
Assurez-vous d'avoir les autorisations appropriées avant utilisation."""
    
    status_text.insert(tk.END, default_info)
    status_text.config(state='disabled')
    
    # Logs initiaux
    logs_text.insert(tk.END, f"📝 Session démarrée - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    logs_text.insert(tk.END, f"🛡️ Outil Taclane initialisé pour {ip_var.get()}\n")
    
    # Configuration par défaut
    config_info = """⚙️ Configuration Taclane

🌐 Réseau:
• Segment: 172.16.0.0/24
• Passerelle probable: 172.16.0.254
• Masque: 255.255.255.0

🔒 Sécurité:
• Chiffrement: AES-256 (typique)
• Authentification: Certificats/PSK
• Management: HTTPS recommandé

🔧 Maintenance:
• Vérification régulière de connectivité
• Monitoring des performances
• Surveillance des logs d'erreur
• Mise à jour firmware si nécessaire"""
    
    config_text.insert(tk.END, config_info)
    
    # Fermeture propre
    def on_closing():
        monitoring_active[0] = False
        taclane_win.destroy()
    
    taclane_win.protocol("WM_DELETE_WINDOW", on_closing)
    
    return taclane_win