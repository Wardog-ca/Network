#!/usr/bin/env python3

import subprocess
import platform

def test_network_interfaces():
    """Test de la fonction get_network_interfaces pour macOS"""
    print(f"Système détecté: {platform.system()}")
    print("\n=== Test de la commande ifconfig ===")
    
    try:
        output = subprocess.check_output(["ifconfig"], encoding="utf-8")
        print("Sortie brute de ifconfig:")
        print(output[:500] + "..." if len(output) > 500 else output)
        
        print("\n=== Parsing des interfaces ===")
        interfaces = {}
        current_interface = None
        
        for line in output.splitlines():
            if line and not line.startswith('\t') and ':' in line:
                # Nouvelle interface
                current_interface = line.split(':')[0]
                interfaces[current_interface] = {
                    'ipv4': [],
                    'ipv6': [],
                    'status': 'DOWN'
                }
                if 'UP' in line:
                    interfaces[current_interface]['status'] = 'UP'
                print(f"Interface trouvée: {current_interface} - Status: {interfaces[current_interface]['status']}")
            elif current_interface and '\tinet ' in line:
                # Adresse IPv4
                parts = line.strip().split()
                if len(parts) >= 2:
                    interfaces[current_interface]['ipv4'].append(parts[1])
                    print(f"  IPv4: {parts[1]}")
            elif current_interface and '\tinet6 ' in line:
                # Adresse IPv6
                parts = line.strip().split()
                if len(parts) >= 2 and not parts[1].startswith('fe80'):
                    interfaces[current_interface]['ipv6'].append(parts[1])
                    print(f"  IPv6: {parts[1]}")
        
        print(f"\n=== Résumé des interfaces ===")
        for name, data in interfaces.items():
            if name not in ['lo0']:  # Afficher toutes sauf loopback
                print(f"{name}: {data['status']} - IPv4: {data['ipv4']} - IPv6: {data['ipv6']}")
        
        return interfaces
        
    except Exception as e:
        print(f"Erreur: {e}")
        return {}

if __name__ == "__main__":
    interfaces = test_network_interfaces()