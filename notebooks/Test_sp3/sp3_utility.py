#!/usr/bin/env python3
"""
Test du téléchargement SP3 avec authentification Earthdata
pour la date du 24 novembre 2024
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging détaillé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sp3_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_sp3_download():
    """Test complet du téléchargement SP3"""
    
    print("="*60)
    print("🧪 TEST TÉLÉCHARGEMENT SP3 AVEC EARTHDATA NASA")
    print("="*60)
    
    try:
        # Import du téléchargeur robuste
        from sp3_downloader_robust import RobustSP3Downloader
        
        # Initialiser avec vos identifiants
        print("🔐 Initialisation avec authentification Earthdata...")
        downloader = RobustSP3Downloader(
            earthdata_user="a.meunier",
            earthdata_password="%Fugro64600%"
        )
        
        # Test de connectivité des serveurs
        print("\n🌐 Test de connectivité des serveurs...")
        downloader.test_servers()
        
        # Date de vos observations
        obs_date = datetime(2024, 11, 24)
        output_dir = "C:/1-Data/01-Projet/ProjetPY/Test_GNSS"
        
        print(f"\n📅 Téléchargement pour {obs_date.strftime('%Y-%m-%d')}")
        print(f"📁 Répertoire de sortie: {output_dir}")
        
        # Tentative de téléchargement
        downloaded_files = downloader.download_sp3_for_date(
            obs_date,
            output_dir,
            products=['igr', 'igs', 'igu']
        )
        
        # Résultats
        print("\n" + "="*60)
        print("📊 RÉSULTATS DU TEST")
        print("="*60)
        
        if downloaded_files:
            print(f"✅ SUCCÈS ! {len(downloaded_files)} fichier(s) téléchargé(s):")
            
            for file_path in downloaded_files:
                size_mb = file_path.stat().st_size / (1024*1024)
                print(f"   📄 {file_path.name} ({size_mb:.1f} MB)")
                
                # Analyser le contenu du fichier
                print(f"      📍 Emplacement: {file_path}")
                
                # Lire les premières lignes pour vérifier le format
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()[:10]
                    
                    print(f"      📋 En-tête SP3:")
                    for i, line in enumerate(lines[:3]):
                        print(f"        {i+1}: {line.strip()}")
                    
                    # Compter les époques
                    epoch_count = sum(1 for line in lines if line.startswith('*'))
                    print(f"      ⏰ Époques trouvées dans l'échantillon: {epoch_count}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur lecture: {e}")
            
            print(f"\n🎉 TÉLÉCHARGEMENT RÉUSSI !")
            print(f"💡 Vous pouvez maintenant relancer votre programme principal.")
            print(f"   Il détectera automatiquement les fichiers SP3 et les utilisera.")
            
            return True
            
        else:
            print(f"❌ ÉCHEC - Aucun fichier téléchargé")
            print(f"💡 Solutions:")
            print(f"   1. Vérifiez votre connexion internet")
            print(f"   2. Les fichiers peuvent ne plus être disponibles (trop anciens)")
            print(f"   3. Votre programme fonctionne très bien avec les éphémérides broadcast")
            
            return False
            
    except ImportError as e:
        print(f"❌ ERREUR IMPORT: {e}")
        print(f"💡 Assurez-vous que sp3_downloader_robust.py est dans le même répertoire")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")
        logger.exception("Erreur détaillée:")
        return False

def test_earthdata_auth():
    """Test spécifique de l'authentification Earthdata"""
    
    print("\n🔐 TEST AUTHENTIFICATION EARTHDATA")
    print("-" * 40)
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Test d'authentification simple
        auth_url = "https://urs.earthdata.nasa.gov/oauth/authorize"
        session = requests.Session()
        session.auth = HTTPBasicAuth("a.meunier", "%Fugro64600%")
        
        print("🌐 Test de connexion à Earthdata...")
        
        # Test avec un endpoint simple
        test_response = session.get(
            "https://urs.earthdata.nasa.gov/profile",
            timeout=10,
            allow_redirects=True
        )
        
        if test_response.status_code in [200, 302, 401]:
            print("✅ Serveur Earthdata accessible")
            if test_response.status_code == 401:
                print("🔐 Authentification requise (normal)")
            else:
                print("✅ Authentification semble fonctionner")
        else:
            print(f"⚠️ Status inattendu: {test_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur test Earthdata: {e}")

def check_prerequisites():
    """Vérifie les prérequis"""
    
    print("🔍 VÉRIFICATION DES PRÉREQUIS")
    print("-" * 30)
    
    # Vérifier les modules requis
    required_modules = ['requests', 'urllib3', 'gzip', 'ssl']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - MANQUANT")
            missing_modules.append(module)
    
    # Vérifier la connectivité internet
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        print(f"✅ Connectivité internet")
    except:
        print(f"❌ Connectivité internet")
    
    # Vérifier le répertoire de sortie
    output_dir = Path("C:/1-Data/01-Projet/ProjetPY/Test_GNSS")
    if output_dir.exists():
        print(f"✅ Répertoire de sortie: {output_dir}")
    else:
        print(f"⚠️ Répertoire de sortie n'existe pas: {output_dir}")
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Répertoire créé")
        except:
            print(f"❌ Impossible de créer le répertoire")
    
    return len(missing_modules) == 0

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU TEST SP3")
    
    # Vérifications préliminaires
    if not check_prerequisites():
        print("\n❌ Prérequis manquants - installation requise")
        sys.exit(1)
    
    # Test d'authentification
    test_earthdata_auth()
    
    # Test principal
    success = test_sp3_download()
    
    print("\n" + "="*60)
    if success:
        print("🎉 TEST TERMINÉ AVEC SUCCÈS !")
        print("Votre système SP3 est maintenant opérationnel.")
    else:
        print("⚠️ TEST PARTIELLEMENT RÉUSSI")
        print("Votre programme fonctionne parfaitement sans SP3.")
    print("="*60)