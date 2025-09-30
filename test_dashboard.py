#!/usr/bin/env python3

import subprocess
import platform

def get_network_interfaces():
    """Récupère toutes les interfaces réseau et leurs adresses IP"""
    system = platform.system()
    interfaces = {}
    
    try:
        if system == "Darwin":
            # macOS - utiliser ifconfig
            output = subprocess.check_output(["ifconfig"], encoding="utf-8")
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
                elif current_interface and '\tinet ' in line:
                    # Adresse IPv4
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        interfaces[current_interface]['ipv4'].append(parts[1])
                elif current_interface and '\tinet6 ' in line:
                    # Adresse IPv6
                    parts = line.strip().split()
                    if len(parts) >= 2 and not parts[1].startswith('fe80'):
                        interfaces[current_interface]['ipv6'].append(parts[1])
                        
    except Exception as e:
        print(f"Erreur lors de la récupération des interfaces: {str(e)}")
    
    return interfaces

def simulate_dashboard():
    """Simule ce que le dashboard devrait afficher"""
    interfaces = get_network_interfaces()
    
    print("=== SIMULATION DU DASHBOARD ===")
    print(f"Interfaces détectées: {len(interfaces)}")
    
    # Filtrer comme le fait le dashboard (avec nouveau filtrage)
    filtered_interfaces = {}
    for k, v in interfaces.items():
        if k in ['lo', 'lo0', 'Loopback']:
            continue
        if k.startswith(('anpi', 'awdl', 'llw', 'gif', 'stf')):
            continue
        if k.startswith('utun') and not v['ipv4'] and not v['ipv6']:
            continue
        filtered_interfaces[k] = v
    
    print(f"Interfaces après filtrage (sans système): {len(filtered_interfaces)}")
    
    total_interfaces = len(filtered_interfaces)
    active_interfaces = len([k for k, v in filtered_interfaces.items() if v['status'] == 'UP'])
    
    print(f"Statistiques: {active_interfaces}/{total_interfaces} actives")
    print()
    
    # Simuler les cartes d'interface
    for iface_name, iface_data in filtered_interfaces.items():
        print(f"--- CARTE INTERFACE: {iface_name} ---")
        
        # Choisir l'icône selon le type d'interface
        if 'wlan' in iface_name.lower() or 'wifi' in iface_name.lower() or 'wl' in iface_name.lower():
            type_icon = "📶"  # WiFi
        elif 'eth' in iface_name.lower() or 'enp' in iface_name.lower() or 'ens' in iface_name.lower() or 'en' in iface_name.lower():
            type_icon = "🔌"  # Ethernet
        elif 'ppp' in iface_name.lower() or 'tun' in iface_name.lower() or 'vpn' in iface_name.lower():
            type_icon = "🔒"  # VPN/Tunnel
        elif 'docker' in iface_name.lower() or 'br-' in iface_name.lower() or 'bridge' in iface_name.lower():
            type_icon = "🐳"  # Docker/Bridge
        else:
            type_icon = "🌐"  # Interface générique
        
        status_icon = "🟢" if iface_data['status'] == 'UP' else "🔴"
        
        # Nom d'interface tronqué pour économiser l'espace
        display_name = iface_name[:12] if len(iface_name) > 12 else iface_name
        
        print(f"Titre: {type_icon} {display_name} {status_icon}")
        
        if iface_data['ipv4']:
            first_ipv4 = iface_data['ipv4'][0]
            print(f"IPv4: {first_ipv4}")
            
            # Indicateur s'il y a plusieurs IPs
            if len(iface_data['ipv4']) > 1:
                print(f"Plus d'IPs: +{len(iface_data['ipv4'])-1}")
        
        if not iface_data['ipv4'] and not iface_data['ipv6']:
            print("Aucune adresse IP")
        
        print()

if __name__ == "__main__":
    simulate_dashboard()