#!/usr/bin/env python3
"""
Serveur TFTP simple et robuste
Peut être utilisé indépendamment ou intégré
"""

import socket
import os
import threading
import time
from pathlib import Path

class SimpleTFTPServer:
    def __init__(self, host='0.0.0.0', port=6969, directory='.'):
        self.host = host
        self.port = port
        self.directory = Path(directory).resolve()
        self.socket = None
        self.running = False
        
    def start(self):
        """Démarre le serveur TFTP"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)
            
            self.running = True
            print(f"🚀 Serveur TFTP démarré sur {self.host}:{self.port}")
            print(f"📁 Répertoire: {self.directory}")
            
            while self.running:
                try:
                    data, client_addr = self.socket.recvfrom(1024)
                    self.handle_request(data, client_addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"❌ Erreur: {e}")
                        
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {e}")
        finally:
            self.stop()
    
    def handle_request(self, data, client_addr):
        """Traite une requête TFTP"""
        try:
            if len(data) < 4:
                return
                
            opcode = int.from_bytes(data[:2], 'big')
            
            if opcode == 1:  # Read Request (RRQ)
                self.handle_read_request(data[2:], client_addr)
            elif opcode == 2:  # Write Request (WRQ)
                self.handle_write_request(data[2:], client_addr)
            else:
                self.send_error(5, "Unknown opcode", client_addr)
                
        except Exception as e:
            print(f"❌ Erreur traitement requête: {e}")
            self.send_error(0, str(e), client_addr)
    
    def handle_read_request(self, data, client_addr):
        """Traite une demande de lecture de fichier"""
        try:
            # Parser le nom de fichier
            parts = data.split(b'\x00')
            if len(parts) < 2:
                self.send_error(4, "Invalid filename", client_addr)
                return
                
            filename = parts[0].decode('utf-8')
            filepath = self.directory / filename
            
            print(f"📄 Demande de lecture: {filename} de {client_addr[0]}")
            
            # Vérifier que le fichier existe et est dans le répertoire autorisé
            if not filepath.exists():
                self.send_error(1, "File not found", client_addr)
                return
                
            if not str(filepath).startswith(str(self.directory)):
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
                    
            print(f"✅ Fichier {filename} envoyé à {client_addr[0]}")
            
        except Exception as e:
            print(f"❌ Erreur lecture fichier: {e}")
            self.send_error(0, str(e), client_addr)
    
    def handle_write_request(self, data, client_addr):
        """Traite une demande d'écriture de fichier"""
        # Envoyer ACK pour dire qu'on accepte (implémentation basique)
        self.send_ack(0, client_addr)
        print(f"📝 Demande d'écriture de {client_addr[0]} (non implémentée)")
    
    def send_data(self, block_num, data, client_addr):
        """Envoie un bloc de données"""
        packet = b'\x00\x03' + block_num.to_bytes(2, 'big') + data
        self.socket.sendto(packet, client_addr)
    
    def send_ack(self, block_num, client_addr):
        """Envoie un ACK"""
        packet = b'\x00\x04' + block_num.to_bytes(2, 'big')
        self.socket.sendto(packet, client_addr)
    
    def send_error(self, error_code, message, client_addr):
        """Envoie une erreur"""
        packet = b'\x00\x05' + error_code.to_bytes(2, 'big') + message.encode('utf-8') + b'\x00'
        self.socket.sendto(packet, client_addr)
        print(f"❌ Erreur envoyée à {client_addr[0]}: {message}")
    
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("🛑 Serveur TFTP arrêté")

def main():
    """Lance le serveur TFTP en mode standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Serveur TFTP simple')
    parser.add_argument('--host', default='0.0.0.0', help='Adresse IP (défaut: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=6969, help='Port (défaut: 6969)')
    parser.add_argument('--dir', default='.', help='Répertoire à partager (défaut: .)')
    
    args = parser.parse_args()
    
    server = SimpleTFTPServer(args.host, args.port, args.dir)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
        server.stop()

if __name__ == '__main__':
    main()