#!/usr/bin/env python3

def start_tftp_server_replacement():
    """Nouvelle fonction TFTP améliorée à insérer dans network.py"""
    return '''
def start_tftp_server():
    """Démarre un serveur TFTP avec interface graphique améliorée"""
    try:
        from tftp_interface import create_tftp_interface
        create_tftp_interface(root, COLORS, log)
    except ImportError:
        # Fallback - interface TFTP basique intégrée
        log("ℹ️ Utilisation de l'interface TFTP intégrée")
        
        tftp_win = tk.Toplevel(root)
        tftp_win.title("📁 Serveur TFTP")
        tftp_win.geometry("650x550")
        tftp_win.configure(bg=COLORS['light'])
        
        # Variables globales pour le serveur
        tftp_server_instance = None
        server_thread = None
        request_count = [0]
        file_count = [0]
        
        # En-tête
        header = tk.Frame(tftp_win, bg=COLORS['primary'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="📁 Serveur TFTP", 
                font=("Arial", 14, "bold"), 
                fg=COLORS['white'], bg=COLORS['primary']).pack(pady=12)
        
        # Configuration
        config_frame = tk.LabelFrame(tftp_win, text="Configuration", bg=COLORS['light'])
        config_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Dossier
        tk.Label(config_frame, text="Dossier:", bg=COLORS['light']).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        folder_var = tk.StringVar(value=os.getcwd())
        folder_entry = tk.Entry(config_frame, textvariable=folder_var, width=40)
        folder_entry.grid(row=0, column=1, padx=5, pady=5)
        
        def browse_folder():
            folder = filedialog.askdirectory(initialdir=folder_var.get())
            if folder:
                folder_var.set(folder)
        
        tk.Button(config_frame, text="📂", command=browse_folder, 
                 bg=COLORS['info'], fg=COLORS['white']).grid(row=0, column=2, padx=5, pady=5)
        
        # Port
        tk.Label(config_frame, text="Port:", bg=COLORS['light']).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        port_var = tk.StringVar(value="6969")
        port_entry = tk.Entry(config_frame, textvariable=port_var, width=10)
        port_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Statut
        status_frame = tk.LabelFrame(tftp_win, text="Statut", bg=COLORS['light'])
        status_frame.pack(fill=tk.X, padx=15, pady=10)
        
        status_label = tk.Label(status_frame, text="🔴 Arrêté", 
                               font=("Arial", 11, "bold"), 
                               fg=COLORS['danger'], bg=COLORS['light'])
        status_label.pack(pady=8)
        
        stats_frame = tk.Frame(status_frame, bg=COLORS['light'])
        stats_frame.pack()
        
        requests_label = tk.Label(stats_frame, text="Requêtes: 0", bg=COLORS['light'])
        requests_label.pack(side=tk.LEFT, padx=10)
        
        files_label = tk.Label(stats_frame, text="Fichiers: 0", bg=COLORS['light'])
        files_label.pack(side=tk.LEFT, padx=10)
        
        # Serveur TFTP intégré
        class SimpleTFTPServer:
            def __init__(self, host, port, directory):
                self.host = host
                self.port = port
                self.directory = directory
                self.socket = None
                self.running = False
                
            def start(self):
                try:
                    import socket as sock
                    self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
                    self.socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
                    self.socket.bind((self.host, self.port))
                    self.socket.settimeout(1.0)
                    
                    self.running = True
                    log(f"🚀 Serveur TFTP sur {self.host}:{self.port}")
                    status_label.config(text=f"🟢 Actif:{self.port}", fg=COLORS['success'])
                    start_btn.config(state='disabled')
                    stop_btn.config(state='normal')
                    
                    while self.running:
                        try:
                            data, client_addr = self.socket.recvfrom(1024)
                            request_count[0] += 1
                            requests_label.config(text=f"Requêtes: {request_count[0]}")
                            self.handle_request(data, client_addr)
                        except sock.timeout:
                            continue
                        except Exception as e:
                            if self.running:
                                log(f"❌ Erreur: {e}")
                                
                except Exception as e:
                    log(f"❌ Erreur serveur: {e}")
                    status_label.config(text="🔴 Erreur", fg=COLORS['danger'])
                finally:
                    self.stop()
            
            def handle_request(self, data, client_addr):
                try:
                    if len(data) < 4:
                        return
                        
                    opcode = int.from_bytes(data[:2], 'big')
                    
                    if opcode == 1:  # Read Request
                        self.handle_read_request(data[2:], client_addr)
                    else:
                        self.send_error(5, "Unsupported", client_addr)
                        
                except Exception as e:
                    self.send_error(0, str(e), client_addr)
            
            def handle_read_request(self, data, client_addr):
                try:
                    parts = data.split(b'\\x00')
                    if len(parts) < 2:
                        self.send_error(4, "Invalid filename", client_addr)
                        return
                        
                    filename = parts[0].decode('utf-8')
                    filepath = os.path.join(self.directory, filename)
                    
                    log(f"📄 Demande: {filename} ({client_addr[0]})")
                    
                    if not os.path.exists(filepath):
                        self.send_error(1, "File not found", client_addr)
                        return
                    
                    # Lire et envoyer fichier par blocs de 512 octets
                    with open(filepath, 'rb') as f:
                        block_num = 1
                        while True:
                            chunk = f.read(512)
                            self.send_data(block_num, chunk, client_addr)
                            if len(chunk) < 512:
                                break
                            block_num += 1
                            
                    file_count[0] += 1
                    files_label.config(text=f"Fichiers: {file_count[0]}")
                    log(f"✅ {filename} envoyé")
                    
                except Exception as e:
                    log(f"❌ Erreur fichier: {e}")
                    self.send_error(0, str(e), client_addr)
            
            def send_data(self, block_num, data, client_addr):
                packet = b'\\x00\\x03' + block_num.to_bytes(2, 'big') + data
                self.socket.sendto(packet, client_addr)
            
            def send_error(self, error_code, message, client_addr):
                packet = b'\\x00\\x05' + error_code.to_bytes(2, 'big') + message.encode('utf-8') + b'\\x00'
                self.socket.sendto(packet, client_addr)
                log(f"❌ Erreur {client_addr[0]}: {message}")
            
            def stop(self):
                self.running = False
                if self.socket:
                    self.socket.close()
                status_label.config(text="🔴 Arrêté", fg=COLORS['danger'])
                start_btn.config(state='normal')
                stop_btn.config(state='disabled')
                log("🛑 Serveur TFTP arrêté")
        
        # Contrôles
        controls_frame = tk.Frame(tftp_win, bg=COLORS['light'])
        controls_frame.pack(fill=tk.X, padx=15, pady=10)
        
        def start_server():
            nonlocal tftp_server_instance, server_thread
            try:
                port = int(port_var.get())
                folder = folder_var.get()
                
                if not os.path.exists(folder):
                    log("❌ Dossier inexistant")
                    return
                
                tftp_server_instance = SimpleTFTPServer("0.0.0.0", port, folder)
                server_thread = threading.Thread(target=tftp_server_instance.start, daemon=True)
                server_thread.start()
                
            except ValueError:
                log("❌ Port invalide")
            except Exception as e:
                log(f"❌ Erreur: {e}")
        
        def stop_server():
            nonlocal tftp_server_instance
            if tftp_server_instance:
                tftp_server_instance.stop()
        
        start_btn = tk.Button(controls_frame, text="▶️ Démarrer", command=start_server,
                             bg=COLORS['success'], fg=COLORS['white'], padx=15, pady=3)
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = tk.Button(controls_frame, text="⏹️ Arrêter", command=stop_server,
                            bg=COLORS['danger'], fg=COLORS['white'], padx=15, pady=3, state='disabled')
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Test
        def test_server():
            try:
                port = int(port_var.get())
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                test_socket.settimeout(3.0)
                
                # Test RRQ pour README.md
                request = b'\\x00\\x01' + b'README.md' + b'\\x00' + b'octet' + b'\\x00'
                test_socket.sendto(request, ('127.0.0.1', port))
                
                data, addr = test_socket.recvfrom(1024)
                if len(data) >= 4 and data[:2] == b'\\x00\\x03':
                    log("✅ Test TFTP réussi!")
                else:
                    log("⚠️ Réponse serveur inattendue")
                    
                test_socket.close()
                
            except Exception as e:
                log(f"❌ Test échoué: {e}")
        
        tk.Button(controls_frame, text="🧪 Test", command=test_server,
                 bg=COLORS['warning'], fg=COLORS['white'], padx=10, pady=3).pack(side=tk.LEFT, padx=5)
        
        # Informations
        info_frame = tk.LabelFrame(tftp_win, text="Informations", bg=COLORS['light'])
        info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        info_text = tk.Text(info_frame, height=6, bg=COLORS['white'], wrap=tk.WORD,
                           font=("Consolas", 9))
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        info_content = """📖 Serveur TFTP (Trivial File Transfer Protocol)

🔧 Utilisation:
1. Sélectionnez le dossier à partager
2. Configurez le port (6969 par défaut, 69 pour standard)
3. Démarrez le serveur

💡 Test avec curl:
curl -o local.txt tftp://127.0.0.1:6969/fichier.txt

⚠️ Ce serveur implémente TFTP basique (lecture seule).
Il supporte les fichiers jusqu'à quelques MB."""
        
        info_text.insert(tk.END, info_content)
        info_text.config(state='disabled')
        
        # Fermeture propre
        def on_closing():
            nonlocal tftp_server_instance
            if tftp_server_instance and tftp_server_instance.running:
                stop_server()
            tftp_win.destroy()
        
        tftp_win.protocol("WM_DELETE_WINDOW", on_closing)
'''

if __name__ == "__main__":
    print(start_tftp_server_replacement())