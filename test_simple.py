#!/usr/bin/env python3

import tkinter as tk
import subprocess
import platform

def test_tkinter():
    """Test simple de tkinter"""
    print("Testing tkinter...")
    
    try:
        root = tk.Tk()
        root.title("Test Tkinter")
        root.geometry("300x200")
        
        label = tk.Label(root, text="Tkinter fonctionne!", font=("Arial", 14))
        label.pack(pady=50)
        
        def close_app():
            root.destroy()
        
        button = tk.Button(root, text="Fermer", command=close_app)
        button.pack(pady=20)
        
        print("Fenêtre tkinter créée avec succès!")
        root.mainloop()
        
    except Exception as e:
        print(f"Erreur avec tkinter: {e}")

def test_network_detection():
    """Test de détection des interfaces réseau"""
    print("\nTesting network interface detection...")
    
    try:
        output = subprocess.check_output(["ifconfig"], encoding="utf-8")
        interfaces = {}
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
        
        print(f"Interfaces détectées: {len(interfaces)}")
        for name, data in interfaces.items():
            if name not in ['lo0'] and data['ipv4']:
                print(f"  {name}: {data['status']} - {data['ipv4']}")
        
        return len(interfaces) > 0
        
    except Exception as e:
        print(f"Erreur détection réseau: {e}")
        return False

if __name__ == "__main__":
    print("=== Test des composants ===")
    
    # Test réseau
    network_ok = test_network_detection()
    
    # Test tkinter (optionnel - commenté pour éviter de bloquer)
    print(f"\nRéseau OK: {network_ok}")
    print("Pour tester tkinter, décommentez la ligne ci-dessous:")
    print("# test_tkinter()")
    
    # Décommentez cette ligne pour tester tkinter visuellement:
    test_tkinter()