#!/usr/bin/env python3
"""
Test du serveur TFTP
"""

import os
import subprocess
import time
import threading
from tftp_server import SimpleTFTPServer

def test_tftp_server():
    """Test le serveur TFTP"""
    print("🧪 Test du serveur TFTP")
    
    # Créer un fichier de test
    test_file = "test_tftp.txt"
    with open(test_file, 'w') as f:
        f.write("Ceci est un test TFTP!\nLe serveur fonctionne correctement.\n")
    
    # Démarrer le serveur en arrière-plan
    server = SimpleTFTPServer('127.0.0.1', 6969, '.')
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    
    time.sleep(1)  # Attendre que le serveur démarre
    
    # Tester avec curl (si disponible)
    try:
        print("📥 Test de téléchargement avec curl...")
        result = subprocess.run([
            'curl', '-o', 'downloaded_test.txt', 
            f'tftp://127.0.0.1:6969/{test_file}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Téléchargement réussi avec curl!")
            if os.path.exists('downloaded_test.txt'):
                with open('downloaded_test.txt', 'r') as f:
                    content = f.read()
                print(f"📄 Contenu téléchargé: {content}")
                os.remove('downloaded_test.txt')
        else:
            print(f"❌ Erreur curl: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Curl non disponible ou erreur: {e}")
    
    # Tester avec tftp client (si disponible)
    try:
        print("📥 Test avec client tftp natif...")
        # Sur macOS, le client tftp est disponible
        cmd = f"""
expect -c '
spawn tftp 127.0.0.1 6969
expect "tftp>"
send "get {test_file} downloaded_test2.txt\\r"
expect "tftp>"
send "quit\\r"
expect eof
'
"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if os.path.exists('downloaded_test2.txt'):
            print("✅ Téléchargement réussi avec tftp client!")
            with open('downloaded_test2.txt', 'r') as f:
                content = f.read()
            print(f"📄 Contenu téléchargé: {content}")
            os.remove('downloaded_test2.txt')
        else:
            print("❌ Téléchargement avec tftp client échoué")
            
    except Exception as e:
        print(f"❌ Client tftp non disponible ou erreur: {e}")
    
    # Test manuel avec socket
    try:
        print("📥 Test avec socket Python...")
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Construire requête RRQ (Read Request)
        filename = test_file.encode('utf-8')
        mode = b'octet'
        rrq_packet = b'\x00\x01' + filename + b'\x00' + mode + b'\x00'
        
        sock.sendto(rrq_packet, ('127.0.0.1', 6969))
        
        # Recevoir la réponse
        data, addr = sock.recvfrom(1024)
        
        if len(data) >= 4 and data[:2] == b'\x00\x03':  # DATA packet
            content = data[4:]  # Skip opcode and block number
            print(f"✅ Réception réussie via socket!")
            print(f"📄 Contenu reçu: {content.decode('utf-8')}")
        else:
            print(f"❌ Réponse inattendue: {data.hex()}")
            
        sock.close()
        
    except Exception as e:
        print(f"❌ Erreur test socket: {e}")
    
    # Nettoyer
    server.stop()
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("🏁 Test terminé")

if __name__ == '__main__':
    test_tftp_server()