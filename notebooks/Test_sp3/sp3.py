#!/usr/bin/env python3
"""
Téléchargeur SP3 intelligent avec produits combinés GPS/GLONASS
Logique de sélection automatique optimisée basée sur la disponibilité temporelle IGS
- IGS Final: disponible après 12 jours (précision 2-3 cm) - PRIORITÉ 1
- IGR Rapid: disponible après 1 jour (précision 2,5 cm) - PRIORITÉ 2
- IGU Ultra-rapid: disponible après 3 heures (précision 3-5 cm) - PRIORITÉ 3
"""

import os
import requests
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SP3CombinedDownloader:
    """Téléchargeur SP3 intelligent pour produits combinés GPS/GLONASS avec logique optimisée"""
    
    def __init__(self, jwt_token, output_dir="./sp3_data"):
        self.jwt_token = jwt_token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session avec authentification
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'SP3-Combined-Downloader/2.1'
        })
        
        # URLs de base CDDIS
        self.cddis_base = "https://cddis.nasa.gov/archive/gnss/products"
        self.mgex_base = "https://cddis.nasa.gov/archive/gnss/products/mgex"  # Produits multi-GNSS
        self.broadcast_base = "https://cddis.nasa.gov/archive/gnss/data/daily"
        
        # Seuils de disponibilité des produits IGS (en heures)
        self.availability_thresholds = {
            'final': 12 * 24,      # 12 jours minimum
            'rapid': 24,           # 1 jour minimum  
            'ultra_rapid': 3       # 3 heures minimum
        }
        
        # Précisions et caractéristiques des produits
        self.product_specs = {
            'final': {
                'precision': '2-3 cm',
                'description': 'Référence de précision maximale',
                'availability': '12 jours après',
                'priority': 1
            },
            'rapid': {
                'precision': '2,5 cm',
                'description': 'Solution quotidienne rapide',
                'availability': '1 jour après',
                'priority': 2
            },
            'ultra_rapid': {
                'precision': '3-5 cm',
                'description': 'Solution temps quasi-réel',
                'availability': '3 heures après',
                'priority': 3
            }
        }
        
    def gps_epoch(self):
        """Époque GPS : 6 janvier 1980 00:00:00 UTC"""
        return datetime(1980, 1, 6, 0, 0, 0)
    
    def date_to_gps_week(self, date_str):
        """Convertit une date en semaine GPS et jour de la semaine"""
        if isinstance(date_str, str):
            if '/' in date_str:
                date = datetime.strptime(date_str, "%d/%m/%Y")
            else:
                date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = date_str
        
        gps_start = self.gps_epoch()
        delta = date - gps_start
        gps_week = delta.days // 7
        day_of_week = delta.days % 7
        
        return gps_week, day_of_week, date
    
    def analyze_data_availability(self, target_date):
        """Analyse la disponibilité des produits"""
        if isinstance(target_date, str):
            if '/' in target_date:
                date_obj = datetime.strptime(target_date, "%d/%m/%Y")
            else:
                date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            date_obj = target_date
        
        now = datetime.now()
        time_diff = now - date_obj
        hours_elapsed = time_diff.total_seconds() / 3600
        
        analysis = {
            'date_requested': date_obj,
            'hours_elapsed': hours_elapsed,
            'optimal_product': None,
            'data_unavailable': False
        }
        
        if hours_elapsed >= self.availability_thresholds['final']:
            analysis['optimal_product'] = 'final'
        elif hours_elapsed >= self.availability_thresholds['rapid']:
            analysis['optimal_product'] = 'rapid'
        elif hours_elapsed >= self.availability_thresholds['ultra_rapid']:
            analysis['optimal_product'] = 'ultra_rapid'
        else:
            analysis['data_unavailable'] = True
        
        return analysis
    
    def generate_combined_sp3_filenames(self, target_date, product_type):
        """
        Génère les noms de fichiers SP3 RÉELLEMENT combinés GPS/GLONASS
        Cherche d'abord les produits multi-GNSS puis les produits IGS standard
        """
        gps_week, day_of_week, date_obj = self.date_to_gps_week(target_date)
        year = date_obj.year
        doy = date_obj.timetuple().tm_yday
        
        filenames = []
        
        # Déterminer le format selon la semaine GPS
        use_new_format = gps_week >= 2238  # Transition novembre 2022
        
        if use_new_format:
            # Format moderne (depuis GPS Week 2238)
            if product_type == 'final':
                # 1. PRODUITS RÉELLEMENT COMBINÉS GPS+GLONASS (MGEX/Centres spécialisés)
                # COD (Center for Orbit Determination) - spécialiste multi-GNSS
                filenames.append(f"COD0MGXFIN_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz")  # Multi-GNSS 5min
                filenames.append(f"COD0MGXFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")  # Multi-GNSS 15min
                
                # GFZ (GeoForschungsZentrum) - expert multi-constellation
                filenames.append(f"GFZ0MGXFIN_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz")
                filenames.append(f"GFZ0MGXFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                
                # WUM (Wuhan University) - spécialiste BeiDou+Multi-GNSS
                filenames.append(f"WUM0MGXFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                
                # 2. PRODUITS COMBINÉS GPS+GLONASS spécifiques
                for center in ['COD', 'GFZ', 'JPL']:
                    filenames.append(f"{center}0GRXFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")  # GPS+GLONASS
                
                # 3. Produits IGS standard (GPS principalement) - en dernier recours
                filenames.append(f"IGS0OPSFIN_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                    
            elif product_type == 'rapid':
                # 1. PRODUITS RAPIDES MULTI-GNSS
                filenames.append(f"COD0MGXRAP_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz")
                filenames.append(f"GFZ0MGXRAP_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz")
                filenames.append(f"WUM0MGXRAP_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                
                # 2. PRODUITS RAPIDES GPS+GLONASS
                for center in ['COD', 'GFZ']:
                    filenames.append(f"{center}0GRXRAP_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                
                # 3. IGR Rapid standard
                filenames.append(f"IGS0OPSRAP_{year}{doy:03d}0000_01D_15M_ORB.SP3.gz")
                    
            elif product_type == 'ultra_rapid':
                # 1. PRODUITS ULTRA-RAPIDES MULTI-GNSS
                for hour in ['00', '06', '12', '18']:
                    filenames.append(f"COD0MGXULT_{year}{doy:03d}{hour}00_01D_05M_ORB.SP3.gz")
                    filenames.append(f"GFZ0MGXULT_{year}{doy:03d}{hour}00_01D_05M_ORB.SP3.gz")
                    
                    # 2. ULTRA-RAPIDES GPS+GLONASS
                    for center in ['COD', 'GFZ']:
                        filenames.append(f"{center}0GRXULT_{year}{doy:03d}{hour}00_01D_15M_ORB.SP3.gz")
                
                # 3. IGU Ultra-rapid standard
                for hour in ['00', '06', '12', '18']:
                    filenames.append(f"IGS0OPSULT_{year}{doy:03d}{hour}00_01D_15M_ORB.SP3.gz")
        
        else:
            # Format hérité (avant GPS Week 2238) - PRODUITS COMBINÉS HISTORIQUES
            if product_type == 'final':
                # 1. Produits combinés historiques centres spécialisés
                for center in ['cod', 'gfz', 'whu']:  # Centres multi-GNSS historiques
                    filenames.append(f"{center}{gps_week:04d}{day_of_week}.sp3.Z")
                
                # 2. Produits IGS standard historiques
                filenames.append(f"igs{gps_week:04d}{day_of_week}.sp3.Z")
                    
            elif product_type == 'rapid':
                # Produits rapides combinés historiques
                for center in ['cod', 'gfz']:
                    filenames.append(f"{center}r{gps_week:04d}{day_of_week}.sp3.Z")
                
                filenames.append(f"igr{gps_week:04d}{day_of_week}.sp3.Z")
                    
            elif product_type == 'ultra_rapid':
                # Ultra-rapides combinés historiques
                for hour in ['00', '06', '12', '18']:
                    for center in ['cod', 'gfz']:
                        filenames.append(f"{center}u{gps_week:04d}{day_of_week}_{hour}.sp3.Z")
                
                    filenames.append(f"igu{gps_week:04d}{day_of_week}_{hour}.sp3.Z")
        
        return filenames, gps_week, use_new_format
    
    def smart_download_sp3(self, target_date):
        """Téléchargement intelligent avec sélection automatique du produit optimal"""
        try:
            availability = self.analyze_data_availability(target_date)
            
            if availability['data_unavailable']:
                print(f"❌ Aucun produit disponible (minimum 3h requis)")
                return None
            
            optimal_product = availability['optimal_product']
            print(f"🔍 Téléchargement {optimal_product.upper()}...")
            
            result = self.download_product_type(target_date, optimal_product)
            if result:
                print(f"✅ Succès {optimal_product.upper()}")
                return result
            else:
                print(f"❌ Échec {optimal_product.upper()}")
                return None
            
        except Exception as e:
            logger.error(f"Erreur téléchargement: {str(e)}")
            return None
    
    def download_product_type(self, target_date, product_type):
        """Télécharge un type de produit spécifique"""
        try:
            filenames, gps_week, use_new_format = self.generate_combined_sp3_filenames(target_date, product_type)
            
            repositories = [
                f"{self.mgex_base}/{gps_week:04d}/",
                f"{self.cddis_base}/{gps_week:04d}/"
            ]
            
            for repo_url in repositories:
                for filename in filenames:
                    file_url = repo_url + filename
                    
                    try:
                        response = self.session.head(file_url, timeout=8)
                        
                        if response.status_code == 200:
                            print(f"   Trouvé: {filename}")
                            return self.download_file(file_url, filename)
                        
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur download_product_type: {str(e)}")
            return None
    
    def search_broadcast_ephemeris(self, target_date):
        """Recherche les éphémérides de diffusion multi-GNSS (solution de secours)"""
        try:
            gps_week, day_of_week, date_obj = self.date_to_gps_week(target_date)
            year = date_obj.year
            doy = date_obj.timetuple().tm_yday
            
            print(f"🌐 SOLUTION DE SECOURS: Éphémérides de diffusion")
            print(f"   📡 Constellations: GPS, GLONASS, Galileo, BeiDou, QZSS, SBAS")
            print(f"   ⚠️ Précision: 1-5 mètres (vs 2-3 cm pour SP3)")
            
            # Format moderne BRDM (Broadcast Multi-GNSS)
            filename = f"BRDM00DLR_S_{year}{doy:03d}0000_01D_MN.rnx.gz"
            
            # URLs prioritaires pour éphémérides
            urls_to_test = [
                f"{self.broadcast_base}/{year}/brdc/{filename}",
                f"{self.broadcast_base}/{year}/{doy:03d}/{year-2000:02d}p/{filename}"
            ]
            
            for i, url in enumerate(urls_to_test):
                try:
                    logger.info(f"Test éphémérides {i+1}: {url}")
                    response = self.session.head(url, timeout=15)
                    
                    if response.status_code == 200:
                        file_size = response.headers.get('content-length', 'Inconnu')
                        print(f"✅ Éphémérides de diffusion disponibles: {filename}")
                        print(f"   💾 Taille: {file_size} octets")
                        print(f"   🎯 Type: Données temps réel multi-GNSS RINEX")
                        
                        return self.download_file(url, filename)
                        
                except Exception as e:
                    logger.warning(f"Erreur test éphémérides {url}: {str(e)}")
                    continue
            
            print(f"❌ Aucune éphémérides de diffusion trouvée")
            print(f"💡 Suggérer de réessayer plus tard ou contacter support CDDIS")
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche éphémérides: {str(e)}")
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
            
            # Décompression automatique
            if filename.endswith('.gz'):
                return self.decompress_file(output_path)
            elif filename.endswith('.Z'):
                return self.decompress_unix_z(output_path)
            
            return str(output_path)
                    
        except Exception as e:
            logger.error(f"Erreur téléchargement {filename}: {str(e)}")
            return None
    
    def decompress_file(self, compressed_path):
        """Décompresse un fichier .gz avec gestion d'erreurs"""
        try:
            decompressed_path = compressed_path.with_suffix('')
            print(f"📦 Décompression gzip: {decompressed_path.name}")
            
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Supprimer le fichier compressé pour économiser l'espace
            compressed_path.unlink()
            
            size = decompressed_path.stat().st_size
            print(f"✅ Décompression réussie: {size:,} octets")
            return str(decompressed_path)
            
        except Exception as e:
            logger.error(f"Erreur décompression gzip: {str(e)}")
            return str(compressed_path)
    
    def decompress_unix_z(self, compressed_path):
        """Décompresse un fichier .Z (Unix compress)"""
        try:
            import subprocess
            decompressed_path = compressed_path.with_suffix('')
            print(f"📦 Décompression Unix .Z: {decompressed_path.name}")
            
            # Essayer la commande uncompress
            result = subprocess.run(['uncompress', str(compressed_path)], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and decompressed_path.exists():
                size = decompressed_path.stat().st_size
                print(f"✅ Décompression Unix réussie: {size:,} octets")
                return str(decompressed_path)
            else:
                print(f"⚠️ Décompression Unix échouée, fichier gardé compressé")
                return str(compressed_path)
                
        except Exception as e:
            logger.warning(f"Erreur décompression Unix: {str(e)}")
            print(f"⚠️ Fichier gardé compressé: {compressed_path}")
            return str(compressed_path)
    
    def analyze_sp3_file(self, file_path):
        """Analyse factuelle d'un fichier SP3"""
        try:
            print(f"\n📊 ANALYSE FICHIER SP3")
            print(f"📁 {Path(file_path).name}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            satellites = {}
            constellations = set()
            all_satellites = set()
            
            for line in lines[:200]:
                if line.startswith('+'):
                    sat_section = line[9:].strip()
                    pos = 0
                    while pos < len(sat_section):
                        if pos + 2 < len(sat_section):
                            sat_id = sat_section[pos:pos+3]
                            if len(sat_id) == 3 and sat_id[0].isalpha() and sat_id[1:].isdigit():
                                constellation = sat_id[0].upper()
                                constellations.add(constellation)
                                all_satellites.add(sat_id)
                                if constellation not in satellites:
                                    satellites[constellation] = set()
                                satellites[constellation].add(sat_id)
                        pos += 3
            
            constellation_names = {
                'G': 'GPS', 'R': 'GLONASS', 'E': 'Galileo', 
                'C': 'BeiDou', 'J': 'QZSS', 'S': 'SBAS'
            }
            
            file_size = Path(file_path).stat().st_size
            total_satellites = len(all_satellites)
            
            print(f"💾 Taille: {file_size / (1024*1024):.2f} MB")
            print(f"🛰️ Satellites: {total_satellites}")
            print(f"🌐 Constellations: {len(constellations)}")
            
            for const_code in sorted(constellations):
                const_name = constellation_names.get(const_code, f'Constellation {const_code}')
                sat_count = len(satellites.get(const_code, []))
                print(f"   {const_name}: {sat_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur analyse: {str(e)}")
            return False

def main():
    """Script principal avec saisie directe de la date"""
    
    # Configuration avec token JWT valide
    JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImEubWV1bmllciIsImV4cCI6MTc1NzYzNjk3NSwiaWF0IjoxNzUyNDUyOTc1LCJpc3MiOiJodHRwczovL3Vycy5lYXJ0aGRhdGEubmFzYS5nb3YiLCJpZGVudGl0eV9wcm92aWRlciI6ImVkbF9vcHMiLCJhY3IiOiJlZGwiLCJhc3N1cmFuY2VfbGV2ZWwiOjN9.nAL8KSU_RDW9ldNEhT-EAbdEZagLNLTeOD_VYq9Bas-UcRSaempBuZ3RiFyX18q7I0fV2bUiLTKV-ME-Ra_yyU_ODT76GNvx48v9QWMB_rzY3W9gXgeyoG05bqgauZJGpLiHyxkMozHLClG_JT23Pcsjmk1dXliW6bW58-vYZnUmKe2mXxDGdbUUfIM6D3mjHbijXQ_MSYZtyxeb9fxcPIfqFTUMmlQ90QqcxSahp2rDLDZBRdxauj0c9xPrsq_SlDoGGJcWx0qDuBz0Z2VkFP3cBJsoFIEhRQrccIn5v9Ykqdr9s224bEWkQGT8dDrO_Rv2rhr6RcFZLYVfwMQURQ"
    
    # RÉPERTOIRE DE SORTIE SPÉCIFIQUE
    OUTPUT_DIRECTORY = r"C:\1-Data\01-Projet\ProjetPY\Test_GNSS"
    
    today = datetime.now()
    
    try:
        print("=" * 80)
        print("TÉLÉCHARGEUR SP3 INTELLIGENT - PRODUITS COMBINÉS GPS/GLONASS V2.1")
        print("Logique optimisée: IGS Final → IGR Rapid → IGU Ultra-rapid")
        print("=" * 80)
        
        print(f"\n📁 RÉPERTOIRE DE SORTIE: {OUTPUT_DIRECTORY}")
        
        # Vérifier et créer le répertoire de sortie
        output_path = Path(OUTPUT_DIRECTORY)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Répertoire créé avec succès")
            except Exception as e:
                print(f"❌ Impossible de créer le répertoire: {e}")
                return
        else:
            print(f"✅ Répertoire existe déjà")
        
        # Vérifier les permissions d'écriture
        try:
            test_file = output_path / "test_permissions.tmp"
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            print(f"✅ Permissions d'écriture vérifiées")
        except Exception as e:
            print(f"❌ Problème de permissions d'écriture: {e}")
            return
        
        print(f"\n🕐 Date et heure actuelles: {today.strftime('%d/%m/%Y à %H:%M:%S UTC')}")
        print(f"\n📋 SEUILS DE DISPONIBILITÉ DES PRODUITS:")
        print(f"   🎯 IGS Final: ≥ 12 jours (précision 2-3 cm) - PRIORITÉ 1")
        print(f"   ⚡ IGR Rapid: ≥ 1 jour (précision 2,5 cm) - PRIORITÉ 2")
        print(f"   🚀 IGU Ultra-rapid: ≥ 3 heures (précision 3-5 cm) - PRIORITÉ 3")
        
        print(f"\n📅 EXEMPLES DE DATES ET PRODUITS ATTENDUS:")
        print(f"   • {(today - timedelta(days=15)).strftime('%d/%m/%Y')} → IGS Final disponible (optimal)")
        print(f"   • {(today - timedelta(days=2)).strftime('%d/%m/%Y')} → IGR Rapid disponible")
        print(f"   • {(today - timedelta(hours=6)).strftime('%d/%m/%Y')} → IGU Ultra-rapid disponible")
        print(f"   • {today.strftime('%d/%m/%Y')} → Aucun produit disponible")
        
        # Saisie directe de la date
        print(f"\n" + "=" * 60)
        while True:
            target_date = input("📅 Entrez la date souhaitée (DD/MM/YYYY): ").strip()
            
            if not target_date:
                print("❌ Veuillez entrer une date.")
                continue
                
            try:
                # Validation du format de date
                date_obj = datetime.strptime(target_date, "%d/%m/%Y")
                
                # Vérification que la date n'est pas dans le futur
                if date_obj > today:
                    print(f"❌ Date dans le futur! La date doit être antérieure à {today.strftime('%d/%m/%Y')}")
                    continue
                
                # Vérification que la date n'est pas trop ancienne (>5 ans)
                five_years_ago = today - timedelta(days=5*365)
                if date_obj < five_years_ago:
                    print(f"⚠️ Date très ancienne (>{five_years_ago.strftime('%d/%m/%Y')}). Les données peuvent ne plus être disponibles.")
                    confirm = input("Continuer quand même? (o/n): ").strip().lower()
                    if confirm not in ['o', 'oui', 'y', 'yes']:
                        continue
                
                print(f"✅ Date validée: {target_date}")
                break
                
            except ValueError:
                print("❌ Format de date invalide. Utilisez le format DD/MM/YYYY")
                print("   Exemples valides: 16/06/2025, 01/12/2024, 25/03/2023")
                continue
        
        # Initialiser le téléchargeur avec le répertoire spécifique
        print(f"\n🔧 Initialisation du téléchargeur...")
        downloader = SP3CombinedDownloader(JWT_TOKEN, output_dir=OUTPUT_DIRECTORY)
        print(f"✅ Configuration terminée")
        print(f"📂 Fichiers seront sauvegardés dans: {OUTPUT_DIRECTORY}")
        
        # Lancement du téléchargement intelligent
        print(f"\n🚀 DÉBUT DU PROCESSUS DE TÉLÉCHARGEMENT")
        print("=" * 60)
        
        downloaded_file = downloader.smart_download_sp3(target_date)
        
        if downloaded_file:
            print(f"\n🎉 TÉLÉCHARGEMENT RÉUSSI!")
            print("=" * 60)
            print(f"📁 Fichier téléchargé: {Path(downloaded_file).name}")
            print(f"📂 Chemin complet: {downloaded_file}")
            print(f"💾 Taille: {Path(downloaded_file).stat().st_size / (1024*1024):.2f} MB")
            
            # Vérifier que le fichier existe bien
            if Path(downloaded_file).exists():
                print(f"✅ Fichier confirmé à l'emplacement: {downloaded_file}")
            else:
                print(f"❌ ATTENTION: Fichier introuvable à l'emplacement indiqué!")
            
            # Analyse détaillée automatique
            print(f"\n🔍 Lancement de l'analyse détaillée...")
            analysis_success = downloader.analyze_sp3_file(downloaded_file)
            
            if analysis_success:
                print(f"\n💡 FICHIER PRÊT POUR UTILISATION")
                print("=" * 60)
                print(f"🎯 Applications recommandées:")
                print(f"   • Positionnement précis (PPP, RTK)")
                print(f"   • Géodésie et cartographie haute précision")
                print(f"   • Navigation scientifique")
                print(f"   • Surveillance géophysique")
                print(f"\n🌍 Avantages multi-constellation:")
                print(f"   • Couverture mondiale optimisée")
                print(f"   • Géométrie satellite supérieure")
                print(f"   • Convergence rapide des solutions")
                print(f"   • Robustesse en environnement dégradé")
                
                print(f"\n📁 LOCALISATION FINALE:")
                print(f"   📂 Dossier: {OUTPUT_DIRECTORY}")
                print(f"   📄 Fichier: {Path(downloaded_file).name}")
            
        else:
            print(f"\n❌ TÉLÉCHARGEMENT ÉCHOUÉ")
            print("=" * 60)
            print(f"💡 Suggestions de dépannage:")
            print(f"   1. Vérifiez que la date respecte les seuils de disponibilité")
            print(f"   2. Essayez une date plus ancienne (>15 jours pour IGS Final)")
            print(f"   3. Vérifiez votre connexion internet")
            print(f"   4. Les serveurs CDDIS peuvent être temporairement indisponibles")
            print(f"   5. Contactez le support NASA Earthdata si le problème persiste")
            
            print(f"\n🔄 Options de récupération:")
            print(f"   • Relancer avec une date plus ancienne")
            print(f"   • Utiliser les éphémérides de diffusion (précision réduite)")
            print(f"   • Attendre la disponibilité des produits plus récents")
        
        print(f"\n" + "=" * 80)
        print(f"Téléchargeur SP3 - Session terminée à {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️ INTERRUPTION UTILISATEUR")
        print(f"Session terminée par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur dans le script principal: {str(e)}")
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        print(f"💡 Contactez le support technique si le problème persiste")
        
        # Initialiser le téléchargeur avec configuration optimisée
        print(f"\n🔧 Initialisation du téléchargeur...")
        downloader = SP3CombinedDownloader(JWT_TOKEN)
        print(f"✅ Configuration terminée")
        
        # Lancement du téléchargement intelligent
        print(f"\n🚀 DÉBUT DU PROCESSUS DE TÉLÉCHARGEMENT")
        print("=" * 60)
        
        downloaded_file = downloader.smart_download_sp3(target_date)
        
        if downloaded_file:
            print(f"\n🎉 TÉLÉCHARGEMENT RÉUSSI!")
            print("=" * 60)
            print(f"📁 Fichier téléchargé: {Path(downloaded_file).name}")
            print(f"📂 Chemin complet: {downloaded_file}")
            print(f"💾 Taille: {Path(downloaded_file).stat().st_size / (1024*1024):.2f} MB")
            
            # Analyse détaillée automatique
            print(f"\n🔍 Lancement de l'analyse détaillée...")
            analysis_success = downloader.analyze_sp3_file(downloaded_file)
            
            if analysis_success:
                print(f"\n💡 FICHIER PRÊT POUR UTILISATION")
                print("=" * 60)
                print(f"🎯 Applications recommandées:")
                print(f"   • Positionnement précis (PPP, RTK)")
                print(f"   • Géodésie et cartographie haute précision")
                print(f"   • Navigation scientifique")
                print(f"   • Surveillance géophysique")
                print(f"\n🌍 Avantages multi-constellation:")
                print(f"   • Couverture mondiale optimisée")
                print(f"   • Géométrie satellite supérieure")
                print(f"   • Convergence rapide des solutions")
                print(f"   • Robustesse en environnement dégradé")
            
        else:
            print(f"\n❌ TÉLÉCHARGEMENT ÉCHOUÉ")
            print("=" * 60)
            print(f"💡 Suggestions de dépannage:")
            print(f"   1. Vérifiez que la date respecte les seuils de disponibilité")
            print(f"   2. Essayez une date plus ancienne (>15 jours pour IGS Final)")
            print(f"   3. Vérifiez votre connexion internet")
            print(f"   4. Les serveurs CDDIS peuvent être temporairement indisponibles")
            print(f"   5. Contactez le support NASA Earthdata si le problème persiste")
            
            print(f"\n🔄 Options de récupération:")
            print(f"   • Relancer avec une date plus ancienne")
            print(f"   • Utiliser les éphémérides de diffusion (précision réduite)")
            print(f"   • Attendre la disponibilité des produits plus récents")
        
        print(f"\n" + "=" * 80)
        print(f"Téléchargeur SP3 - Session terminée à {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️ INTERRUPTION UTILISATEUR")
        print(f"Session terminée par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur dans le script principal: {str(e)}")
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        print(f"💡 Contactez le support technique si le problème persiste")
        
        # Initialiser le téléchargeur avec configuration optimisée
        print(f"\n🔧 Initialisation du téléchargeur...")
        downloader = SP3CombinedDownloader(JWT_TOKEN)
        print(f"✅ Configuration terminée")
        
        # Lancement du téléchargement intelligent
        print(f"\n🚀 DÉBUT DU PROCESSUS DE TÉLÉCHARGEMENT")
        print("=" * 60)
        
        downloaded_file = downloader.smart_download_sp3(target_date)
        
        if downloaded_file:
            print(f"\n🎉 TÉLÉCHARGEMENT RÉUSSI!")
            print("=" * 60)
            print(f"📁 Fichier téléchargé: {Path(downloaded_file).name}")
            print(f"📂 Chemin complet: {downloaded_file}")
            print(f"💾 Taille: {Path(downloaded_file).stat().st_size / (1024*1024):.2f} MB")
            
            # Analyse détaillée automatique
            print(f"\n🔍 Lancement de l'analyse détaillée...")
            analysis_success = downloader.analyze_sp3_file(downloaded_file)
            
            if analysis_success:
                print(f"\n💡 FICHIER PRÊT POUR UTILISATION")
                print("=" * 60)
                print(f"🎯 Applications recommandées:")
                print(f"   • Positionnement précis (PPP, RTK)")
                print(f"   • Géodésie et cartographie haute précision")
                print(f"   • Navigation scientifique")
                print(f"   • Surveillance géophysique")
                print(f"\n🌍 Avantages multi-constellation:")
                print(f"   • Couverture mondiale optimisée")
                print(f"   • Géométrie satellite supérieure")
                print(f"   • Convergence rapide des solutions")
                print(f"   • Robustesse en environnement dégradé")
            
        else:
            print(f"\n❌ TÉLÉCHARGEMENT ÉCHOUÉ")
            print("=" * 60)
            print(f"💡 Suggestions de dépannage:")
            print(f"   1. Vérifiez que la date respecte les seuils de disponibilité")
            print(f"   2. Essayez une date plus ancienne (>15 jours pour IGS Final)")
            print(f"   3. Vérifiez votre connexion internet")
            print(f"   4. Les serveurs CDDIS peuvent être temporairement indisponibles")
            print(f"   5. Contactez le support NASA Earthdata si le problème persiste")
            
            print(f"\n🔄 Options de récupération:")
            print(f"   • Relancer avec une date plus ancienne")
            print(f"   • Utiliser les éphémérides de diffusion (précision réduite)")
            print(f"   • Attendre la disponibilité des produits plus récents")
        
        print(f"\n" + "=" * 80)
        print(f"Téléchargeur SP3 - Session terminée à {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print(f"\n\n⏸️ INTERRUPTION UTILISATEUR")
        print(f"Session terminée par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur dans le script principal: {str(e)}")
        print(f"\n❌ ERREUR CRITIQUE: {str(e)}")
        print(f"💡 Contactez le support technique si le problème persiste")

if __name__ == "__main__":
    main()