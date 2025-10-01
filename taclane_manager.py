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
    
    def check_network_config():
        """Vérifie la configuration réseau actuelle"""
        try:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            
            # Chercher une interface dans le réseau 172.16.0.x
            taclane_interfaces = []
            current_interface = None
            
            for line in result.stdout.split('\n'):
                if line and not line.startswith('\t') and ':' in line:
                    current_interface = line.split(':')[0]
                elif current_interface and 'inet 172.16.0.' in line:
                    ip_addr = line.split('inet ')[1].split()[0]
                    taclane_interfaces.append((current_interface, ip_addr))
            
            net_win = tk.Toplevel(taclane_win)
            net_win.title("🌐 Configuration Réseau")
            net_win.geometry("500x400")
            
            tk.Label(net_win, text="🌐 État de la Configuration Réseau", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            net_text = tk.Text(net_win, bg=colors['white'], font=("Consolas", 9))
            net_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            net_info = "🔍 Vérification des interfaces réseau...\n\n"
            
            if taclane_interfaces:
                net_info += "✅ Interface(s) configurée(s) pour Taclane:\n"
                for interface, ip in taclane_interfaces:
                    net_info += f"  • {interface}: {ip}\n"
                net_info += "\n✅ Vous pouvez accéder au Taclane!\n"
            else:
                net_info += "❌ Aucune interface dans le réseau 172.16.0.0/24\n\n"
                net_info += "⚠️  Configuration requise:\n"
                net_info += "   • Votre interface doit avoir une IP comme 172.16.0.2\n"
                net_info += "   • Ceci permet la communication avec le Taclane (172.16.0.1)\n\n"
                net_info += "💡 Utilisez le bouton 'Config Auto' pour configurer automatiquement\n"
            
            net_info += f"\n📋 Interfaces réseau détectées:\n"
            
            # Lister toutes les interfaces
            current_interface = None
            for line in result.stdout.split('\n'):
                if line and not line.startswith('\t') and ':' in line:
                    current_interface = line.split(':')[0]
                    status = "UP" if "UP" in line else "DOWN"
                    net_info += f"  • {current_interface}: {status}\n"
                elif current_interface and 'inet ' in line and 'inet 127.0.0.1' not in line:
                    ip_addr = line.split('inet ')[1].split()[0]
                    net_info += f"    └─ IP: {ip_addr}\n"
            
            net_text.insert(tk.END, net_info)
            net_text.config(state='disabled')
            
            # Bouton pour configuration auto si nécessaire
            if not taclane_interfaces:
                def auto_config():
                    net_win.destroy()
                    show_network_config_help()
                
                tk.Button(net_win, text="🔧 Guide Configuration", 
                         command=auto_config, bg=colors['warning'], 
                         fg=colors['white'], padx=20, pady=5).pack(pady=10)
            
        except Exception as e:
            log_func(f"❌ Erreur vérification réseau: {e}")
    
    def show_network_config_help():
        """Affiche l'aide pour la configuration réseau"""
        help_win = tk.Toplevel(taclane_win)
        help_win.title("🔧 Guide Configuration Réseau")
        help_win.geometry("700x500")
        
        tk.Label(help_win, text="🔧 Configuration Réseau pour Taclane", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        help_text = tk.Text(help_win, bg=colors['white'], font=("Arial", 10), wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        config_help = """
🎯 OBJECTIF: Configurer votre interface réseau pour communiquer avec le Taclane

📍 Configuration requise:
• Taclane: 172.16.0.1 (équipement cible)
• Votre PC: 172.16.0.2 (adresse recommandée)
• Masque: 255.255.255.0 (/24)

══════════════════════════════════════════════════════════════════

🍎 CONFIGURATION macOS:

1️⃣ Méthode Terminal (Recommandée):
   sudo ifconfig en0 alias 172.16.0.2 netmask 255.255.255.0
   
2️⃣ Méthode Graphique:
   • Préférences Système → Réseau
   • Sélectionner votre interface (Wi-Fi/Ethernet)
   • Avancé → TCP/IP
   • Configurer IPv4: Manuellement
   • Adresse IP: 172.16.0.2
   • Masque: 255.255.255.0

══════════════════════════════════════════════════════════════════

🐧 CONFIGURATION Linux:

1️⃣ Méthode ip (Moderne):
   sudo ip addr add 172.16.0.2/24 dev eth0
   
2️⃣ Méthode ifconfig (Classique):
   sudo ifconfig eth0:1 172.16.0.2 netmask 255.255.255.0 up

══════════════════════════════════════════════════════════════════

🪟 CONFIGURATION Windows:

1️⃣ Méthode PowerShell (Administrateur):
   netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0
   
2️⃣ Méthode Graphique:
   • Panneau de configuration → Réseau et Internet
   • Modifier les paramètres de la carte
   • Clic droit sur votre interface → Propriétés
   • IPv4 → Utiliser l'adresse IP suivante
   • IP: 172.16.0.2, Masque: 255.255.255.0

══════════════════════════════════════════════════════════════════

✅ VÉRIFICATION après configuration:

1️⃣ Test ping:
   ping 172.16.0.1
   
2️⃣ Vérifier votre IP:
   • macOS/Linux: ifconfig ou ip addr
   • Windows: ipconfig
   
3️⃣ Test interface web:
   • https://172.16.0.1
   • http://172.16.0.1

══════════════════════════════════════════════════════════════════

⚠️ NOTES IMPORTANTES:

• Cette configuration est souvent temporaire (perdue au redémarrage)
• Sauvegardez votre config réseau actuelle avant modification
• L'adresse 172.16.0.2 ne doit pas être utilisée par un autre équipement
• Testez la connectivité avant d'accéder à l'interface web

💡 Une fois configuré, utilisez le bouton "🌐 Interface Web" pour accéder au Taclane!
        """
        
        help_text.insert(tk.END, config_help)
        help_text.config(state='disabled')
        
        # Boutons d'action
        btn_frame = tk.Frame(help_win)
        btn_frame.pack(pady=10)
        
        def copy_macos_cmd():
            help_win.clipboard_clear()
            help_win.clipboard_append("sudo ifconfig en0 alias 172.16.0.2 netmask 255.255.255.0")
            log_func("📋 Commande macOS copiée")
        
        def copy_linux_cmd():
            help_win.clipboard_clear()
            help_win.clipboard_append("sudo ip addr add 172.16.0.2/24 dev eth0")
            log_func("📋 Commande Linux copiée")
        
        def copy_windows_cmd():
            help_win.clipboard_clear()
            help_win.clipboard_append('netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0')
            log_func("📋 Commande Windows copiée")
        
        tk.Button(btn_frame, text="📋 Copier macOS", command=copy_macos_cmd,
                 bg='#007AFF', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📋 Copier Linux", command=copy_linux_cmd,
                 bg='#FF6B35', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📋 Copier Windows", command=copy_windows_cmd,
                 bg='#0078D4', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
    
    tk.Button(ip_frame, text="🌐 Config Réseau", command=check_network_config,
             bg=colors['warning'], fg=colors['white'], padx=10).pack(side=tk.LEFT, padx=5)
    
    # Outils de diagnostic
    diagnostic_frame = tk.LabelFrame(taclane_win, text="🔍 Outils de Diagnostic", 
                                   bg=colors['light'], font=("Arial", 11, "bold"))
    diagnostic_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # Grille d'outils de diagnostic
    diag_grid = tk.Frame(diagnostic_frame, bg=colors['light'])
    diag_grid.pack(padx=10, pady=10)
    
    def validate_network_config():
        """Valide la configuration réseau complète"""
        validation_win = tk.Toplevel(taclane_win)
        validation_win.title("✅ Validation Réseau")
        validation_win.geometry("600x400")
        
        tk.Label(validation_win, text="✅ Validation Configuration Réseau", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        validation_text = tk.Text(validation_win, bg=colors['white'], 
                                 font=("Consolas", 9))
        validation_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def run_validation():
            validation_text.delete(1.0, tk.END)
            validation_text.insert(tk.END, "🔍 Validation en cours...\n\n")
            validation_text.update()
            
            try:
                ip = ip_var.get()
                
                # 1. Vérifier interfaces locales
                validation_text.insert(tk.END, "1️⃣ Vérification interfaces locales...\n")
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                
                taclane_interfaces = []
                current_interface = None
                
                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t') and ':' in line:
                        current_interface = line.split(':')[0]
                    elif current_interface and 'inet 172.16.0.' in line:
                        ip_addr = line.split('inet ')[1].split()[0]
                        taclane_interfaces.append((current_interface, ip_addr))
                
                if taclane_interfaces:
                    validation_text.insert(tk.END, "   ✅ Interface(s) configurée(s):\n")
                    for interface, local_ip in taclane_interfaces:
                        validation_text.insert(tk.END, f"      • {interface}: {local_ip}\n")
                        if local_ip == "172.16.0.2":
                            validation_text.insert(tk.END, "      ✅ IP recommandée configurée!\n")
                else:
                    validation_text.insert(tk.END, "   ❌ Aucune interface dans le réseau 172.16.0.0/24\n")
                    validation_text.insert(tk.END, "   💡 Configuration requise: 172.16.0.2\n")
                
                # 2. Test ping
                validation_text.insert(tk.END, f"\n2️⃣ Test ping vers {ip}...\n")
                ping_result = subprocess.run(['ping', '-c', '3', '-W', '2000', ip], 
                                           capture_output=True, text=True, timeout=10)
                
                if ping_result.returncode == 0:
                    validation_text.insert(tk.END, f"   ✅ {ip} accessible\n")
                    # Extraire les stats
                    for line in ping_result.stdout.split('\n'):
                        if 'packets transmitted' in line:
                            validation_text.insert(tk.END, f"   📊 {line.strip()}\n")
                else:
                    validation_text.insert(tk.END, f"   ❌ {ip} non accessible\n")
                
                # 3. Test ports
                validation_text.insert(tk.END, f"\n3️⃣ Test des ports essentiels...\n")
                essential_ports = {80: "HTTP", 443: "HTTPS", 22: "SSH"}
                
                for port, service in essential_ports.items():
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((ip, port))
                        
                        if result == 0:
                            validation_text.insert(tk.END, f"   ✅ Port {port} ({service}): OUVERT\n")
                        else:
                            validation_text.insert(tk.END, f"   🔴 Port {port} ({service}): FERMÉ\n")
                        
                        sock.close()
                    except:
                        validation_text.insert(tk.END, f"   ❓ Port {port} ({service}): ERREUR\n")
                
                # 4. Recommandations finales
                validation_text.insert(tk.END, f"\n4️⃣ Recommandations:\n")
                if taclane_interfaces and ping_result.returncode == 0:
                    validation_text.insert(tk.END, "   🎉 Configuration validée! Vous pouvez:\n")
                    validation_text.insert(tk.END, f"      • Accéder via navigateur: https://{ip}\n")
                    validation_text.insert(tk.END, f"      • Utiliser les outils de diagnostic\n")
                    validation_text.insert(tk.END, f"      • Lancer le monitoring continu\n")
                else:
                    validation_text.insert(tk.END, "   ⚠️ Configuration incomplète:\n")
                    if not taclane_interfaces:
                        validation_text.insert(tk.END, "      • Configurez votre interface réseau (172.16.0.2)\n")
                    if ping_result.returncode != 0:
                        validation_text.insert(tk.END, "      • Vérifiez que le Taclane est allumé et connecté\n")
                
            except Exception as e:
                validation_text.insert(tk.END, f"\n❌ Erreur lors de la validation: {e}\n")
        
        # Lancer la validation automatiquement
        validation_win.after(500, run_validation)
        
        # Bouton pour relancer
        tk.Button(validation_win, text="🔄 Relancer Validation", 
                 command=run_validation, bg=colors['success'], 
                 fg=colors['white'], padx=20, pady=5).pack(pady=10)
    
    diagnostic_tools = [
        ("🏓 Ping Continu", lambda: start_continuous_ping(ip_var.get())),
        ("📊 Traceroute", lambda: run_traceroute(ip_var.get())),
        ("🔌 Scan Ports", lambda: run_port_scan(ip_var.get())),
        ("📈 Monitoring", lambda: start_monitoring(ip_var.get())),
        ("🌐 Interface Web", lambda: open_web_interface(ip_var.get())),
        ("📋 ARP Table", lambda: show_arp_info(ip_var.get())),
        ("✅ Valid. Réseau", lambda: validate_network_config()),
        ("🔧 Guide Config", lambda: show_network_config_help())
    ]
    
    for i, (name, command) in enumerate(diagnostic_tools):
        row, col = i // 4, i % 4  # 4 colonnes pour les 8 outils
        
        # Couleurs spéciales pour les nouveaux outils
        btn_color = colors['info']
        if "Valid. Réseau" in name:
            btn_color = colors['success']
        elif "Guide Config" in name:
            btn_color = colors['warning']
        
        btn = tk.Button(diag_grid, text=name, command=command,
                       bg=btn_color, fg=colors['white'], 
                       width=12, pady=5, font=("Arial", 9))
        btn.grid(row=row, column=col, padx=3, pady=5)
    
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
        """Ouvre l'interface web du Taclane avec vérification réseau"""
        def check_and_configure_network():
            try:
                # Vérifier si on a une interface dans le bon réseau
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                has_taclane_network = '172.16.0.' in result.stdout
                
                if not has_taclane_network:
                    # Demander confirmation pour configurer l'interface
                    config_net = tk.messagebox.askyesno(
                        "Configuration réseau",
                        f"Aucune interface trouvée dans le réseau 172.16.0.0/24.\n\n"
                        f"Pour accéder au Taclane ({ip}), votre interface doit avoir\n"
                        f"une adresse IP dans le même réseau (ex: 172.16.0.2).\n\n"
                        f"Voulez-vous configurer automatiquement l'interface réseau?",
                        icon='question'
                    )
                    
                    if config_net:
                        configure_interface_for_taclane()
                    else:
                        show_manual_config_instructions()
                        return
                
                # Continuer avec l'ouverture de l'interface web
                open_web_browser(ip)
                
            except Exception as e:
                log_func(f"❌ Erreur vérification réseau: {e}")
                open_web_browser(ip)  # Essayer quand même
        
        def configure_interface_for_taclane():
            """Configure automatiquement une interface pour le réseau Taclane"""
            try:
                import platform
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    # Trouver une interface disponible
                    result = subprocess.run(['route', 'get', 'default'], 
                                          capture_output=True, text=True)
                    
                    # Extraire l'interface par défaut
                    default_interface = None
                    for line in result.stdout.split('\n'):
                        if 'interface:' in line:
                            default_interface = line.split(':')[1].strip()
                            break
                    
                    if default_interface:
                        # Configurer un alias sur l'interface par défaut
                        cmd = f"sudo ifconfig {default_interface} alias 172.16.0.2 netmask 255.255.255.0"
                        
                        config_win = tk.Toplevel(taclane_win)
                        config_win.title("🔧 Configuration réseau")
                        config_win.geometry("600x400")
                        
                        tk.Label(config_win, text="🔧 Configuration de l'interface réseau", 
                                font=("Arial", 14, "bold")).pack(pady=10)
                        
                        tk.Label(config_win, text=f"Interface détectée: {default_interface}", 
                                font=("Arial", 11)).pack(pady=5)
                        
                        tk.Label(config_win, text="Commande à exécuter:", 
                                font=("Arial", 11, "bold")).pack(pady=(10,5))
                        
                        cmd_text = tk.Text(config_win, height=3, bg='#f0f0f0', 
                                         font=("Consolas", 10))
                        cmd_text.pack(padx=20, pady=5, fill=tk.X)
                        cmd_text.insert(tk.END, cmd)
                        cmd_text.config(state='disabled')
                        
                        instructions = """
🔧 Instructions:
1. Ouvrez un terminal
2. Copiez et exécutez la commande ci-dessus
3. Entrez votre mot de passe administrateur si demandé
4. L'interface aura l'adresse 172.16.0.2
5. Vous pourrez alors accéder au Taclane sur 172.16.0.1

⚠️ Cette configuration est temporaire et sera perdue au redémarrage.
                        """
                        
                        info_text = tk.Text(config_win, height=8, bg='white', 
                                          font=("Arial", 10), wrap=tk.WORD)
                        info_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
                        info_text.insert(tk.END, instructions)
                        info_text.config(state='disabled')
                        
                        def copy_command():
                            config_win.clipboard_clear()
                            config_win.clipboard_append(cmd)
                            log_func("📋 Commande copiée dans le presse-papier")
                        
                        tk.Button(config_win, text="📋 Copier la commande", 
                                 command=copy_command, bg=colors['info'], 
                                 fg=colors['white'], padx=20, pady=5).pack(pady=10)
                
                elif system == "Linux":
                    # Configuration Linux
                    show_linux_config_instructions()
                    
                elif system == "Windows":
                    # Configuration Windows
                    show_windows_config_instructions()
                    
            except Exception as e:
                log_func(f"❌ Erreur configuration interface: {e}")
                show_manual_config_instructions()
        
        def show_manual_config_instructions():
            """Affiche les instructions de configuration manuelle"""
            manual_win = tk.Toplevel(taclane_win)
            manual_win.title("📖 Configuration manuelle")
            manual_win.geometry("700x500")
            
            tk.Label(manual_win, text="📖 Configuration manuelle de l'interface réseau", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            instructions_text = tk.Text(manual_win, bg='white', font=("Arial", 10), 
                                      wrap=tk.WORD)
            instructions_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
            
            manual_instructions = """
🔧 Configuration manuelle par système d'exploitation:

═══════════════════════════════════════════════════════════════

🍎 macOS:
1. Ouvrez un terminal
2. Exécutez: sudo ifconfig en0 alias 172.16.0.2 netmask 255.255.255.0
   (remplacez 'en0' par votre interface réseau principale)
3. Vérifiez: ifconfig en0

🐧 Linux:
1. Ouvrez un terminal  
2. Exécutez: sudo ip addr add 172.16.0.2/24 dev eth0
   (remplacez 'eth0' par votre interface réseau)
3. Vérifiez: ip addr show eth0

🪟 Windows:
1. Ouvrez une invite de commande en tant qu'administrateur
2. Exécutez: netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0
   (remplacez "Ethernet" par le nom de votre interface)
3. Vérifiez: ipconfig

═══════════════════════════════════════════════════════════════

💡 Alternative - Configuration graphique:

🍎 macOS (Préférences Système):
• Aller dans Préférences Système > Réseau
• Sélectionner votre interface réseau
• Cliquer sur "Avancé..." > TCP/IP
• Ajouter une configuration manuelle avec 172.16.0.2

🐧 Linux (NetworkManager):
• Clic droit sur l'icône réseau
• Modifier les connexions
• Ajouter une nouvelle configuration avec IP 172.16.0.2/24

🪟 Windows (Panneau de configuration):
• Panneau de configuration > Réseau et Internet
• Modifier les paramètres de la carte
• Propriétés > IPv4 > Utiliser l'adresse IP suivante
• IP: 172.16.0.2, Masque: 255.255.255.0

═══════════════════════════════════════════════════════════════

⚠️ Important:
• Cette configuration permet la communication avec le Taclane
• L'adresse 172.16.0.2 ne doit pas être utilisée par un autre équipement
• Sauvegardez votre configuration réseau actuelle avant modification
• Cette configuration peut être temporaire selon vos besoins

🔗 Une fois configuré, vous pourrez accéder au Taclane via:
• https://172.16.0.1 (HTTPS recommandé)
• http://172.16.0.1 (HTTP)
            """
            
            instructions_text.insert(tk.END, manual_instructions)
            instructions_text.config(state='disabled')
        
        def show_linux_config_instructions():
            """Instructions spécifiques Linux"""
            linux_win = tk.Toplevel(taclane_win)
            linux_win.title("🐧 Configuration Linux")
            linux_win.geometry("600x400")
            
            tk.Label(linux_win, text="🐧 Configuration Linux", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            # Détecter l'interface principale
            try:
                result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                      capture_output=True, text=True)
                default_interface = "eth0"  # Fallback
                
                for line in result.stdout.split('\n'):
                    if 'dev' in line:
                        parts = line.split()
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            default_interface = parts[dev_index + 1]
                            break
                
                cmd = f"sudo ip addr add 172.16.0.2/24 dev {default_interface}"
                
                tk.Label(linux_win, text=f"Interface détectée: {default_interface}", 
                        font=("Arial", 11)).pack(pady=5)
                
                tk.Label(linux_win, text="Commande recommandée:", 
                        font=("Arial", 11, "bold")).pack(pady=(10,5))
                
                cmd_text = tk.Text(linux_win, height=2, bg='#f0f0f0', 
                                 font=("Consolas", 10))
                cmd_text.pack(padx=20, pady=5, fill=tk.X)
                cmd_text.insert(tk.END, cmd)
                cmd_text.config(state='disabled')
                
                def copy_linux_cmd():
                    linux_win.clipboard_clear()
                    linux_win.clipboard_append(cmd)
                    log_func("📋 Commande Linux copiée")
                
                tk.Button(linux_win, text="📋 Copier", command=copy_linux_cmd,
                         bg=colors['info'], fg=colors['white']).pack(pady=10)
                
            except Exception as e:
                log_func(f"❌ Erreur détection interface Linux: {e}")
        
        def show_windows_config_instructions():
            """Instructions spécifiques Windows"""
            windows_win = tk.Toplevel(taclane_win)
            windows_win.title("🪟 Configuration Windows")
            windows_win.geometry("600x400")
            
            tk.Label(windows_win, text="🪟 Configuration Windows", 
                    font=("Arial", 14, "bold")).pack(pady=10)
            
            cmd = 'netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0'
            
            tk.Label(windows_win, text="Commande PowerShell (Administrateur):", 
                    font=("Arial", 11, "bold")).pack(pady=(10,5))
            
            cmd_text = tk.Text(windows_win, height=2, bg='#f0f0f0', 
                             font=("Consolas", 10))
            cmd_text.pack(padx=20, pady=5, fill=tk.X)
            cmd_text.insert(tk.END, cmd)
            cmd_text.config(state='disabled')
            
            def copy_windows_cmd():
                windows_win.clipboard_clear()
                windows_win.clipboard_append(cmd)
                log_func("📋 Commande Windows copiée")
            
            tk.Button(windows_win, text="📋 Copier", command=copy_windows_cmd,
                     bg=colors['info'], fg=colors['white']).pack(pady=10)
        
        def open_web_browser(ip):
            """Ouvre le navigateur vers l'interface Taclane"""
            try:
                import webbrowser
                
                # Test de connectivité d'abord
                test_result = subprocess.run(['ping', '-c', '1', '-W', '2000', ip], 
                                           capture_output=True)
                
                if test_result.returncode != 0:
                    tk.messagebox.showwarning(
                        "Connectivité",
                        f"⚠️ Le Taclane ({ip}) ne répond pas au ping.\n\n"
                        f"Vérifiez que:\n"
                        f"• L'équipement est allumé\n"
                        f"• Votre interface réseau est configurée (172.16.0.2)\n"
                        f"• Le câble réseau est connecté"
                    )
                
                # Essayer HTTPS d'abord, puis HTTP
                urls = [f"https://{ip}", f"http://{ip}"]
                
                for url in urls:
                    try:
                        webbrowser.open(url)
                        log_func(f"🌐 Interface web ouverte: {url}")
                        log_func("💡 Assurez-vous que votre interface a l'IP 172.16.0.2")
                        break
                    except:
                        continue
                        
            except Exception as e:
                log_func(f"❌ Erreur ouverture interface web: {e}")
        
        # Lancer la vérification et configuration
        threading.Thread(target=check_and_configure_network, daemon=True).start()
    
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