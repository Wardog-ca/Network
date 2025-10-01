#!/bin/bash

echo "🚀 Démarrage du serveur TFTP..."
echo "📁 Répertoire courant: $(pwd)"
echo "📋 Fichiers disponibles:"
ls -la

echo ""
echo "🔧 Démarrage du serveur sur le port 6969..."
python3 tftp_server.py --port 6969 --dir .

echo ""
echo "Pour tester le serveur depuis un autre terminal:"
echo "curl -o test_download.txt tftp://127.0.0.1:6969/README.md"
echo "ou"
echo "tftp 127.0.0.1 6969"
echo "get README.md downloaded_readme.txt"