#!/usr/bin/env python3
"""
Configuration rapide pour équipements Taclane
Script d'aide pour administrateurs réseau
"""

import subprocess
import socket
import time
import sys

def print_banner():
    """Affiche la bannière"""
    print("=" * 60)
    print("🛡️  CONFIGURATION RAPIDE TACLANE")
    print("=" * 60)
    print("📋  Outil d'aide pour administrateurs réseau")
    print("🌐  Réseau par défaut: 172.16.0.0/24")
    print("=" * 60)
    print()

def test_taclane_connectivity(ip="172.16.0.1"):
    """Test la connectivité vers un Taclane"""
    print(f"🔍 Test de connectivité vers {ip}...")
    
    try:
        # Test ping
        result = subprocess.run(['ping', '-c', '3', '-W', '2000', ip], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {ip} est accessible")
            return True
        else:
            print(f"❌ {ip} n'est pas accessible")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def scan_taclane_ports(ip="172.16.0.1"):
    """Scan les ports courants d'un Taclane"""
    print(f"🔌 Scan des ports sur {ip}...")
    
    common_ports = {
        22: "SSH",
        23: "Telnet", 
        80: "HTTP",
        443: "HTTPS",
        161: "SNMP",
        162: "SNMP Trap"
    }
    
    open_ports = []
    
    for port, service in common_ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                print(f"  🟢 Port {port} ({service}): OUVERT")
                open_ports.append(port)
            else:
                print(f"  🔴 Port {port} ({service}): FERMÉ")
            
            sock.close()
            
        except Exception as e:
            print(f"  ❓ Port {port} ({service}): ERREUR - {e}")
    
    return open_ports

def discover_taclane_network():
    """Découvre les équipements Taclane sur le réseau"""
    print("🔍 Découverte des équipements Taclane...")
    print("📡 Scan du réseau 172.16.0.0/24...")
    
    active_ips = []
    
    # Scanner les 50 premières adresses pour économiser du temps
    for i in range(1, 51):
        ip = f"172.16.0.{i}"
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                  capture_output=True, timeout=3)
            
            if result.returncode == 0:
                print(f"  🟢 {ip} - Actif")
                active_ips.append(ip)
            else:
                print(f"  🔴 {ip} - Inactif", end='\r')  # Overwrite line
                
        except:
            continue
    
    print("\n" + "=" * 40)
    print(f"📊 Résumé: {len(active_ips)} équipements actifs trouvés")
    for ip in active_ips:
        print(f"  • {ip}")
    
    return active_ips

def generate_config_report(ip, open_ports):
    """Génère un rapport de configuration"""
    print(f"\n📋 RAPPORT DE CONFIGURATION - {ip}")
    print("=" * 50)
    
    print("🌐 Configuration réseau:")
    print(f"  • Adresse IP: {ip}")
    print("  • Réseau: 172.16.0.0/24")
    print("  • Masque: 255.255.255.0")
    print("  • Passerelle probable: 172.16.0.254")
    
    print("\n🔌 Services détectés:")
    if open_ports:
        service_names = {22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 161: "SNMP"}
        for port in open_ports:
            service = service_names.get(port, "Inconnu")
            print(f"  • Port {port}: {service}")
    else:
        print("  • Aucun service détecté")
    
    print("\n🔧 Recommandations:")
    if 443 in open_ports:
        print("  ✅ Interface HTTPS disponible - Recommandé")
        print(f"     → Accès: https://{ip}")
    elif 80 in open_ports:
        print("  ⚠️  Interface HTTP détectée - HTTPS recommandé")
        print(f"     → Accès: http://{ip}")
    
    if 22 in open_ports:
        print("  🔐 SSH disponible pour administration")
        print(f"     → Commande: ssh admin@{ip}")
    
    if 161 in open_ports:
        print("  📊 SNMP disponible pour monitoring")
        print(f"     → Test: snmpget -v2c -c public {ip} 1.3.6.1.2.1.1.1.0")
    
    print("\n⚠️  Notes de sécurité:")
    print("  • Vérifiez les certificats SSL/TLS")
    print("  • Utilisez des mots de passe forts")
    print("  • Activez l'authentification multi-facteurs si disponible")
    print("  • Consultez les logs régulièrement")

def main():
    """Fonction principale"""
    print_banner()
    
    # Menu interactif
    while True:
        print("🔧 Options disponibles:")
        print("  1. 🔍 Tester un Taclane spécifique")
        print("  2. 📡 Découvrir les Taclanes sur le réseau")
        print("  3. 🔌 Scanner les ports d'un Taclane")
        print("  4. 📋 Rapport complet")
        print("  5. 🚪 Quitter")
        
        try:
            choice = input("\n👉 Choisissez une option (1-5): ").strip()
            
            if choice == "1":
                ip = input("🌐 Adresse IP du Taclane (défaut: 172.16.0.1): ").strip()
                if not ip:
                    ip = "172.16.0.1"
                test_taclane_connectivity(ip)
                
            elif choice == "2":
                discover_taclane_network()
                
            elif choice == "3":
                ip = input("🌐 Adresse IP du Taclane (défaut: 172.16.0.1): ").strip()
                if not ip:
                    ip = "172.16.0.1"
                scan_taclane_ports(ip)
                
            elif choice == "4":
                ip = input("🌐 Adresse IP du Taclane (défaut: 172.16.0.1): ").strip()
                if not ip:
                    ip = "172.16.0.1"
                
                if test_taclane_connectivity(ip):
                    open_ports = scan_taclane_ports(ip)
                    generate_config_report(ip, open_ports)
                else:
                    print("❌ Impossible de générer le rapport - équipement non accessible")
                    
            elif choice == "5":
                print("👋 Au revoir!")
                break
                
            else:
                print("❌ Option invalide")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
        
        print("\n" + "-" * 40)

if __name__ == "__main__":
    main()