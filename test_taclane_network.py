#!/usr/bin/env python3
"""
Test de configuration réseau pour Taclane
Script de vérification rapide
"""

import subprocess
import socket
import sys

def check_network_for_taclane():
    """Vérifie si la configuration réseau permet d'accéder au Taclane"""
    print("=" * 60)
    print("🛡️  VÉRIFICATION RÉSEAU TACLANE")
    print("=" * 60)
    print()
    
    taclane_ip = "172.16.0.1"
    required_network = "172.16.0"
    
    # 1. Vérifier les interfaces réseau
    print("🔍 Vérification des interfaces réseau...")
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        
        # Rechercher interfaces dans le réseau Taclane
        taclane_interfaces = []
        current_interface = None
        
        for line in result.stdout.split('\n'):
            if line and not line.startswith('\t') and ':' in line:
                current_interface = line.split(':')[0]
            elif current_interface and f'inet {required_network}.' in line:
                ip_addr = line.split('inet ')[1].split()[0]
                taclane_interfaces.append((current_interface, ip_addr))
        
        if taclane_interfaces:
            print("✅ Interface(s) configurée(s) pour Taclane:")
            for interface, ip in taclane_interfaces:
                print(f"   • {interface}: {ip}")
                
                # Vérifier si c'est l'IP recommandée
                if ip == "172.16.0.2":
                    print("   ✅ IP recommandée (172.16.0.2) configurée!")
                elif ip.startswith("172.16.0."):
                    print(f"   ⚠️  IP dans le bon réseau mais différente de 172.16.0.2")
        else:
            print("❌ Aucune interface dans le réseau 172.16.0.0/24")
            show_config_instructions()
            return False
    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    # 2. Test de connectivité au Taclane
    print(f"\n🏓 Test de connectivité vers {taclane_ip}...")
    try:
        result = subprocess.run(['ping', '-c', '3', '-W', '2000', taclane_ip], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {taclane_ip} est accessible!")
            
            # Extraire les statistiques de ping
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'packets transmitted' in line:
                    print(f"   📊 {line.strip()}")
                elif 'round-trip' in line or 'rtt' in line:
                    print(f"   ⏱️  {line.strip()}")
        else:
            print(f"❌ {taclane_ip} n'est pas accessible")
            print("   💡 Vérifiez que:")
            print("      • L'équipement Taclane est allumé")
            print("      • Le câble réseau est connecté")
            print("      • Votre interface est bien configurée")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout lors du ping vers {taclane_ip}")
        return False
    except Exception as e:
        print(f"❌ Erreur ping: {e}")
        return False
    
    # 3. Test des ports Taclane
    print(f"\n🔌 Test des ports sur {taclane_ip}...")
    taclane_ports = {
        80: "HTTP",
        443: "HTTPS", 
        22: "SSH",
        23: "Telnet",
        161: "SNMP"
    }
    
    open_ports = []
    for port, service in taclane_ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((taclane_ip, port))
            
            if result == 0:
                print(f"   ✅ Port {port} ({service}): OUVERT")
                open_ports.append(port)
            else:
                print(f"   🔴 Port {port} ({service}): FERMÉ")
            
            sock.close()
            
        except Exception as e:
            print(f"   ❓ Port {port} ({service}): ERREUR - {e}")
    
    # 4. Recommandations d'accès
    print(f"\n🌐 Recommandations d'accès:")
    if 443 in open_ports:
        print(f"   ✅ Interface HTTPS: https://{taclane_ip}")
        print("   🔒 Recommandé pour la sécurité")
    
    if 80 in open_ports:
        print(f"   ⚠️  Interface HTTP: http://{taclane_ip}")
        if 443 not in open_ports:
            print("   💡 Utilisable mais HTTPS préférable")
    
    if 22 in open_ports:
        print(f"   🔐 SSH disponible: ssh admin@{taclane_ip}")
    
    if not (80 in open_ports or 443 in open_ports):
        print("   ❌ Aucune interface web détectée")
        print("   💡 L'équipement peut être en mode configuration restreinte")
    
    print(f"\n🎉 Configuration réseau validée pour l'accès au Taclane!")
    return True

def show_config_instructions():
    """Affiche les instructions de configuration"""
    print(f"\n🔧 INSTRUCTIONS DE CONFIGURATION:")
    print(f"═══════════════════════════════════════════════════════")
    
    print(f"\n🍎 macOS:")
    print(f"   sudo ifconfig en0 alias 172.16.0.2 netmask 255.255.255.0")
    
    print(f"\n🐧 Linux:")
    print(f"   sudo ip addr add 172.16.0.2/24 dev eth0")
    
    print(f"\n🪟 Windows (PowerShell Administrateur):")
    print(f'   netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0')
    
    print(f"\n💡 Après configuration, relancez ce script pour vérifier!")

def main():
    """Fonction principale"""
    try:
        success = check_network_for_taclane()
        
        if success:
            print(f"\n" + "=" * 60)
            print(f"✅ RÉSEAU PRÊT POUR TACLANE")
            print(f"=" * 60)
            sys.exit(0)
        else:
            print(f"\n" + "=" * 60)
            print(f"❌ CONFIGURATION RÉSEAU REQUISE")
            print(f"=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n👋 Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()