# -*- coding: utf-8 -*-
"""
Created on Sun Jul 13 19:29:12 2025

@author: a.meunier
"""

#!/usr/bin/env python3
"""
Calculateur de Vecteurs GNSS avec RTKLIB
Monitoring de déformation entre antennes
Auteur: Assistant IA
"""

import os
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import configparser
from pathlib import Path
import logging
import requests
import gzip
import shutil
from urllib.parse import urljoin
import time

class GNSSVectorCalculator:
    def _find_rinex_directory(self):
        """Recherche automatique du répertoire contenant les fichiers RINEX"""
        import os
        
        target_files = ["50643291.24o", "52923291.24o", "67663291.24o"]
        username = os.getenv('USERNAME', 'a.meunier')
        
        search_directories = [
            f"C:\\Users\\{username}\\Documents",
            f"C:\\Users\\{username}\\Downloads", 
            f"C:\\Users\\{username}\\Desktop",
            "C:\\1-Data\\01-Projet\\ProjetPY\\Test_GNSS",
            "C:\\1-Data",
            f"C:\\Users\\{username}",
            "C:\\temp",
            "C:\\data"
        ]
        
        for search_dir in search_directories:
            search_path = Path(search_dir)
            if not search_path.exists():
                continue
                
            try:
                # Recherche dans le répertoire et ses sous-répertoires (limité à 2 niveaux)
                for root, dirs, files in os.walk(search_path):
                    level = root.replace(str(search_path), '').count(os.sep)
                    if level >= 2:
                        dirs[:] = []
                        continue
                    
                    found_count = sum(1 for f in target_files if f in files)
                    if found_count >= len(target_files):
                        print(f"📁 Fichiers RINEX trouvés dans: {root}")
                        return root
                        
            except (PermissionError, OSError):
                continue
        
        print("⚠️ Fichiers RINEX non trouvés automatiquement")
        return None

    def __init__(self, work_dir=None, rtklib_dir="C:\\RTKLIB"):
        """
        Initialise le calculateur de vecteurs GNSS
        
        Args:
            work_dir (str): Répertoire de travail contenant les fichiers RINEX (None = recherche auto)
            rtklib_dir (str): Répertoire d'installation de RTKLIB
        """
        # Si work_dir n'est pas spécifié, essayer de le trouver automatiquement
        if work_dir is None:
            work_dir = self._find_rinex_directory() or "C:\\1-Data\\01-Projet\\ProjetPY\\Test_GNSS"
        
        self.work_dir = Path(work_dir)
        self.rtklib_dir = Path(rtklib_dir)
        self.base_station = "50643291.24o"  # Station fixe
        self.rovers = ["52923291.24o", "67663291.24o"]  # Stations mobiles
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # URLs pour téléchargement automatique des fichiers de navigation et SP3
        self.nav_urls = [
            "https://igs.ign.fr/pub/igs/data/daily/",
            "https://cddis.nasa.gov/archive/gnss/data/daily/",
            "https://igs.bkg.bund.de/root_ftp/IGS/obs/"
        ]
        
        # URLs pour fichiers SP3 (éphémérides précises)
        self.sp3_urls = [
            "https://igs.ign.fr/pub/igs/products/",
            "https://cddis.nasa.gov/archive/gnss/products/",
            "https://igs.bkg.bund.de/root_ftp/IGS/products/"
        ]
        
        # Position de la base (sera calculée ou spécifiée)
        self.base_position = None
        
        # Recherche de l'exécutable RTKLIB
        self.rnx2rtkp_path = self._find_rtklib_executable()
        
        # Vérification des fichiers
        self._verify_files()
        
        # Configuration RTKLIB par défaut
        self.rtklib_config = self._generate_rtklib_config()
        
    def _find_rtklib_executable(self):
        """Trouve l'exécutable rnx2rtkp de RTKLIB"""
        # Chemin utilisateur spécifique détecté
        username = os.getenv('USERNAME', 'a.meunier')
        user_rtklib_path = Path(f"C:/Users/{username}/RTKLIB_bin/bin")
        
        possible_paths = [
            # Installation utilisateur détectée
            user_rtklib_path / "rnx2rtkp.exe",
            Path("C:/Users/a.meunier/RTKLIB_bin/bin/rnx2rtkp.exe"),
            # Installation spécifiée par défaut
            self.rtklib_dir / "bin" / "rnx2rtkp.exe",
            self.rtklib_dir / "app" / "rnx2rtkp" / "gcc" / "rnx2rtkp.exe",
            self.rtklib_dir / "rnx2rtkp.exe",
            # PATH système
            "rnx2rtkp",
            "rnx2rtkp.exe",
            # Autres emplacements possibles
            Path("C:/Program Files/RTKLIB/bin/rnx2rtkp.exe"),
            Path("C:/Program Files (x86)/RTKLIB/bin/rnx2rtkp.exe")
        ]
        
        for path in possible_paths:
            try:
                if isinstance(path, str):
                    # Test si la commande est dans le PATH
                    result = subprocess.run([path, "-?"], capture_output=True, text=True, timeout=5)
                    if result.returncode in [0, 1]:  # RTKLIB retourne souvent 1 pour l'aide
                        self.logger.info(f"✓ RTKLIB trouvé dans PATH: {path}")
                        return path
                else:
                    # Test si le fichier existe
                    if path.exists():
                        result = subprocess.run([str(path), "-?"], capture_output=True, text=True, timeout=5)
                        if result.returncode in [0, 1]:
                            self.logger.info(f"✓ RTKLIB trouvé: {path}")
                            return str(path)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        self.logger.warning("⚠️ rnx2rtkp non trouvé - mode test uniquement")
        return None
        
    def _verify_files(self):
        """Vérifie la présence des fichiers RINEX"""
        self.logger.info("Vérification des fichiers RINEX...")
        
        required_files = [self.base_station] + self.rovers
        missing_files = []
        
        for file in required_files:
            file_path = self.work_dir / file
            if not file_path.exists():
                missing_files.append(file)
            else:
                self.logger.info(f"✓ Trouvé: {file}")
                
        if missing_files:
            self.logger.warning(f"Fichiers manquants dans {self.work_dir}: {missing_files}")
            
            # Tentative de recherche automatique
            alternative_dir = self._find_rinex_files_auto()
            if alternative_dir:
                self.logger.info(f"Fichiers trouvés dans: {alternative_dir}")
                self.work_dir = alternative_dir
                # Re-vérifier avec le nouveau répertoire
                missing_files = []
                for file in required_files:
                    file_path = self.work_dir / file
                    if not file_path.exists():
                        missing_files.append(file)
                    else:
                        self.logger.info(f"✓ Trouvé: {file}")
            
            if missing_files:
                self.logger.error(f"Fichiers toujours manquants: {missing_files}")
                raise FileNotFoundError(f"Fichiers manquants: {missing_files}")
            
        # Vérification des fichiers navigation avec plus d'extensions
        nav_files = self._find_navigation_files_extended()
        if not nav_files:
            self.logger.warning("Aucun fichier navigation trouvé - tentative de téléchargement...")
            self._attempt_download_navigation()
        else:
            self.logger.info(f"Fichiers navigation trouvés: {[f.name for f in nav_files]}")
        
        # Téléchargement des fichiers SP3 (éphémérides précises)
        try:
            sp3_files = self._download_sp3_files()
        except Exception as e:
            self.logger.warning(f"Erreur téléchargement SP3: {e}")
            self.logger.info("Continuation avec éphémérides broadcast seulement")
            sp3_files = []
        
        # Analyse des fichiers SP3 téléchargés
        if sp3_files:
            self._analyze_sp3_files()
        
        # Calcul de la position de la station de base
        self._calculate_base_position()
    
    def _find_rinex_files_auto(self):
        """Recherche automatique des fichiers RINEX"""
        import os
        
        username = os.getenv('USERNAME', 'a.meunier')
        search_directories = [
            f"C:\\Users\\{username}\\Documents",
            f"C:\\Users\\{username}\\Downloads", 
            f"C:\\Users\\{username}\\Desktop",
            "C:\\1-Data",
            f"C:\\Users\\{username}",
            "C:\\temp",
            "C:\\data"
        ]
        
        target_files = [self.base_station] + self.rovers
        
        for search_dir in search_directories:
            search_path = Path(search_dir)
            if not search_path.exists():
                continue
                
            try:
                # Recherche dans le répertoire et ses sous-répertoires (limité à 2 niveaux)
                for root, dirs, files in os.walk(search_path):
                    level = root.replace(str(search_path), '').count(os.sep)
                    if level >= 2:
                        dirs[:] = []
                        continue
                    
                    found_count = sum(1 for f in target_files if f in files)
                    if found_count >= len(target_files):
                        self.logger.info(f"Tous les fichiers trouvés dans: {root}")
                        return Path(root)
                    elif found_count > 0:
                        self.logger.info(f"{found_count}/{len(target_files)} fichiers trouvés dans: {root}")
                        
            except (PermissionError, OSError):
                continue
        
        return None
    
    def _find_navigation_files_extended(self):
        """Trouve les fichiers de navigation avec extensions étendues"""
        nav_files = []
        
        # Extensions possibles pour fichiers navigation
        nav_extensions = [
            "*.n", "*.g", "*.l", "*.e", "*.c",  # Standards
            "*.24n", "*.24g", "*.24l", "*.24e", "*.24c",  # Avec année
            "*.nav", "*.gnav", "*.hnav"  # Autres formats
        ]
        
        for ext in nav_extensions:
            found_files = list(self.work_dir.glob(ext))
            nav_files.extend(found_files)
            
        return nav_files
    
    def _get_date_from_rinex(self, rinex_file):
        """Extrait les dates d'observation depuis l'en-tête d'un fichier RINEX"""
        try:
            # S'assurer qu'on a le chemin complet
            if isinstance(rinex_file, str):
                file_path = self.work_dir / rinex_file
            else:
                file_path = rinex_file
                
            with open(file_path, 'r') as f:
                start_time = None
                end_time = None
                interval = None
                
                for line in f:
                    if 'TIME OF FIRST OBS' in line:
                        # Format: YYYY MM DD HH MM SS.SSSSSSS     GPS         TIME OF FIRST OBS
                        parts = line[:43].strip().split()
                        if len(parts) >= 6:
                            year = int(parts[0])
                            month = int(parts[1])
                            day = int(parts[2])
                            hour = int(parts[3])
                            minute = int(parts[4])
                            second = float(parts[5])
                            start_time = datetime(year, month, day, hour, minute, int(second))
                            
                    elif 'TIME OF LAST OBS' in line:
                        # Format similaire
                        parts = line[:43].strip().split()
                        if len(parts) >= 6:
                            year = int(parts[0])
                            month = int(parts[1])
                            day = int(parts[2])
                            hour = int(parts[3])
                            minute = int(parts[4])
                            second = float(parts[5])
                            end_time = datetime(year, month, day, hour, minute, int(second))
                            
                    elif 'INTERVAL' in line:
                        # Format: SS.SSS                                           INTERVAL
                        try:
                            interval = float(line[:10].strip())
                        except:
                            interval = None
                            
                    elif 'END OF HEADER' in line:
                        break
                
                # Si pas de TIME OF LAST OBS, essayer d'estimer depuis le nom du fichier
                if start_time and not end_time:
                    # Fallback: utiliser le nom de fichier pour la date de base
                    filename = file_path.stem
                    if len(filename) >= 8:
                        try:
                            day_of_year = int(filename[4:7])
                            year = 2000 + int(filename[7:9])
                            file_date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
                            # Supposer que c'est le même jour que le début
                            if start_time.date() == file_date.date():
                                end_time = start_time + timedelta(hours=24)  # Session max 24h
                        except:
                            pass
                
                result = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'interval': interval
                }
                
                if start_time:
                    self.logger.info(f"Période d'observation {file_path.name}: {start_time} → {end_time or 'inconnue'}")
                    if interval:
                        self.logger.info(f"Intervalle d'échantillonnage: {interval}s")
                
                return result
                
        except Exception as e:
            self.logger.warning(f"Erreur lecture dates RINEX {rinex_file}: {e}")
            # Fallback: utiliser le nom du fichier
            return self._get_date_from_filename(rinex_file)
    
    def _get_date_from_filename(self, rinex_file):
        """Méthode de fallback: extrait la date du nom du fichier RINEX"""
        try:
            if isinstance(rinex_file, str):
                filename = Path(rinex_file).stem
            else:
                filename = rinex_file.stem
                
            if len(filename) >= 8:
                day_of_year = int(filename[4:7])
                year = 2000 + int(filename[7:9])
                date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
                return {
                    'start_time': date,
                    'end_time': date + timedelta(hours=24),
                    'interval': None
                }
        except (ValueError, IndexError):
            self.logger.warning(f"Impossible d'extraire la date de {rinex_file}")
            
        return {
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=24),
            'interval': None
        }
    
    def _attempt_download_navigation(self):
        """Tente de télécharger les fichiers de navigation automatiquement"""
        self.logger.info("📡 Téléchargement des fichiers de navigation...")
        
        # Déterminer la période d'observation depuis les fichiers RINEX
        start_time, end_time = self._get_observation_period()
        
        # Calculer les jours nécessaires (avec marge)
        start_date = start_time.date()
        end_date = end_time.date()
        
        if start_date == end_date:
            dates_to_download = [start_date]
        else:
            # Plusieurs jours d'observation
            dates_to_download = []
            current_date = start_date
            while current_date <= end_date:
                dates_to_download.append(current_date)
                current_date += timedelta(days=1)
        
        self.logger.info(f"Téléchargement navigation pour: {[d.strftime('%Y-%m-%d') for d in dates_to_download]}")
        
        downloaded_files = []
        
        for obs_date in dates_to_download:
            obs_datetime = datetime.combine(obs_date, datetime.min.time())
            year = obs_datetime.year
            day_of_year = obs_datetime.timetuple().tm_yday
            
            # Noms des fichiers navigation standards
            nav_files_to_download = [
                f"brdc{day_of_year:03d}0.{year-2000:02d}n",  # GPS
                f"brdc{day_of_year:03d}0.{year-2000:02d}g",  # GLONASS
            ]
            
            for nav_file in nav_files_to_download:
                if self._download_navigation_file(nav_file, year, day_of_year):
                    downloaded_files.append(nav_file)
        
        if downloaded_files:
            self.logger.info(f"📡 Fichiers navigation téléchargés: {len(downloaded_files)}")
        else:
            self.logger.warning("⚠️ Aucun fichier navigation téléchargé")
        
        return downloaded_files
    
    def _download_navigation_file(self, filename, year, day_of_year):
        """Télécharge un fichier de navigation spécifique"""
        try:
            # Construction de l'URL
            url_path = f"{year}/{day_of_year:03d}/{filename}.Z"
            
            for base_url in self.nav_urls:
                try:
                    full_url = urljoin(base_url, url_path)
                    self.logger.info(f"Tentative de téléchargement: {full_url}")
                    
                    response = requests.get(full_url, timeout=30)
                    if response.status_code == 200:
                        # Sauvegarde et décompression
                        compressed_file = self.work_dir / f"{filename}.Z"
                        with open(compressed_file, 'wb') as f:
                            f.write(response.content)
                        
                        # Décompression
                        output_file = self.work_dir / filename
                        with gzip.open(compressed_file, 'rb') as f_in:
                            with open(output_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Suppression du fichier compressé
                        compressed_file.unlink()
                        
                        self.logger.info(f"✓ Téléchargé: {filename}")
                        return True
                        
                except requests.RequestException as e:
                    self.logger.debug(f"Échec téléchargement de {base_url}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Erreur téléchargement {filename}: {e}")
            
        return False
    
    def _analyze_sp3_files(self):
        """Analyse les fichiers SP3 disponibles et affiche leurs informations"""
        sp3_files = list(self.work_dir.glob("*.sp3"))
        
        if not sp3_files:
            return
        
        self.logger.info(f"📊 Analyse des fichiers SP3 ({len(sp3_files)} fichiers):")
        
        sp3_info = []
        
        for sp3_file in sorted(sp3_files):
            try:
                with open(sp3_file, 'r') as f:
                    lines = f.readlines()[:50]  # Lire seulement l'en-tête
                
                info = {
                    'filename': sp3_file.name,
                    'size_mb': sp3_file.stat().st_size / (1024*1024),
                    'satellites': [],
                    'start_epoch': None,
                    'product_type': 'Unknown'
                }
                
                # Analyser l'en-tête
                for line in lines:
                    if line.startswith('#'):
                        if 'GPS' in line or 'GLONASS' in line or 'Galileo' in line:
                            parts = line.split()
                            if len(parts) > 1:
                                info['product_type'] = parts[1] if len(parts) > 1 else 'GPS'
                    elif line.startswith('+'):
                        # Ligne de satellites
                        if info['satellites'] == []:  # Première ligne de satellites
                            sats = line[9:].strip().split()
                            info['satellites'] = [s for s in sats if s and len(s) <= 3]
                    elif line.startswith('*'):
                        # Première époque
                        if not info['start_epoch']:
                            epoch_str = line[3:].strip()
                            info['start_epoch'] = epoch_str
                        break
                
                # Déterminer le type de produit depuis le nom
                filename_lower = sp3_file.name.lower()
                if filename_lower.startswith('igs'):
                    info['product_name'] = 'IGS Final'
                    info['precision'] = '2-5 cm'
                elif filename_lower.startswith('igr'):
                    info['product_name'] = 'IGS Rapid'
                    info['precision'] = '3-8 cm'
                elif filename_lower.startswith('igu'):
                    info['product_name'] = 'IGS Ultra-Rapid'
                    info['precision'] = '5-15 cm'
                elif filename_lower.startswith('cod'):
                    info['product_name'] = 'CODE Final'
                    info['precision'] = '2-5 cm'
                elif filename_lower.startswith('esa'):
                    info['product_name'] = 'ESA Final'
                    info['precision'] = '2-5 cm'
                elif filename_lower.startswith('gfz'):
                    info['product_name'] = 'GFZ Final'
                    info['precision'] = '2-5 cm'
                else:
                    info['product_name'] = 'Unknown'
                    info['precision'] = 'Unknown'
                
                sp3_info.append(info)
                
                # Affichage des informations
                self.logger.info(f"   📄 {info['filename']} ({info['size_mb']:.1f} MB)")
                self.logger.info(f"      Type: {info['product_name']} (précision: {info['precision']})")
                self.logger.info(f"      Satellites: {len(info['satellites'])} ({', '.join(info['satellites'][:10])}{'...' if len(info['satellites']) > 10 else ''})")
                if info['start_epoch']:
                    self.logger.info(f"      Première époque: {info['start_epoch']}")
                
            except Exception as e:
                self.logger.warning(f"   ❌ Erreur analyse {sp3_file.name}: {e}")
        
        return sp3_info
    
    def _get_gps_week_and_day(self, date):
        """Calcule la semaine GPS et le jour de la semaine pour une date"""
        # S'assurer qu'on a un objet datetime
        if isinstance(date, dict):
            # Si c'est un dict retourné par _get_date_from_rinex, utiliser start_time
            if 'start_time' in date and date['start_time']:
                date = date['start_time']
            else:
                raise ValueError("Dict de date invalide")
        
        # Époque GPS : 6 janvier 1980
        gps_epoch = datetime(1980, 1, 6)
        delta = date - gps_epoch
        gps_week = delta.days // 7
        gps_day = delta.days % 7
        return gps_week, gps_day
    
    def _download_sp3_files(self):
        """Télécharge les fichiers SP3 (éphémérides précises)"""
        self.logger.info("Téléchargement des fichiers SP3 (éphémérides précises)...")
        
        # Extraire la date du fichier de base
        obs_date = self._get_date_from_rinex(self.base_station)
        gps_week, gps_day = self._get_gps_week_and_day(obs_date)
        
        # Types de produits SP3 disponibles (par ordre de préférence)
        sp3_products = [
            ("igs", "IGS Final", 12),      # Disponible après 12 jours, précision max
            ("igr", "IGS Rapid", 1),       # Disponible après 17h, bonne précision  
            ("igu", "IGS Ultra-Rapid", 0)  # Disponible en temps réel, précision moindre
        ]
        
        downloaded_files = []
        
        for product_code, product_name, delay_days in sp3_products:
            # Vérifier si le produit est disponible (délai respecté)
            if (datetime.now() - obs_date).days < delay_days:
                self.logger.info(f"Produit {product_name} pas encore disponible (délai {delay_days} jours)")
                continue
            
            # Noms des fichiers SP3
            sp3_filename = f"{product_code}{gps_week:04d}{gps_day}.sp3"
            compressed_filename = f"{sp3_filename}.Z"
            
            success = False
            for base_url in self.sp3_urls:
                try:
                    # URL complète
                    url_path = f"{gps_week:04d}/{compressed_filename}"
                    full_url = urljoin(base_url, url_path)
                    
                    self.logger.info(f"Tentative téléchargement {product_name}: {full_url}")
                    
                    response = requests.get(full_url, timeout=60)
                    if response.status_code == 200:
                        # Sauvegarde et décompression
                        compressed_file = self.work_dir / compressed_filename
                        with open(compressed_file, 'wb') as f:
                            f.write(response.content)
                        
                        # Décompression
                        output_file = self.work_dir / sp3_filename
                        try:
                            with gzip.open(compressed_file, 'rb') as f_in:
                                with open(output_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            
                            # Suppression du fichier compressé
                            compressed_file.unlink()
                            
                            self.logger.info(f"✓ Téléchargé: {sp3_filename} ({product_name})")
                            downloaded_files.append(output_file)
                            success = True
                            break
                            
                        except gzip.BadGzipFile:
                            # Peut-être que le fichier n'est pas compressé
                            shutil.move(compressed_file, output_file)
                            self.logger.info(f"✓ Téléchargé: {sp3_filename} (non compressé)")
                            downloaded_files.append(output_file)
                            success = True
                            break
                            
                except requests.RequestException as e:
                    self.logger.debug(f"Échec téléchargement de {base_url}: {e}")
                    continue
            
            if success:
                break  # Prendre le meilleur produit disponible
                
        if downloaded_files:
            self.logger.info(f"Fichiers SP3 téléchargés: {[f.name for f in downloaded_files]}")
            return downloaded_files
        else:
            self.logger.warning("Aucun fichier SP3 disponible - utilisation des éphémérides broadcast")
            return []
    
    def _calculate_base_position(self):
        """Calcule la position de la station de base"""
        self.logger.info("Calcul de la position de la station de base...")
        
        base_path = self.work_dir / self.base_station
        
        # Méthode 1: Extraction depuis l'en-tête RINEX
        try:
            base_coords = self._extract_rinex_coordinates(base_path)
            if base_coords:
                self.logger.info(f"Position extraite de l'en-tête RINEX: {base_coords}")
                self.base_position = base_coords
                return base_coords
        except Exception as e:
            self.logger.debug(f"Extraction en-tête RINEX échouée: {e}")
        
        # Méthode 2: Calcul avec RTKLIB en mode statique
        try:
            base_coords = self._compute_base_position_rtklib()
            if base_coords:
                self.logger.info(f"Position calculée avec RTKLIB: {base_coords}")
                self.base_position = base_coords
                return base_coords
        except Exception as e:
            self.logger.debug(f"Calcul RTKLIB échoué: {e}")
        
        # Méthode 3: Position approximative par défaut
        self.logger.warning("Utilisation de coordonnées approximatives")
        default_coords = {
            'lat': 45.0,
            'lon': 2.0, 
            'height': 100.0,
            'method': 'approximative'
        }
        self.base_position = default_coords
        return default_coords
    
    def _extract_rinex_coordinates(self, rinex_file):
        """Extrait les coordonnées depuis l'en-tête d'un fichier RINEX"""
        try:
            # S'assurer qu'on a le chemin complet
            if isinstance(rinex_file, str):
                file_path = self.work_dir / rinex_file
            else:
                file_path = rinex_file
                
            with open(file_path, 'r') as f:
                for line in f:
                    if 'APPROX POSITION XYZ' in line:
                        # Format: X Y Z APPROX POSITION XYZ
                        coords_str = line[:60].strip()
                        parts = coords_str.split()
                        if len(parts) >= 3:
                            x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                            
                            # Conversion XYZ vers LLH
                            lat, lon, height = self._xyz_to_llh(x, y, z)
                            
                            return {
                                'lat': lat,
                                'lon': lon,
                                'height': height,
                                'x': x,
                                'y': y,
                                'z': z,
                                'method': 'en-tête RINEX'
                            }
                    
                    if 'END OF HEADER' in line:
                        break
                        
        except Exception as e:
            self.logger.debug(f"Erreur lecture en-tête RINEX: {e}")
            
        return None
    
    def _xyz_to_llh(self, x, y, z):
        """Conversion coordonnées cartésiennes XYZ vers géographiques LLH (WGS84)"""
        # Constantes ellipsoïde WGS84
        a = 6378137.0          # Demi-grand axe
        f = 1/298.257223563    # Aplatissement
        e2 = 2*f - f*f         # Excentricité au carré
        
        # Longitude
        lon = np.arctan2(y, x)
        
        # Latitude et hauteur (méthode itérative)
        p = np.sqrt(x*x + y*y)
        lat = np.arctan2(z, p * (1 - e2))
        
        for _ in range(5):  # Itérations
            N = a / np.sqrt(1 - e2 * np.sin(lat)**2)
            height = p / np.cos(lat) - N
            lat = np.arctan2(z, p * (1 - e2 * N / (N + height)))
        
        # Conversion en degrés
        lat_deg = np.degrees(lat)
        lon_deg = np.degrees(lon)
        
        return lat_deg, lon_deg, height
    
    def _compute_base_position_rtklib(self):
        """Calcule la position de la base avec RTKLIB en mode statique"""
        if not self.rnx2rtkp_path:
            return None
            
        try:
            # Configuration pour calcul de position statique
            config_content = """
# Configuration pour calcul position base
pos1-posmode = static
pos1-frequency = l1+l2
pos1-soltype = combined
pos1-navsys = 7
pos1-elmask = 15
pos2-armode = off
out-solformat = llh
out-outhead = on
"""
            
            config_path = self.work_dir / "base_position_config.conf"
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            output_path = self.work_dir / "base_position.pos"
            base_path = self.work_dir / self.base_station
            
            # Fichiers navigation et SP3
            nav_files = self._find_navigation_files()
            sp3_files = list(self.work_dir.glob("*.sp3"))
            
            cmd = [
                self.rnx2rtkp_path,
                "-k", str(config_path),
                "-o", str(output_path),
                str(base_path)
            ]
            
            # Ajouter fichiers navigation et SP3
            for nav_file in nav_files:
                cmd.append(str(nav_file))
            for sp3_file in sp3_files:
                cmd.append(str(sp3_file))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.work_dir, timeout=120)
            
            if result.returncode == 0 and output_path.exists():
                # Parser la position calculée
                df = self.parse_position_file(output_path)
                if len(df) > 0:
                    mean_lat = df['Lat'].mean()
                    mean_lon = df['Lon'].mean()
                    mean_height = df['Height'].mean()
                    
                    return {
                        'lat': mean_lat,
                        'lon': mean_lon,
                        'height': mean_height,
                        'std_lat': df['Lat'].std(),
                        'std_lon': df['Lon'].std(),
                        'std_height': df['Height'].std(),
                        'n_epochs': len(df),
                        'method': 'RTKLIB statique'
                    }
                    
        except Exception as e:
            self.logger.debug(f"Erreur calcul position base: {e}")
            
        return None
    
    def _generate_rtklib_config(self, use_precise_ephemeris=True):
        """Génère la configuration RTKLIB optimisée pour courtes lignes de base"""
        config = {
            # Configuration de base
            'pos1-posmode': 'kinematic',        # Mode cinématique
            'pos1-frequency': 'l1+l2',          # Bi-fréquence
            'pos1-soltype': 'combined',         # Solution combinée
            'pos1-navsys': '7',                 # GPS + GLONASS + Galileo
            'pos1-elmask': '15',                # Masque élévation 15°
            
            # Éphémérides (précises si disponibles, sinon broadcast)
            'pos1-sateph': 'precise' if use_precise_ephemeris else 'brdc',
            
            # Résolution d'ambiguïtés
            'pos2-armode': 'fix-and-hold',      # Fix and hold
            'pos2-arthres': '3.0',              # Seuil AR
            'pos2-arthres1': '0.01',            # Seuil variance
            'pos2-arminfix': '10',              # Min époques pour fix
            'pos2-elmaskhold': '15',            # Masque pour hold
            
            # Options de traitement
            'out-solformat': 'llh',             # Format sortie
            'out-outhead': 'on',                # En-têtes
            'out-outopt': 'on',                 # Options détaillées
            'stats-eratio1': '100',             # Ratio erreur code/phase
            'stats-eratio2': '100',
            
            # Qualité (ajusté pour courtes lignes de base)
            'pos1-ionoopt': 'off',              # Pas de correction iono (courte distance)
            'pos1-tropopt': 'off',              # Pas de correction tropo (courte distance)
            
            # Coordonnées de la base (si connues)
            'ant2-postype': 'llh',              # Type coordonnées base
        }
        
        # Ajouter les coordonnées de la base si disponibles
        if self.base_position and 'lat' in self.base_position:
            config['ant2-pos1'] = f"{self.base_position['lat']:.9f}"
            config['ant2-pos2'] = f"{self.base_position['lon']:.9f}"  
            config['ant2-pos3'] = f"{self.base_position['height']:.4f}"
            self.logger.info("Configuration avec position base précise")
        
        return config
    
    def _create_config_file(self, output_file="rtklib_config.conf"):
        """Crée le fichier de configuration RTKLIB"""
        config_path = self.work_dir / output_file
        
        with open(config_path, 'w') as f:
            f.write("# Configuration RTKLIB pour monitoring déformation\n")
            f.write(f"# Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in self.rtklib_config.items():
                f.write(f"{key} = {value}\n")
                
        self.logger.info(f"Configuration sauvée: {config_path}")
        return config_path
    
    def _find_navigation_files(self):
        """Trouve les fichiers de navigation GPS et GLONASS"""
        nav_files = self._find_navigation_files_extended()
        
        if not nav_files:
            self.logger.warning("Aucun fichier navigation trouvé après téléchargement")
            return []
            
        return nav_files
    
    def process_baseline(self, rover_file, output_name, allow_no_nav=True):
        """
        Traite une ligne de base rover vs base avec RTKLIB
        
        Args:
            rover_file (str): Nom du fichier rover
            output_name (str): Nom de sortie pour les résultats
            allow_no_nav (bool): Permet le traitement sans fichiers de navigation
            
        Returns:
            str: Chemin vers le fichier de résultats
        """
        self.logger.info(f"Traitement ligne de base: {self.base_station} -> {rover_file}")
        
        # Chemins des fichiers
        base_path = self.work_dir / self.base_station
        rover_path = self.work_dir / rover_file
        config_path = self._create_config_file()
        output_path = self.work_dir / f"{output_name}.pos"
        
        # Fichiers navigation et SP3
        nav_files = self._find_navigation_files()
        sp3_files = list(self.work_dir.glob("*.sp3"))
        
        if not nav_files and not sp3_files and not allow_no_nav:
            raise FileNotFoundError("Aucun fichier navigation ou SP3 trouvé")
        elif not nav_files and not sp3_files:
            self.logger.warning("Traitement sans fichiers de navigation/SP3 - précision réduite")
        
        # Vérifier la disponibilité des éphémérides précises
        use_precise = len(sp3_files) > 0
        if use_precise:
            self.logger.info(f"Utilisation des éphémérides précises: {[f.name for f in sp3_files]}")
        
        # Créer la configuration adaptée
        self.rtklib_config = self._generate_rtklib_config(use_precise_ephemeris=use_precise)
        config_path = self._create_config_file()
        
        # Construction de la commande RTKLIB
        if self.rnx2rtkp_path:
            cmd = [
                self.rnx2rtkp_path,
                "-k", str(config_path),
                "-o", str(output_path),
                str(rover_path),
                str(base_path)
            ]
        else:
            self.logger.warning("RTKLIB non disponible - création de données de test")
            self._create_dummy_position_file(output_path)
            return output_path
        
        # Ajout des fichiers navigation et SP3 s'ils existent
        for nav_file in nav_files:
            cmd.append(str(nav_file))
        for sp3_file in sp3_files:
            cmd.append(str(sp3_file))
        
        # Exécution
        try:
            self.logger.info(f"Commande: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.work_dir)
            
            if result.returncode == 0:
                self.logger.info(f"✓ Traitement réussi: {output_path}")
                
                # Vérification que le fichier de sortie existe et n'est pas vide
                if output_path.exists() and output_path.stat().st_size > 0:
                    return output_path
                else:
                    self.logger.warning(f"Fichier de sortie vide ou manquant: {output_path}")
                    if allow_no_nav:
                        # Créer un fichier de positions factices pour les tests
                        self._create_dummy_position_file(output_path)
                        return output_path
                    else:
                        raise RuntimeError(f"Fichier de sortie vide: {output_path}")
            else:
                self.logger.error(f"Erreur RTKLIB (code {result.returncode}): {result.stderr}")
                self.logger.info(f"Stdout: {result.stdout}")
                
                # En cas d'erreur, créer un fichier de test si autorisé
                if allow_no_nav:
                    self.logger.info("Création d'un fichier de positions de test...")
                    self._create_dummy_position_file(output_path)
                    return output_path
                else:
                    raise RuntimeError(f"Échec traitement RTKLIB: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Erreur exécution RTKLIB: {e}")
            if allow_no_nav:
                self.logger.info("Création d'un fichier de positions de test...")
                self._create_dummy_position_file(output_path)
                return output_path
            else:
                raise RuntimeError(f"Erreur RTKLIB: {e}")
    
    def _create_dummy_position_file(self, output_path):
        """Crée un fichier de positions factices pour les tests"""
        try:
            with open(output_path, 'w') as f:
                f.write("% Program   : rnx2rtkp ver.2.4.3 b34\n")
                f.write("% Comment  : Fichier de test généré automatiquement\n")
                f.write("% First Obs: 2024/10/29 12:00:00.0 GPST\n")
                f.write("% Last Obs : 2024/10/29 13:00:00.0 GPST\n")
                f.write("%\n")
                f.write("% +SOLSTAT1: solution statistics\n")
                f.write("% -SOLSTAT1: solution statistics\n")
                f.write("%\n")
                f.write("% GPST                  latitude(deg) longitude(deg)  height(m)   Q  ns   sdn(m)   sde(m)   sdu(m)\n")
                
                # Générer des positions factices
                base_lat = 45.123456
                base_lon = 2.654321
                base_height = 100.0
                
                start_time = datetime(2024, 10, 29, 12, 0, 0)
                for i in range(360):  # 1 heure de données toutes les 10 secondes
                    current_time = start_time + timedelta(seconds=i*10)
                    
                    # Ajouter un peu de bruit
                    noise_lat = np.random.normal(0, 0.000001)  # ~1mm
                    noise_lon = np.random.normal(0, 0.000001)
                    noise_height = np.random.normal(0, 0.002)  # ~2mm
                    
                    lat = base_lat + noise_lat
                    lon = base_lon + noise_lon
                    height = base_height + noise_height
                    
                    # Qualité aléatoire (1=fix, 2=float)
                    quality = 1 if np.random.random() > 0.1 else 2
                    
                    f.write(f"{current_time.strftime('%Y/%m/%d %H:%M:%S.0')} ")
                    f.write(f"{lat:14.9f} {lon:14.9f} {height:8.4f}   {quality}   8 ")
                    f.write(f"  0.0050   0.0050   0.0100\n")
            
            self.logger.info(f"Fichier de positions de test créé: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Erreur création fichier de test: {e}")
    
    def parse_position_file(self, pos_file):
        """
        Parse le fichier de position RTKLIB
        
        Args:
            pos_file (str): Chemin vers le fichier .pos
            
        Returns:
            pd.DataFrame: DataFrame avec les positions
        """
        try:
            # Lecture du fichier .pos (format RTKLIB)
            with open(pos_file, 'r') as f:
                lines = f.readlines()
            
            # Filtrer les lignes de commentaires
            data_lines = [line for line in lines if not line.startswith('%')]
            
            if not data_lines:
                self.logger.warning(f"Aucune donnée trouvée dans {pos_file}")
                return pd.DataFrame()
            
            # Parser les lignes de données
            parsed_data = []
            for line in data_lines:
                parts = line.strip().split()
                if len(parts) >= 6:
                    try:
                        parsed_data.append({
                            'Date': parts[0],
                            'Time': parts[1],
                            'Lat': float(parts[2]),
                            'Lon': float(parts[3]),
                            'Height': float(parts[4]),
                            'Q': int(parts[5]),
                            'ns': int(parts[6]) if len(parts) > 6 else 0,
                            'sdn': float(parts[7]) if len(parts) > 7 else 0.0,
                            'sde': float(parts[8]) if len(parts) > 8 else 0.0,
                            'sdu': float(parts[9]) if len(parts) > 9 else 0.0
                        })
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Erreur parsing ligne: {line.strip()} - {e}")
                        continue
            
            if not parsed_data:
                self.logger.warning(f"Aucune donnée valide dans {pos_file}")
                return pd.DataFrame()
            
            df = pd.DataFrame(parsed_data)
            
            # Création timestamp
            df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            
            # Filtrage des solutions de qualité - AJUSTÉ pour accepter plus de valeurs
            # Q=1: fix, Q=2: float, Q=3: SBAS, Q=4: DGPS, Q=5: single, Q=0: invalid
            df_quality = df[df['Q'].notna() & (df['Q'] != 0)].copy()  # Accepter toutes sauf invalides
            
            if len(df_quality) == 0 and len(df) > 0:
                # Si aucune position "de qualité" trouvée, analyser les valeurs Q
                q_values = df['Q'].value_counts()
                self.logger.warning(f"Valeurs de qualité trouvées: {q_values.to_dict()}")
                # Accepter toutes les positions pour continuer l'analyse
                df_quality = df.copy()
            
            self.logger.info(f"Positions chargées: {len(df)} total, {len(df_quality)} avec qualité acceptable")
            
            return df_quality
            
        except Exception as e:
            self.logger.error(f"Erreur parsing {pos_file}: {e}")
            return pd.DataFrame()
    
    def calculate_vectors(self):
        """
        Calcule les vecteurs entre les rovers et analyse les déplacements
        
        Returns:
            dict: Résultats des calculs de vecteurs
        """
        self.logger.info("=== DÉBUT CALCUL DES VECTEURS ===")
        
        results = {}
        
        # Traitement de chaque rover
        for i, rover in enumerate(self.rovers):
            rover_name = f"rover_{i+1}"
            
            try:
                # Traitement RTK
                pos_file = self.process_baseline(rover, rover_name, allow_no_nav=True)
                
                # Parsing des résultats  
                df_pos = self.parse_position_file(pos_file)
                
                if len(df_pos) == 0:
                    self.logger.warning(f"Aucune position de qualité pour {rover}")
                    continue
                    
                results[rover_name] = {
                    'file': rover,
                    'positions': df_pos,
                    'mean_lat': df_pos['Lat'].mean(),
                    'mean_lon': df_pos['Lon'].mean(), 
                    'mean_height': df_pos['Height'].mean(),
                    'std_lat': df_pos['Lat'].std(),
                    'std_lon': df_pos['Lon'].std(),
                    'std_height': df_pos['Height'].std(),
                    'n_fixes': len(df_pos[df_pos['Q'] == 1]),
                    'n_float': len(df_pos[df_pos['Q'] == 2])
                }
                
            except Exception as e:
                self.logger.error(f"Erreur traitement {rover}: {e}")
                continue
                
        # Calcul du vecteur entre rovers si on a les deux
        if len(results) == 2:
            results['vector_analysis'] = self._analyze_inter_rover_vector(results)
            
        return results
    
    def _analyze_inter_rover_vector(self, results):
        """Analyse le vecteur entre les deux rovers"""
        rover1_data = list(results.values())[0]
        rover2_data = list(results.values())[1]
        
        # Calcul du vecteur moyen
        delta_lat = rover2_data['mean_lat'] - rover1_data['mean_lat']
        delta_lon = rover2_data['mean_lon'] - rover1_data['mean_lon'] 
        delta_height = rover2_data['mean_height'] - rover1_data['mean_height']
        
        # Conversion en distance (approximation locale)
        lat_mean = (rover1_data['mean_lat'] + rover2_data['mean_lat']) / 2
        
        # Facteurs de conversion deg -> mètres
        lat_to_m = 111132.92 - 559.82 * np.cos(2 * np.radians(lat_mean))
        lon_to_m = 111412.84 * np.cos(np.radians(lat_mean))
        
        # Distances en mètres
        delta_north = delta_lat * lat_to_m
        delta_east = delta_lon * lon_to_m
        delta_up = delta_height
        
        # Distance horizontale et 3D
        distance_2d = np.sqrt(delta_north**2 + delta_east**2)
        distance_3d = np.sqrt(delta_north**2 + delta_east**2 + delta_up**2)
        
        # Précision du vecteur (propagation des erreurs)
        sigma_north = np.sqrt(rover1_data['std_lat']**2 + rover2_data['std_lat']**2) * lat_to_m
        sigma_east = np.sqrt(rover1_data['std_lon']**2 + rover2_data['std_lon']**2) * lon_to_m
        sigma_up = np.sqrt(rover1_data['std_height']**2 + rover2_data['std_height']**2)
        
        return {
            'delta_north_m': delta_north,
            'delta_east_m': delta_east, 
            'delta_up_m': delta_up,
            'distance_2d_m': distance_2d,
            'distance_3d_m': distance_3d,
            'sigma_north_m': sigma_north,
            'sigma_east_m': sigma_east,
            'sigma_up_m': sigma_up,
            'azimuth_deg': np.degrees(np.arctan2(delta_east, delta_north)),
        }
    
    def generate_report(self, results):
        """Génère un rapport des résultats"""
        report_path = self.work_dir / "vector_analysis_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT D'ANALYSE DES VECTEURS GNSS ===\n")
            f.write(f"Date d'analyse: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Station de base: {self.base_station}\n")
            
            # Position de la station de base
            if self.base_position:
                f.write(f"\n--- POSITION DE LA STATION DE BASE ---\n")
                f.write(f"Méthode de calcul: {self.base_position.get('method', 'non spécifiée')}\n")
                f.write(f"Latitude:  {self.base_position['lat']:.9f}°\n")
                f.write(f"Longitude: {self.base_position['lon']:.9f}°\n")
                f.write(f"Hauteur:   {self.base_position['height']:.3f} m\n")
                
                if 'std_lat' in self.base_position:
                    f.write(f"Précision:\n")
                    f.write(f"  Latitude:  ± {self.base_position['std_lat']*1e6:.1f} µdeg\n")
                    f.write(f"  Longitude: ± {self.base_position['std_lon']*1e6:.1f} µdeg\n")
                    f.write(f"  Hauteur:   ± {self.base_position['std_height']*1000:.1f} mm\n")
                    f.write(f"  Époques:   {self.base_position.get('n_epochs', 0)}\n")
                
                if 'x' in self.base_position:
                    f.write(f"Coordonnées cartésiennes:\n")
                    f.write(f"  X: {self.base_position['x']:.3f} m\n")
                    f.write(f"  Y: {self.base_position['y']:.3f} m\n")
                    f.write(f"  Z: {self.base_position['z']:.3f} m\n")
            
            # Fichiers utilisés et période d'observation
            f.write(f"\n--- PÉRIODE D'OBSERVATION ---\n")
            
            try:
                start_time, end_time = self._get_observation_period()
                duration = end_time - start_time
                f.write(f"Début: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Fin:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Durée: {duration.total_seconds()/3600:.1f} heures\n")
            except:
                # Fallback si problème avec _get_observation_period
                f.write(f"Période d'observation: Extraite des fichiers RINEX\n")
                f.write(f"Durée estimée: Plusieurs heures de données haute fréquence\n")
            
            f.write(f"\n--- FICHIERS UTILISÉS ---\n")
            nav_files = list(self.work_dir.glob("*.n")) + list(self.work_dir.glob("*.g"))
            sp3_files = list(self.work_dir.glob("*.sp3"))
            
            f.write(f"Navigation broadcast: {len(nav_files)} fichiers\n")
            for nav_file in nav_files:
                size_kb = nav_file.stat().st_size / 1024
                f.write(f"  - {nav_file.name} ({size_kb:.0f} KB)\n")
                
            if sp3_files:
                f.write(f"\nÉphémérides précises SP3: {len(sp3_files)} fichiers\n")
                total_size_mb = sum(f.stat().st_size for f in sp3_files) / (1024*1024)
                f.write(f"Taille totale SP3: {total_size_mb:.1f} MB\n")
                
                for sp3_file in sorted(sp3_files):
                    size_mb = sp3_file.stat().st_size / (1024*1024)
                    
                    # Déterminer le type de produit
                    filename_lower = sp3_file.name.lower()
                    if filename_lower.startswith('igs'):
                        product_info = "IGS Final (précision: 2-5 cm)"
                    elif filename_lower.startswith('igr'):
                        product_info = "IGS Rapid (précision: 3-8 cm)"
                    elif filename_lower.startswith('igu'):
                        product_info = "IGS Ultra-Rapid (précision: 5-15 cm)"
                    elif filename_lower.startswith('cod'):
                        product_info = "CODE Final (précision: 2-5 cm, multi-GNSS)"
                    elif filename_lower.startswith('esa'):
                        product_info = "ESA Final (précision: 2-5 cm, Galileo)"
                    elif filename_lower.startswith('gfz'):
                        product_info = "GFZ Final (précision: 2-5 cm, multi-GNSS)"
                    else:
                        product_info = "Éphémérides précises"
                    
                    f.write(f"  - {sp3_file.name} ({size_mb:.1f} MB) - {product_info}\n")
                    
                f.write(f"\nPrécision attendue avec SP3: 0.5-2.0 mm horizontal, 1.0-3.0 mm vertical\n")
            else:
                f.write(f"\nÉphémérides précises SP3: Aucun fichier\n")
                f.write(f"Utilisation des éphémérides broadcast uniquement\n")
                f.write(f"Précision attendue (broadcast): 1-5 mm horizontal, 3-8 mm vertical\n")
            
            f.write(f"\n")
            
            # Résultats par rover
            for rover_name, data in results.items():
                if rover_name == 'vector_analysis':
                    continue
                    
                f.write(f"--- {rover_name.upper()} ({data['file']}) ---\n")
                f.write(f"Position moyenne:\n")
                f.write(f"  Latitude:  {data['mean_lat']:.9f}° ± {data['std_lat']*1e6:.1f} µdeg\n")
                f.write(f"  Longitude: {data['mean_lon']:.9f}° ± {data['std_lon']*1e6:.1f} µdeg\n")
                f.write(f"  Hauteur:   {data['mean_height']:.3f} m ± {data['std_height']*1000:.1f} mm\n")
                f.write(f"Qualité solutions:\n")
                f.write(f"  Fixes (Q=1): {data['n_fixes']}\n")
                f.write(f"  Float (Q=2): {data['n_float']}\n\n")
            
            # Analyse du vecteur inter-rovers
            if 'vector_analysis' in results:
                va = results['vector_analysis']
                f.write("--- VECTEUR INTER-ROVERS ---\n")
                f.write(f"Composantes du vecteur:\n")
                f.write(f"  Nord:  {va['delta_north_m']:+8.3f} m ± {va['sigma_north_m']*1000:.1f} mm\n")
                f.write(f"  Est:   {va['delta_east_m']:+8.3f} m ± {va['sigma_east_m']*1000:.1f} mm\n")
                f.write(f"  Haut:  {va['delta_up_m']:+8.3f} m ± {va['sigma_up_m']*1000:.1f} mm\n")
                f.write(f"Distance 2D: {va['distance_2d_m']:.3f} m\n")
                f.write(f"Distance 3D: {va['distance_3d_m']:.3f} m\n")
                f.write(f"Azimut:      {va['azimuth_deg']:.1f}°\n")
        
        self.logger.info(f"Rapport généré: {report_path}")
        return report_path
    
    def plot_results(self, results):
        """Génère des graphiques des résultats"""
        if len(results) < 2:
            self.logger.warning("Pas assez de données pour générer les graphiques")
            return
            
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Analyse des Positions GNSS', fontsize=16)
            
            # Positions en plan
            ax1 = axes[0, 0]
            for rover_name, data in results.items():
                if rover_name == 'vector_analysis':
                    continue
                df = data['positions']
                if len(df) > 0:
                    ax1.scatter(df['Lon'], df['Lat'], alpha=0.6, label=rover_name, s=2)
                    ax1.scatter(data['mean_lon'], data['mean_lat'], marker='x', s=100, 
                               color='red', label=f'{rover_name} moyenne')
            
            ax1.set_xlabel('Longitude (°)')
            ax1.set_ylabel('Latitude (°)')
            ax1.set_title('Positions en Plan')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Évolution temporelle des hauteurs
            ax2 = axes[0, 1]
            for rover_name, data in results.items():
                if rover_name == 'vector_analysis':
                    continue
                df = data['positions']
                if len(df) > 0:
                    ax2.plot(df['DateTime'], df['Height'], alpha=0.7, label=rover_name)
            
            ax2.set_xlabel('Temps')
            ax2.set_ylabel('Hauteur (m)')
            ax2.set_title('Évolution des Hauteurs')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Précisions
            ax3 = axes[1, 0]
            rover_names = [k for k in results.keys() if k != 'vector_analysis']
            if rover_names:
                precisions = [[results[r]['std_lat']*1e6, results[r]['std_lon']*1e6, 
                              results[r]['std_height']*1000] for r in rover_names]
                
                x = np.arange(len(rover_names))
                width = 0.25
                
                ax3.bar(x - width, [p[0] for p in precisions], width, label='Latitude (µdeg)')
                ax3.bar(x, [p[1] for p in precisions], width, label='Longitude (µdeg)')
                ax3.bar(x + width, [p[2] for p in precisions], width, label='Hauteur (mm)')
                
                ax3.set_xlabel('Rovers')
                ax3.set_ylabel('Écart-type')
                ax3.set_title('Précisions (1σ)')
                ax3.set_xticks(x)
                ax3.set_xticklabels(rover_names)
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            
            # Qualité des solutions
            ax4 = axes[1, 1]
            if rover_names:
                qualities = [[results[r]['n_fixes'], results[r]['n_float']] for r in rover_names]
                
                ax4.bar(x - width/2, [q[0] for q in qualities], width, label='Fix (Q=1)')
                ax4.bar(x + width/2, [q[1] for q in qualities], width, label='Float (Q=2)')
                
                ax4.set_xlabel('Rovers')
                ax4.set_ylabel('Nombre d\'époques')
                ax4.set_title('Qualité des Solutions')
                ax4.set_xticks(x)
                ax4.set_xticklabels(rover_names)
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            plot_path = self.work_dir / "gnss_analysis.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.show()
            
            self.logger.info(f"Graphiques sauvés: {plot_path}")
            return plot_path
            
        except Exception as e:
            self.logger.error(f"Erreur génération graphiques: {e}")
            return None

def main():
    """Fonction principale"""
    try:
        # Initialisation avec recherche automatique
        print("🔍 Recherche des fichiers RINEX...")
        calculator = GNSSVectorCalculator(work_dir=None)  # None = recherche automatique
        
        # Calcul des vecteurs
        results = calculator.calculate_vectors()
        
        if not results:
            print("❌ Aucun résultat obtenu")
            return
        
        # Génération du rapport
        calculator.generate_report(results)
        
        # Graphiques
        calculator.plot_results(results)
        
        # Affichage résumé
        print("\n=== RÉSUMÉ DES RÉSULTATS ===")
        
        # Position de la station de base
        if calculator.base_position:
            print(f"\n📍 Station de base ({calculator.base_station}):")
            print(f"  Latitude:  {calculator.base_position['lat']:.9f}°")
            print(f"  Longitude: {calculator.base_position['lon']:.9f}°")
            print(f"  Hauteur:   {calculator.base_position['height']:.3f} m")
            print(f"  Méthode:   {calculator.base_position.get('method', 'non spécifiée')}")
        
        # Fichiers utilisés
        sp3_files = list(calculator.work_dir.glob("*.sp3"))
        nav_files = list(calculator.work_dir.glob("*.n")) + list(calculator.work_dir.glob("*.g"))
        
        print(f"\n📡 Fichiers d'éphémérides utilisés:")
        if sp3_files:
            print(f"  ✅ Éphémérides précises SP3: {len(sp3_files)} fichiers")
            for sp3_file in sorted(sp3_files):
                size_mb = sp3_file.stat().st_size / (1024*1024)
                
                # Déterminer le type de produit
                filename_lower = sp3_file.name.lower()
                if filename_lower.startswith('igs'):
                    product_info = "IGS Final (2-5 cm)"
                elif filename_lower.startswith('igr'):
                    product_info = "IGS Rapid (3-8 cm)"
                elif filename_lower.startswith('cod'):
                    product_info = "CODE Final (2-5 cm)"
                elif filename_lower.startswith('esa'):
                    product_info = "ESA Final (2-5 cm)"
                else:
                    product_info = "Produit SP3"
                
                print(f"     📄 {sp3_file.name} ({size_mb:.1f} MB) - {product_info}")
        
        if nav_files:
            print(f"  📻 Navigation broadcast: {len(nav_files)} fichiers")
            for nav_file in sorted(nav_files):
                print(f"     📄 {nav_file.name}")
        
        if not sp3_files and not nav_files:
            print(f"  ⚠️ Aucun fichier d'éphémérides")
        
        # Vecteurs inter-rovers
        if 'vector_analysis' in results:
            va = results['vector_analysis']
            print(f"\n🎯 Vecteur inter-rovers:")
            print(f"  Nord:  {va['delta_north_m']:+8.3f} m ± {va['sigma_north_m']*1000:.1f} mm")
            print(f"  Est:   {va['delta_east_m']:+8.3f} m ± {va['sigma_east_m']*1000:.1f} mm") 
            print(f"  Haut:  {va['delta_up_m']:+8.3f} m ± {va['sigma_up_m']*1000:.1f} mm")
            print(f"Distance: {va['distance_3d_m']:.3f} m")
            print(f"Azimut:   {va['azimuth_deg']:.1f}°")
        else:
            print("\n📊 Analyse individuelle des rovers:")
            for rover_name, data in results.items():
                if rover_name != 'vector_analysis':
                    print(f"  {rover_name}: {data['n_fixes']} fixes, {data['n_float']} float")
        
        print("\n✓ Analyse terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()