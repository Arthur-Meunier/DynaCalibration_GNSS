#!/usr/bin/env python3
"""
SP3 Downloader - Version avec Configuration
Téléchargeur intelligent de produits SP3 combinés GPS/GLONASS
Avec menu de paramètres pour personnaliser token et répertoire
"""

import os
import sys
import json
import requests
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path

def setup_logging():
    """Configure le logging"""
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).parent
        log_file = app_dir / "sp3_downloader.log"
    else:
        log_file = Path(__file__).parent / "sp3_downloader.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ConfigManager:
    """Gestionnaire de configuration"""
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Mode exécutable
            self.config_dir = Path(sys.executable).parent
        else:
            # Mode développement
            self.config_dir = Path(__file__).parent
        
        self.config_file = self.config_dir / "sp3_config.json"
        self.default_config = {
            "jwt_token": (
                "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ."
                "eyJ0eXBlIjoiVXNlciIsInVpZCI6ImEubWV1bmllciIsImV4cCI6MTc1NzYzNjk3NSwiaWF0IjoxNzUyNDUyOTc1LCJpc3MiOiJodHRwczovL3Vycy5lYXJ0aGRhdGEubmFzYS5nb3YiLCJpZGVudGl0eV9wcm92aWRlciI6ImVkbF9vcHMiLCJhY3IiOiJlZGwiLCJhc3N1cmFuY2VfbGV2ZWwiOjN9."
                "nAL8KSU_RDW9ldNEhT-EAbdEZagLNLTeOD_VYq9Bas-UcRSaempBuZ3RiFyX18q7I0fV2bUiLTKV-ME-Ra_yyU_ODT76GNvx48v9QWMB_rzY3W9gXgeyoG05bqgauZJGpLiHyxkMozHLClG_JT23Pcsjmk1dXliW6bW58-vYZnUmKe2mXxDGdbUUfIM6D3mjHbijXQ_MSYZtyxeb9fxcPIfqFTUMmlQ90QqcxSahp2rDLDZBRdxauj0c9xPrsq_SlDoGGJcWx0qDuBz0Z2VkFP3cBJsoFIEhRQrccIn5v9Ykqdr9s224bEWkQGT8dDrO_Rv2rhr6RcFZLYVfwMQURQ"
            ),
            "output_directory": str(self.config_dir / "SP3_Data"),
            "user_name": "Utilisateur",
            "auto_cleanup": True
        }
        
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Vérifier que toutes les clés par défaut existent
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde config: {e}")
            return False
    
    def get(self, key):
        """Récupère une valeur de configuration"""
        return self.config.get(key, self.default_config.get(key))
    
    def set(self, key, value):
        """Définit une valeur de configuration"""
        self.config[key] = value

class SP3DownloaderWithConfig:
    """Téléchargeur SP3 avec configuration personnalisable"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.output_dir = Path(self.config.get('output_directory'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session avec authentification
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.get("jwt_token")}',
            'User-Agent': 'SP3-Downloader-Config/1.0'
        })
        
        # URLs de base
        self.mgex_base = "https://cddis.nasa.gov/archive/gnss/products/mgex"
        self.cddis_base = "https://cddis.nasa.gov/archive/gnss/products"
        
        # Seuils de disponibilité
        self.availability_thresholds = {
            'final': 12 * 24,
            'rapid': 24,
            'ultra_rapid': 3
        }
    
    def update_config(self, config_manager):
        """Met à jour la configuration"""
        self.config = config_manager
        self.output_dir = Path(self.config.get('output_directory'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mettre à jour l'authentification
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.get("jwt_token")}'
        })
    
    def gps_epoch(self):
        """Époque GPS"""
        return datetime(1980, 1, 6, 0, 0, 0)
    
    def date_to_gps_week(self, date_str):
        """Convertit une date en semaine GPS"""
        date = datetime.strptime(date_str, "%d/%m/%Y")
        delta = date - self.gps_epoch()
        gps_week = delta.days // 7
        day_of_week = delta.days % 7
        return gps_week, day_of_week, date
    
    def analyze_availability(self, target_date):
        """Analyse la disponibilité"""
        date_obj = datetime.strptime(target_date, "%d/%m/%Y")
        hours_elapsed = (datetime.now() - date_obj).total_seconds() / 3600
        
        if hours_elapsed >= self.availability_thresholds['final']:
            return 'final'
        elif hours_elapsed >= self.availability_thresholds['rapid']:
            return 'rapid'
        elif hours_elapsed >= self.availability_thresholds['ultra_rapid']:
            return 'ultra_rapid'
        else:
            return None
    
    def generate_filenames(self, target_date, product_type):
        """Génère les noms de fichiers"""
        gps_week, day_of_week, date_obj = self.date_to_gps_week(target_date)
        year = date_obj.year
        doy = date_obj.timetuple().tm_yday
        
        filenames = []
        use_new_format = gps_week >= 2238
        
        if use_new_format:
            if product_type == 'final':
                filenames.extend([
                    f"COD0MGXFIN_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz",
                    f"GFZ0MGXFIN_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz",
                    f"WUM0MGXFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz",
                    f"IGS0OPSFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz"
                ])
            elif product_type == 'rapid':
                filenames.extend([
                    f"COD0MGXRAP_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz",
                    f"GFZ0MGXRAP_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz",
                    f"IGS0OPSRAP_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz"
                ])
            elif product_type == 'ultra_rapid':
                for hour in ['00', '06', '12', '18']:
                    filenames.extend([
                        f"COD0MGXULT_{year}{doy:03d}{hour}00_01D_05M_ORB.SP3.gz",
                        f"IGS0OPSULT_{year}{doy:03d}{hour}00_01D_15M_ORB.SP3.gz"
                    ])
        else:
            if product_type == 'final':
                filenames.extend([
                    f"cod{gps_week:04d}{day_of_week}.sp3.Z",
                    f"igs{gps_week:04d}{day_of_week}.sp3.Z"
                ])
            elif product_type == 'rapid':
                filenames.extend([
                    f"codr{gps_week:04d}{day_of_week}.sp3.Z",
                    f"igr{gps_week:04d}{day_of_week}.sp3.Z"
                ])
        
        return filenames, gps_week
    
    def download_product(self, target_date, product_type):
        """Télécharge un produit"""
        try:
            filenames, gps_week = self.generate_filenames(target_date, product_type)
            
            repositories = [
                f"{self.mgex_base}/{gps_week:04d}/",
                f"{self.cddis_base}/{gps_week:04d}/"
            ]
            
            for repo_url in repositories:
                for filename in filenames:
                    file_url = repo_url + filename
                    try:
                        response = self.session.head(file_url, timeout=10)
                        if response.status_code == 200:
                            print(f"   Trouvé: {filename}")
                            return self.download_file(file_url, filename)
                    except:
                        continue
            return None
        except Exception as e:
            logger.error(f"Erreur téléchargement: {e}")
            return None
    
    def download_file(self, file_url, filename):
        """Télécharge un fichier"""
        try:
            response = self.session.get(file_url, stream=True, timeout=120)
            response.raise_for_status()
            
            output_path = self.output_dir / filename
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if filename.endswith('.gz'):
                return self.decompress_gzip(output_path)
            elif filename.endswith('.Z'):
                return self.decompress_unix_z(output_path)
            
            return str(output_path)
        except Exception as e:
            logger.error(f"Erreur téléchargement fichier: {e}")
            return None
    
    def decompress_gzip(self, compressed_path):
        """Décompresse .gz"""
        try:
            decompressed_path = compressed_path.with_suffix('')
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            if self.config.get('auto_cleanup', True):
                compressed_path.unlink()
            return str(decompressed_path)
        except Exception as e:
            logger.error(f"Erreur décompression: {e}")
            return str(compressed_path)
    
    def decompress_unix_z(self, compressed_path):
        """Décompresse .Z"""
        try:
            import subprocess
            decompressed_path = compressed_path.with_suffix('')
            result = subprocess.run(['uncompress', str(compressed_path)], 
                                  capture_output=True, timeout=60)
            if result.returncode == 0 and decompressed_path.exists():
                return str(decompressed_path)
            return str(compressed_path)
        except:
            return str(compressed_path)
    
    def analyze_sp3(self, file_path):
        """Analyse détaillée d'un fichier SP3"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            satellites = {}
            constellations = set()
            all_satellites = set()
            
            # Analyser plus de lignes pour avoir une analyse complète
            for line in lines[:200]:
                if line.startswith('+'):
                    # Ligne de satellites - parser correctement
                    # Format: "+ 32   G01G02G03G04G05G06G07G08G09G10G11G12G13G14G15G16G17"
                    sat_section = line[9:].strip()  # Après le nombre de satellites
                    
                    # Parser les satellites par groupes de 3 caractères
                    pos = 0
                    while pos < len(sat_section):
                        if pos + 2 < len(sat_section):
                            sat_id = sat_section[pos:pos+3]
                            
                            # Vérifier que c'est un identifiant satellite valide
                            if len(sat_id) == 3 and sat_id[0].isalpha() and sat_id[1:].isdigit():
                                constellation = sat_id[0].upper()
                                constellations.add(constellation)
                                all_satellites.add(sat_id)
                                
                                if constellation not in satellites:
                                    satellites[constellation] = set()
                                satellites[constellation].add(sat_id)
                        pos += 3
            
            return satellites, constellations
            
        except Exception as e:
            logger.error(f"Erreur analyse SP3: {e}")
            return {}, set()

def show_settings_menu(config_manager):
    """Affiche le menu des paramètres"""
    while True:
        print("\n" + "=" * 50)
        print("⚙️  MENU PARAMÈTRES")
        print("=" * 50)
        print(f"👤 Utilisateur: {config_manager.get('user_name')}")
        print(f"📁 Répertoire: {config_manager.get('output_directory')}")
        print(f"🔑 Token: {'●' * 20}...{config_manager.get('jwt_token')[-20:]}")
        print(f"🧹 Nettoyage auto: {'✅' if config_manager.get('auto_cleanup') else '❌'}")
        
        print(f"\n📋 OPTIONS:")
        print(f"1. Changer nom utilisateur")
        print(f"2. Changer répertoire de sortie")
        print(f"3. Changer token JWT")
        print(f"4. Activer/Désactiver nettoyage auto")
        print(f"5. Réinitialiser paramètres")
        print(f"6. Retour au menu principal")
        
        choice = input("\nChoix (1-6): ").strip()
        
        if choice == '1':
            name = input("Nouveau nom d'utilisateur: ").strip()
            if name:
                config_manager.set('user_name', name)
                config_manager.save_config()
                print(f"✅ Nom mis à jour: {name}")
        
        elif choice == '2':
            print(f"Répertoire actuel: {config_manager.get('output_directory')}")
            new_dir = input("Nouveau répertoire (ou Entrée pour annuler): ").strip()
            if new_dir:
                try:
                    test_path = Path(new_dir)
                    test_path.mkdir(parents=True, exist_ok=True)
                    # Test d'écriture
                    test_file = test_path / "test.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    
                    config_manager.set('output_directory', str(test_path))
                    config_manager.save_config()
                    print(f"✅ Répertoire mis à jour: {test_path}")
                except Exception as e:
                    print(f"❌ Erreur: {e}")
        
        elif choice == '3':
            print(f"Token actuel: {config_manager.get('jwt_token')[:50]}...")
            print(f"⚠️  Attention: Le token JWT doit être valide pour NASA Earthdata")
            new_token = input("Nouveau token JWT (ou Entrée pour annuler): ").strip()
            if new_token:
                if len(new_token) > 100:  # Vérification basique
                    config_manager.set('jwt_token', new_token)
                    config_manager.save_config()
                    print(f"✅ Token mis à jour")
                else:
                    print(f"❌ Token trop court (doit faire >100 caractères)")
        
        elif choice == '4':
            current = config_manager.get('auto_cleanup')
            config_manager.set('auto_cleanup', not current)
            config_manager.save_config()
            status = "activé" if not current else "désactivé"
            print(f"✅ Nettoyage auto {status}")
        
        elif choice == '5':
            confirm = input("Réinitialiser tous les paramètres? (oui/non): ").strip().lower()
            if confirm in ['oui', 'o', 'yes', 'y']:
                config_manager.config = config_manager.default_config.copy()
                config_manager.save_config()
                print(f"✅ Paramètres réinitialisés")
        
        elif choice == '6':
            break
        
        else:
            print(f"❌ Choix invalide")

def main():
    """Application principale"""
    # Initialiser la configuration
    config_manager = ConfigManager()
    downloader = SP3DownloaderWithConfig(config_manager)
    
    while True:
        try:
            print("\n" + "=" * 50)
            print(f"🛰️  SP3 DOWNLOADER v2.0")
            print("=" * 50)
            print(f"👤 {config_manager.get('user_name')}")
            print(f"📁 {config_manager.get('output_directory')}")
            
            print(f"\n📋 MENU PRINCIPAL:")
            print(f"1. Télécharger fichier SP3")
            print(f"2. ⚙️  Paramètres")
            print(f"3. ❌ Quitter")
            
            choice = input("\nChoix (1-3): ").strip()
            
            if choice == '1':
                # Téléchargement SP3
                print("\n" + "-" * 30)
                target_date = input("Date (DD/MM/YYYY): ").strip()
                
                if not target_date:
                    continue
                
                try:
                    date_obj = datetime.strptime(target_date, "%d/%m/%Y")
                    if date_obj > datetime.now():
                        print("❌ Date future invalide")
                        continue
                except ValueError:
                    print("❌ Format invalide")
                    continue
                
                # Analyser disponibilité
                optimal_product = downloader.analyze_availability(target_date)
                
                if optimal_product is None:
                    print("❌ Aucun produit disponible (minimum 3h requis)")
                    input("Appuyez sur Entrée pour continuer...")
                    continue
                
                print(f"🔍 Recherche {optimal_product.upper()}...")
                
                # Télécharger
                downloaded_file = downloader.download_product(target_date, optimal_product)
                
                if downloaded_file:
                    print(f"✅ Succès: {Path(downloaded_file).name}")
                    print(f"📂 Emplacement: {downloaded_file}")
                    
                    # Vérifier que le fichier existe
                    if not Path(downloaded_file).exists():
                        print("❌ Erreur: Fichier non trouvé après téléchargement")
                        input("Appuyez sur Entrée pour continuer...")
                        continue
                    
                    # Analyse détaillée
                    print(f"\n🔍 Analyse du fichier...")
                    satellites, constellations = downloader.analyze_sp3(downloaded_file)
                    
                    if not satellites and not constellations:
                        print("❌ Erreur lors de l'analyse du fichier")
                        input("Appuyez sur Entrée pour continuer...")
                        continue
                    
                    # Calcul des totaux
                    total_sats = sum(len(sats) for sats in satellites.values())
                    
                    # Affichage des résultats
                    file_size = Path(downloaded_file).stat().st_size / (1024*1024)
                    
                    print(f"\n📊 ANALYSE FICHIER SP3:")
                    print(f"📁 {Path(downloaded_file).name}")
                    print(f"💾 Taille: {file_size:.2f} MB")
                    print(f"🛰️ Satellites totaux: {total_sats}")
                    print(f"🌐 Constellations: {len(constellations)}")
                    
                    # Détail par constellation
                    constellation_names = {
                        'G': 'GPS', 'R': 'GLONASS', 'E': 'Galileo', 
                        'C': 'BeiDou', 'J': 'QZSS', 'S': 'SBAS'
                    }
                    
                    if constellations:
                        print(f"\n🌍 CONSTELLATIONS DÉTECTÉES:")
                        for const in sorted(constellations):
                            name = constellation_names.get(const, f'Constellation {const}')
                            count = len(satellites.get(const, []))
                            print(f"   {name}: {count} satellites")
                    
                    # Évaluation du type de fichier
                    if len(constellations) >= 3:
                        print(f"\n🌍 FICHIER MULTI-GNSS COMPLET")
                        print(f"   Excellent pour applications de précision")
                    elif len(constellations) == 2 and 'R' in constellations:
                        print(f"\n🛰️ FICHIER GPS+GLONASS")
                        print(f"   Bon pour applications standards")
                    elif len(constellations) == 1:
                        print(f"\n⚠️ FICHIER MONO-CONSTELLATION")
                        print(f"   Limité à GPS uniquement")
                    
                    print(f"\n✅ Fichier prêt à utiliser!")
                else:
                    print("❌ Téléchargement échoué")
                
                input("Appuyez sur Entrée pour continuer...")
            
            elif choice == '2':
                # Menu paramètres
                show_settings_menu(config_manager)
                # Mettre à jour le downloader avec la nouvelle config
                downloader.update_config(config_manager)
            
            elif choice == '3':
                print("👋 Au revoir!")
                break
            
            else:
                print("❌ Choix invalide")
        
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            logger.error(f"Erreur main: {e}")
            input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()