#!/usr/bin/env python3
"""
Interface TFTP intégrée pour network.py
"""

import tkinter as tk
from tkinter import filedialog
import os
import threading
import socket
import time

def create_tftp_interface(parent, colors, log_func):
    """Crée l'interface TFTP complète"""
    
    tftp_win = tk.Toplevel(parent)
    tftp_win.title("📁 Serveur TFTP Professional")
    tftp_win.geometry("700x600")
    tftp_win.configure(bg=colors['light'])
    
    # Variables globales pour le serveur
    tftp_server_instance = None
    server_thread = None
    
    # En-tête
    header = tk.Frame(tftp_win, bg=colors['primary'], height=60)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    tk.Label(header, text="📁 Serveur TFTP Professional", 
            font=("Arial", 16, "bold"), 
            fg=colors['white'], bg=colors['primary']).pack(pady=15)
    
    # Configuration
    config_frame = tk.LabelFrame(tftp_win, text="⚙️ Configuration", bg=colors['light'])
    config_frame.pack(fill=tk.X, padx=15, pady=10)
    
    # Dossier de partage
    tk.Label(config_frame, text="📂 Dossier partagé:", bg=colors['light']).grid(row=0, column=0, sticky='w', padx=5, pady=5)
    
    folder_var = tk.StringVar(value=os.getcwd())
    folder_entry = tk.Entry(config_frame, textvariable=folder_var, width=45)
    folder_entry.grid(row=0, column=1, padx=5, pady=5)
    
    def browse_folder():
        folder = filedialog.askdirectory(initialdir=folder_var.get())
        if folder:
            folder_var.set(folder)
    
    tk.Button(config_frame, text="📂 Parcourir", command=browse_folder, 
             bg=colors['info'], fg=colors['white']).grid(row=0, column=2, padx=5, pady=5)
    
    # Port et adresse
    tk.Label(config_frame, text="🌐 Adresse:", bg=colors['light']).grid(row=1, column=0, sticky='w', padx=5, pady=5)
    host_var = tk.StringVar(value="0.0.0.0")
    host_entry = tk.Entry(config_frame, textvariable=host_var, width=15)
    host_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
    
    tk.Label(config_frame, text="🔌 Port:", bg=colors['light']).grid(row=2, column=0, sticky='w', padx=5, pady=5)
    port_var = tk.StringVar(value="6969")
    port_entry = tk.Entry(config_frame, textvariable=port_var, width=10)
    port_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
    
    tk.Label(config_frame, text="💡 Utilisez 69 pour le port TFTP standard (nécessite des privilèges root)", 
            font=("Arial", 9), fg=colors['secondary'], bg=colors['light']).grid(row=3, column=0, columnspan=3, sticky='w', padx=5)
    
    # Statut
    status_frame = tk.LabelFrame(tftp_win, text="📊 Statut du serveur", bg=colors['light'])
    status_frame.pack(fill=tk.X, padx=15, pady=10)
    
    status_label = tk.Label(status_frame, text="🔴 Arrêté", 
                           font=("Arial", 12, "bold"), 
                           fg=colors['danger'], bg=colors['light'])
    status_label.pack(pady=10)
    
    # Statistiques
    stats_frame = tk.Frame(status_frame, bg=colors['light'])
    stats_frame.pack(fill=tk.X, padx=10, pady=5)
    
    requests_label = tk.Label(stats_frame, text="📥 Requêtes: 0", bg=colors['light'])
    requests_label.pack(side=tk.LEFT, padx=10)
    
    files_label = tk.Label(stats_frame, text="📄 Fichiers: 0", bg=colors['light'])
    files_label.pack(side=tk.LEFT, padx=10)
    
    # Contrôles
    controls_frame = tk.Frame(tftp_win, bg=colors['light'])
    controls_frame.pack(fill=tk.X, padx=15, pady=10)
    
    class IntegratedTFTPServer:
        def __init__(self, host, port, directory):
            self.host = host
            self.port = port
            self.directory = directory
            self.socket = None
            self.running = False
            self.request_count = 0
            self.file_count = 0
            
        def start(self):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind((self.host, self.port))
                self.socket.settimeout(1.0)
                
                self.running = True
                log_func(f"🚀 Serveur TFTP démarré sur {self.host}:{self.port}")
                log_func(f"📁 Dossier partagé: {self.directory}")
                
                status_label.config(text=f"🟢 Actif sur {self.host}:{self.port}", fg=colors['success'])
                start_btn.config(state='disabled')
                stop_btn.config(state='normal')
                
                while self.running:
                    try:
                        data, client_addr = self.socket.recvfrom(1024)
                        self.request_count += 1
                        requests_label.config(text=f"📥 Requêtes: {self.request_count}")
                        self.handle_request(data, client_addr)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.running:
                            log_func(f"❌ Erreur: {e}")
                            
            except Exception as e:
                log_func(f"❌ Erreur démarrage serveur: {e}")
                status_label.config(text="🔴 Erreur", fg=colors['danger'])
            finally:
                self.stop()
        
        def handle_request(self, data, client_addr):
            try:
                if len(data) < 4:
                    return
                    
                opcode = int.from_bytes(data[:2], 'big')
                
                if opcode == 1:  # Read Request (RRQ)
                    self.handle_read_request(data[2:], client_addr)
                elif opcode == 2:  # Write Request (WRQ)
                    self.send_error(0, "Write not supported", client_addr)
                else:
                    self.send_error(5, "Unknown opcode", client_addr)
                    
            except Exception as e:
                log_func(f"❌ Erreur traitement requête: {e}")
                self.send_error(0, str(e), client_addr)
        
        def handle_read_request(self, data, client_addr):
            try:
                parts = data.split(b'\x00')
                if len(parts) < 2:
                    self.send_error(4, "Invalid filename", client_addr)
                    return
                    
                filename = parts[0].decode('utf-8')
                filepath = os.path.join(self.directory, filename)
                
                log_func(f"📄 Demande de lecture: {filename} de {client_addr[0]}")
                
                if not os.path.exists(filepath):
                    self.send_error(1, "File not found", client_addr)
                    return
                    
                if not os.path.commonpath([self.directory, filepath]) == self.directory:
                    self.send_error(2, "Access violation", client_addr)
                    return
                    
                # Lire et envoyer le fichier
                with open(filepath, 'rb') as f:
                    block_num = 1
                    while True:
                        chunk = f.read(512)
                        self.send_data(block_num, chunk, client_addr)
                        
                        if len(chunk) < 512:
                            break
                        block_num += 1
                        
                self.file_count += 1
                files_label.config(text=f"📄 Fichiers: {self.file_count}")
                log_func(f"✅ Fichier {filename} envoyé à {client_addr[0]}")
                
            except Exception as e:
                log_func(f"❌ Erreur lecture fichier: {e}")
                self.send_error(0, str(e), client_addr)
        
        def send_data(self, block_num, data, client_addr):
            packet = b'\x00\x03' + block_num.to_bytes(2, 'big') + data
            self.socket.sendto(packet, client_addr)
        
        def send_error(self, error_code, message, client_addr):
            packet = b'\x00\x05' + error_code.to_bytes(2, 'big') + message.encode('utf-8') + b'\x00'
            self.socket.sendto(packet, client_addr)
            log_func(f"❌ Erreur envoyée à {client_addr[0]}: {message}")
        
        def stop(self):
            self.running = False
            if self.socket:
                self.socket.close()
            log_func("🛑 Serveur TFTP arrêté")
            status_label.config(text="🔴 Arrêté", fg=colors['danger'])
            start_btn.config(state='normal')
            stop_btn.config(state='disabled')
    
    def start_server():
        nonlocal tftp_server_instance, server_thread
        try:
            port = int(port_var.get())
            host = host_var.get()
            folder = folder_var.get()
            
            if not os.path.exists(folder):
                log_func("❌ Le dossier spécifié n'existe pas", level="ERROR")
                return
            
            # Créer et démarrer le serveur
            tftp_server_instance = IntegratedTFTPServer(host, port, folder)
            server_thread = threading.Thread(target=tftp_server_instance.start, daemon=True)
            server_thread.start()
            
        except ValueError:
            log_func("❌ Port invalide", level="ERROR")
        except Exception as e:
            log_func(f"❌ Erreur démarrage serveur TFTP: {e}", level="ERROR")
            status_label.config(text="🔴 Erreur", fg=colors['danger'])
    
    def stop_server():
        nonlocal tftp_server_instance
        try:
            if tftp_server_instance:
                tftp_server_instance.stop()
        except Exception as e:
            log_func(f"❌ Erreur arrêt serveur: {e}", level="ERROR")
    
    start_btn = tk.Button(controls_frame, text="▶️ Démarrer", command=start_server,
                         bg=colors['success'], fg=colors['white'], padx=20, pady=5,
                         font=("Arial", 10, "bold"))
    start_btn.pack(side=tk.LEFT, padx=5)
    
    stop_btn = tk.Button(controls_frame, text="⏹️ Arrêter", command=stop_server,
                        bg=colors['danger'], fg=colors['white'], padx=20, pady=5, state='disabled',
                        font=("Arial", 10, "bold"))
    stop_btn.pack(side=tk.LEFT, padx=5)
    
    # Informations et test
    info_frame = tk.LabelFrame(tftp_win, text="📖 Informations et Tests", bg=colors['light'])
    info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
    # Zone de texte pour les informations
    info_text = tk.Text(info_frame, height=8, bg=colors['white'], wrap=tk.WORD)
    scrollbar = tk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
    info_text.configure(yscrollcommand=scrollbar.set)
    
    info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    info_content = """
📖 Utilisation du serveur TFTP:

1. 📂 Sélectionnez le dossier à partager
2. 🔧 Configurez l'adresse et le port 
3. ▶️ Cliquez sur "Démarrer" pour lancer le serveur
4. 🌐 Les clients TFTP peuvent maintenant accéder aux fichiers

💡 Commandes de test:
• curl -o fichier_local.txt tftp://IP:PORT/fichier_distant.txt
• tftp IP PORT -c get fichier_distant.txt fichier_local.txt

🔧 Test avec Python:
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
request = b'\\x00\\x01' + b'README.md' + b'\\x00' + b'octet' + b'\\x00'
sock.sendto(request, ('127.0.0.1', 6969))
data, addr = sock.recvfrom(1024)
print(f"Réponse: {data}")

⚠️ Note: Ce serveur TFTP implémente le protocole TFTP basique (RFC 1350).
Il supporte uniquement les requêtes de lecture (RRQ).
    """
    
    info_text.insert(tk.END, info_content)
    info_text.config(state='disabled')
    
    # Boutons d'action supplémentaires
    action_frame = tk.Frame(tftp_win, bg=colors['light'])
    action_frame.pack(fill=tk.X, padx=15, pady=5)
    
    def test_tftp():
        """Test simple du serveur TFTP"""
        try:
            port = int(port_var.get())
            host = host_var.get() if host_var.get() != "0.0.0.0" else "127.0.0.1"
            
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.settimeout(5.0)
            
            # Créer une requête RRQ pour README.md
            filename = b'README.md'
            mode = b'octet'
            rrq_packet = b'\x00\x01' + filename + b'\x00' + mode + b'\x00'
            
            test_sock.sendto(rrq_packet, (host, port))
            
            # Attendre la réponse
            data, addr = test_sock.recvfrom(1024)
            
            if len(data) >= 4:
                opcode = int.from_bytes(data[:2], 'big')
                if opcode == 3:  # DATA
                    log_func("✅ Test TFTP réussi - Serveur répond correctement")
                elif opcode == 5:  # ERROR
                    error_msg = data[4:].decode('utf-8', errors='ignore')
                    log_func(f"⚠️ Test TFTP - Erreur serveur: {error_msg}")
                else:
                    log_func(f"❓ Test TFTP - Réponse inattendue: opcode {opcode}")
            else:
                log_func("❌ Test TFTP - Réponse invalide")
                
            test_sock.close()
            
        except socket.timeout:
            log_func("❌ Test TFTP - Timeout (serveur non démarré?)")
        except Exception as e:
            log_func(f"❌ Test TFTP échoué: {e}")
    
    def start_http_alternative():
        """Lance un serveur HTTP simple comme alternative"""
        try:
            import http.server
            import socketserver
            import webbrowser
            
            http_port = 8080
            folder = folder_var.get()
            
            # Changer le répertoire de travail
            original_dir = os.getcwd()
            os.chdir(folder)
            
            def run_http():
                with socketserver.TCPServer(("", http_port), http.server.SimpleHTTPRequestHandler) as httpd:
                    log_func(f"🌐 Serveur HTTP démarré sur http://localhost:{http_port}")
                    log_func(f"📁 Dossier: {folder}")
                    httpd.serve_forever()
            
            http_thread = threading.Thread(target=run_http, daemon=True)
            http_thread.start()
            
            # Ouvrir dans le navigateur
            webbrowser.open(f"http://localhost:{http_port}")
            
        except Exception as e:
            log_func(f"❌ Erreur serveur HTTP: {e}", level="ERROR")
        finally:
            os.chdir(original_dir)
    
    tk.Button(action_frame, text="🧪 Tester TFTP", command=test_tftp,
             bg=colors['warning'], fg=colors['white'], padx=15, pady=3).pack(side=tk.LEFT, padx=5)
    
    tk.Button(action_frame, text="🌐 HTTP Alternative", command=start_http_alternative,
             bg=colors['info'], fg=colors['white'], padx=15, pady=3).pack(side=tk.LEFT, padx=5)
    
    # Fermeture propre de la fenêtre
    def on_closing():
        nonlocal tftp_server_instance
        if tftp_server_instance and tftp_server_instance.running:
            stop_server()
            time.sleep(0.5)  # Attendre l'arrêt
        tftp_win.destroy()
    
    tftp_win.protocol("WM_DELETE_WINDOW", on_closing)
    
    return tftp_win