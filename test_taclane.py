#!/usr/bin/env python3
"""
Test rapide du gestionnaire Taclane
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import tkinter as tk
from taclane_manager import create_taclane_interface

# Couleurs pour test
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#34495e', 
    'success': '#27ae60',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#3498db',
    'light': '#ecf0f1',
    'dark': '#2c3e50',
    'white': '#ffffff'
}

def log_func(message, level="INFO"):
    """Fonction de log pour test"""
    print(f"[{level}] {message}")

def test_taclane_manager():
    """Test du gestionnaire Taclane"""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    print("🛡️ Test du gestionnaire Taclane")
    print("📋 Configuration:")
    print("  • IP par défaut: 172.16.0.1")
    print("  • Outils de diagnostic intégrés")
    print("  • Monitoring en temps réel")
    print("  • Interface web automatique")
    
    # Créer l'interface Taclane
    taclane_win = create_taclane_interface(root, COLORS, log_func)
    
    print("✅ Interface Taclane créée avec succès!")
    print("🎯 Fonctionnalités disponibles:")
    print("  • 🏓 Ping continu")
    print("  • 📊 Traceroute") 
    print("  • 🔌 Scan de ports")
    print("  • 📈 Monitoring")
    print("  • 🌐 Interface web")
    print("  • 📋 Informations ARP")
    
    root.mainloop()

if __name__ == "__main__":
    test_taclane_manager()