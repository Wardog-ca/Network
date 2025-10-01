# 🛡️ Guide d'utilisation - Gestionnaire Taclane

## Vue d'ensemble

Le **Gestionnaire Taclane** est un outil spécialisé pour la gestion et le diagnostic des équipements de chiffrement Taclane. Il fournit une interface graphique complète pour surveiller, tester et diagnostiquer les dispositifs Taclane sur le réseau.

## 🎯 Fonctionnalités principales

### 🔧 Configuration
- **Adresse IP par défaut**: 172.16.0.1 (modifiable)
- **Test de connectivité** automatique
- **Détection des ports** de service
- **Statut en temps réel**

### 🔍 Outils de diagnostic

#### 🏓 Ping Continu
- Surveillance de la connectivité réseau
- Affichage en temps réel des réponses
- Détection des pertes de paquets
- Interface en style terminal

#### 📊 Traceroute
- Traçage du chemin réseau vers l'équipement
- Identification des sauts intermédiaires
- Détection des goulots d'étranglement
- Analyse de latence

#### 🔌 Scan de Ports
- Test des ports de service standard:
  - **Port 21**: FTP
  - **Port 22**: SSH
  - **Port 23**: Telnet
  - **Port 80**: HTTP
  - **Port 443**: HTTPS
  - **Port 161**: SNMP
- Détection automatique des services actifs

#### 📈 Monitoring
- Surveillance continue de la disponibilité
- Calcul du pourcentage de disponibilité
- Historique des tests
- Alertes en cas de problème

#### 🌐 Interface Web
- **Vérification automatique** de la configuration réseau
- **Configuration assistée** si votre PC n'a pas la bonne IP
- **Ouverture automatique** de l'interface web (HTTPS/HTTP)
- **Test de connectivité** avant ouverture du navigateur
- **Instructions détaillées** pour chaque système d'exploitation

#### 📋 Informations ARP
- Consultation de la table ARP
- Vérification de la résolution MAC
- Diagnostic des problèmes de couche 2

### 📊 Interface à onglets

#### 📊 Onglet Statut
- Informations générales sur l'équipement
- Statut des ports de service
- Configuration réseau recommandée

#### 📝 Onglet Logs
- Historique des événements
- Messages de diagnostic
- Résultats des tests

#### ⚙️ Onglet Configuration
- Informations de monitoring en temps réel
- Statistiques de disponibilité
- Paramètres réseau suggérés

## 🚀 Utilisation

### Démarrage rapide

1. **Depuis l'application principale**:
   - Cliquez sur le bouton "🛡️ Taclane Manager" dans les outils professionnels

2. **Test standalone**:
   ```bash
   python3 test_taclane.py
   ```

### Configuration initiale

1. **Configuration réseau OBLIGATOIRE**:
   - Cliquez sur "🌐 Config Réseau" pour vérifier votre configuration
   - **Votre PC doit avoir l'IP 172.16.0.2** pour communiquer avec le Taclane
   - Le Taclane utilise par défaut l'IP `172.16.0.1`

2. **Configuration automatique**:
   - L'outil détecte automatiquement si votre réseau est configuré
   - Si non configuré, il propose des instructions détaillées
   - Commandes prêtes à copier pour macOS, Linux et Windows

3. **Test de connectivité**:
   - Cliquez sur "🔍 Tester" pour vérifier la connexion
   - Le statut s'affiche en temps réel avec codes couleur

### Diagnostic avancé

1. **Test de ping continu**:
   - Surveille la connectivité en permanence
   - Détecte les interruptions réseau

2. **Analyse réseau**:
   - Utilisez le traceroute pour identifier les problèmes de routage
   - Scannez les ports pour vérifier les services

3. **Monitoring long terme**:
   - Activez le monitoring pour des statistiques continues
   - Consultez les logs pour l'historique

## 🔧 Configuration typique Taclane

### Réseau
- **Segment réseau**: 172.16.0.0/24
- **Masque de sous-réseau**: 255.255.255.0
- **Passerelle probable**: 172.16.0.254
- **🎯 CRITIQUE**: Votre PC doit avoir l'IP **172.16.0.2** pour communiquer

### 🌐 Configuration réseau requise

#### Configuration rapide par système:

**🍎 macOS:**
```bash
sudo ifconfig en0 alias 172.16.0.2 netmask 255.255.255.0
```

**🐧 Linux:**
```bash
sudo ip addr add 172.16.0.2/24 dev eth0
```

**🪟 Windows (PowerShell Administrateur):**
```cmd
netsh interface ip add address "Ethernet" 172.16.0.2 255.255.255.0
```

#### Vérification après configuration:
```bash
# Test de connectivité
ping 172.16.0.1

# Vérification de votre IP
ifconfig  # macOS/Linux
ipconfig  # Windows
```

### Ports de service
- **80/443**: Interface web d'administration
- **22**: SSH pour configuration avancée
- **23**: Telnet (si activé)
- **161**: SNMP pour monitoring

### Sécurité
- **Chiffrement**: AES-256 (typique)
- **Authentification**: Certificats/PSK
- **Management**: HTTPS recommandé

## ⚠️ Notes de sécurité

- Les équipements Taclane sont des dispositifs de chiffrement sensibles
- Assurez-vous d'avoir les autorisations appropriées avant utilisation
- Respectez les procédures de sécurité de votre organisation
- Évitez les accès non autorisés aux interfaces d'administration

## 🛠️ Dépannage

### Problèmes courants

#### "🔴 Hors ligne"
- Vérifiez la connectivité réseau
- Confirmez l'adresse IP de l'équipement
- Testez avec un ping manuel

#### Aucun port ouvert détecté
- L'équipement peut être en mode restrictif
- Vérifiez les règles de pare-feu
- Consultez la documentation de l'équipement

#### Interface web inaccessible
- Essayez HTTP et HTTPS
- Vérifiez les certificats SSL/TLS
- Utilisez l'adresse IP directement

### Commandes de diagnostic manuelles

```bash
# Test ping manuel
ping 172.16.0.1

# Test telnet sur port spécifique
telnet 172.16.0.1 80

# Scan nmap
nmap -p 1-1000 172.16.0.1

# Table ARP
arp -a | grep 172.16.0.1
```

## 📞 Support

Pour des problèmes spécifiques aux équipements Taclane, consultez:
- La documentation officielle de l'équipement
- L'équipe de support réseau de votre organisation
- Les logs de l'outil pour diagnostic détaillé

---

**Version**: 1.0  
**Dernière mise à jour**: Octobre 2025  
**Compatibilité**: Windows, macOS, Linux