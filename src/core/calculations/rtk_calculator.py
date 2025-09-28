"""
Calculateur RTKLIB pour traitement GNSS - VERSION CORRIGÉE
Basé sur test_RTKbat.py avec adaptation pour l'interface
"""

import os
import sys
import subprocess
import re
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class RTKConfig:
    """Configuration RTKLIB centralisée"""
    
    def __init__(self):
        # Chemins par défaut
        self.working_dir = Path(__file__).parent.parent.parent.parent / "RTKlib"
        self.exe_path = self.working_dir / "rnx2rtkp.exe"
        self.conf_file = self.working_dir / "configs" / "conf.conf"
        
        # Fichiers d'entrée (seront définis dynamiquement)
        self.rover_obs_file = None
        self.base_obs_file = None
        self.rover_nav_file = None
        self.base_nav_file = None
        self.rover_gnav_file = None
        self.base_gnav_file = None
        self.precise_eph_file = None
        self.precise_clk_file = None
        
        # Fichier de sortie
        self.output_file = None
        
        # Options
        self.use_sp3_clk = False
        self.fixed_point = "Port"  # Port, Bow, Stbd


class RTKCalculator(QThread):
    """
    Thread pour exécuter RTKLIB et surveiller la progression
    """
    
    # Signaux
    progress_updated = pyqtSignal(str, int)  # message, pourcentage
    quality_updated = pyqtSignal(dict)       # données qualité
    process_finished = pyqtSignal(int)       # code de retour
    log_message = pyqtSignal(str)            # message de log
    
    def __init__(self, config: RTKConfig):
        super().__init__()
        self.config = config
        self.total_epochs = 0
        self.processed_epochs = 0
        self.quality_counts = {str(k): 0 for k in range(7)}
        self.is_running = False
        
    def _estimate_total_epochs(self, obs_file: Path) -> int:
        """Estime le nombre d'époques dans le fichier RINEX"""
        try:
            if not obs_file.exists():
                return 3600
                
            epoch_regex = re.compile(
                r'(^\s*>\s*\d{4}|^\s*\d{2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+\d{1,2}\s+[\d.]+\s+\d)'
            )
            
            with open(obs_file, 'r', errors='ignore') as f:
                line_count = sum(1 for line in f if epoch_regex.match(line))
                return max(line_count, 1)
                
        except Exception as e:
            self.log_message.emit(f"Erreur estimation époques: {e}")
            return 3600
    
    def _build_command(self) -> List[str]:
        """Construit la commande RTKLIB avec détection automatique des fichiers"""
        self.log_message.emit("🔍 Construction de la commande RTKLIB...")
        
        cmd = [
            str(self.config.exe_path),
            "-k", str(self.config.conf_file),
            "-o", str(self.config.output_file)
        ]
        
        # 1. Fichiers OBS (Rover et Base)
        rover_obs_path = Path(self.config.rover_obs_file) if isinstance(self.config.rover_obs_file, str) else self.config.rover_obs_file
        base_obs_path = Path(self.config.base_obs_file) if isinstance(self.config.base_obs_file, str) else self.config.base_obs_file
        
        self.log_message.emit(f"📄 Rover OBS: {rover_obs_path.name}")
        self.log_message.emit(f"📄 Base OBS: {base_obs_path.name}")
        
        cmd.extend([
            str(rover_obs_path.absolute()),
            str(base_obs_path.absolute())
        ])
        
        # 2. Fichier NAV du rover
        if self.config.rover_nav_file:
            rover_nav_path = Path(self.config.rover_nav_file) if isinstance(self.config.rover_nav_file, str) else self.config.rover_nav_file
            if rover_nav_path.exists():
                self.log_message.emit(f"📄 Rover NAV: {rover_nav_path.name}")
                cmd.append(str(rover_nav_path.absolute()))
            else:
                self.log_message.emit(f"⚠️ Fichier NAV rover introuvable: {rover_nav_path.name}")
        
        # 3. Fichiers SP3/CLK (détection automatique dans le même dossier)
        if self.config.use_sp3_clk:
            self._add_precise_files(cmd, rover_obs_path.parent)
        
        # 4. Fichier GNAV du rover
        if self.config.rover_gnav_file:
            rover_gnav_path = Path(self.config.rover_gnav_file) if isinstance(self.config.rover_gnav_file, str) else self.config.rover_gnav_file
            if rover_gnav_path.exists():
                self.log_message.emit(f"📄 Rover GNAV: {rover_gnav_path.name}")
                cmd.append(str(rover_gnav_path.absolute()))
            else:
                self.log_message.emit(f"⚠️ Fichier GNAV rover introuvable: {rover_gnav_path.name}")
        
        self.log_message.emit(f"✅ Commande RTKLIB construite avec {len(cmd)-4} fichiers d'entrée")
        return cmd
    
    def _add_precise_files(self, cmd: List[str], data_dir: Path):
        """Ajoute les fichiers SP3/CLK trouvés dans le dossier des données"""
        self.log_message.emit(f"🔍 Recherche des fichiers SP3/CLK dans: {data_dir}")
        
        # Recherche des fichiers SP3
        sp3_files = list(data_dir.glob("*.sp3")) + list(data_dir.glob("*.SP3"))
        if sp3_files:
            # Priorité: ULT > RAP
            ult_files = [f for f in sp3_files if "ULT" in f.name.upper()]
            rap_files = [f for f in sp3_files if "RAP" in f.name.upper()]
            
            if ult_files:
                sp3_file = ult_files[0]
                self.log_message.emit(f"📄 SP3 ULT: {sp3_file.name}")
            elif rap_files:
                sp3_file = rap_files[0]
                self.log_message.emit(f"📄 SP3 RAP: {sp3_file.name}")
            else:
                sp3_file = sp3_files[0]
                self.log_message.emit(f"📄 SP3: {sp3_file.name}")
            
            cmd.append(str(sp3_file.absolute()))
        else:
            self.log_message.emit("⚠️ Aucun fichier SP3 trouvé")
        
        # Recherche des fichiers CLK
        clk_files = list(data_dir.glob("*.clk")) + list(data_dir.glob("*.CLK"))
        if clk_files:
            # Priorité: FIN
            fin_files = [f for f in clk_files if "FIN" in f.name.upper()]
            
            if fin_files:
                clk_file = fin_files[0]
                self.log_message.emit(f"📄 CLK FIN: {clk_file.name}")
            else:
                clk_file = clk_files[0]
                self.log_message.emit(f"📄 CLK: {clk_file.name}")
            
            cmd.append(str(clk_file.absolute()))
        else:
            self.log_message.emit("⚠️ Aucun fichier CLK trouvé")
    
    def _validate_files(self) -> Tuple[bool, str]:
        """Valide que tous les fichiers requis existent et sont des fichiers RINEX"""
        required_files = [
            (self.config.exe_path, "rnx2rtkp.exe"),
            (self.config.conf_file, "conf.conf"),
            (self.config.rover_obs_file, "Fichier rover OBS"),
            (self.config.base_obs_file, "Fichier base OBS")
        ]
        
        for file_path, description in required_files:
            # Convertir en Path si c'est une chaîne
            if isinstance(file_path, str):
                file_path = Path(file_path)
            if not file_path or not file_path.exists():
                return False, f"{description} manquant: {file_path}"
        
        # Validation spécifique pour les fichiers RINEX
        rover_path = Path(self.config.rover_obs_file) if isinstance(self.config.rover_obs_file, str) else self.config.rover_obs_file
        base_path = Path(self.config.base_obs_file) if isinstance(self.config.base_obs_file, str) else self.config.base_obs_file
        
        if not self._is_rinex_file(rover_path):
            return False, f"Le fichier rover n'est pas un fichier RINEX valide: {rover_path}"
        
        if not self._is_rinex_file(base_path):
            return False, f"Le fichier base n'est pas un fichier RINEX valide: {base_path}"
        
        return True, "OK"
    
    def _is_rinex_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier est un fichier RINEX valide"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                # Un fichier RINEX commence par une version et un type
                # Ex: "     3.04           OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE"
                if 'RINEX VERSION' in first_line or 'OBSERVATION DATA' in first_line:
                    return True
                
                # Vérifier les premières lignes pour les en-têtes RINEX
                for i, line in enumerate(f):
                    if i > 20:  # Limiter la recherche aux 20 premières lignes
                        break
                    if any(keyword in line for keyword in ['END OF HEADER', 'MARKER NAME', 'OBSERVER / AGENCY']):
                        return True
                
                return False
        except Exception:
            return False
    
    def run(self):
        """Exécute le calcul RTKLIB"""
        self.is_running = True
        self._finished_emitted = False  # Garde pour éviter les émissions multiples
        
        # Validation
        is_valid, error_msg = self._validate_files()
        if not is_valid:
            self.log_message.emit(f"❌ {error_msg}")
            if not self._finished_emitted:
                self.process_finished.emit(-1)
                self._finished_emitted = True
            return
        
        # Estimation des époques
        rover_obs_path = Path(self.config.rover_obs_file) if isinstance(self.config.rover_obs_file, str) else self.config.rover_obs_file
        self.total_epochs = self._estimate_total_epochs(rover_obs_path)
        self.log_message.emit(f"📊 Époques estimées: {self.total_epochs}")
        
        # Construction de la commande
        command = self._build_command()
        self.log_message.emit(f"🚀 Commande complète:")
        self.log_message.emit(f"   {' '.join(command)}")
        
        # Nettoyage du fichier de sortie
        if self.config.output_file:
            output_path = Path(self.config.output_file) if isinstance(self.config.output_file, str) else self.config.output_file
            if output_path.exists():
                output_path.unlink()
        
        try:
            # Démarrage du processus
            self.progress_updated.emit("Démarrage RTKLIB...", 0)
            
            # Utiliser le répertoire du fichier de sortie comme répertoire de travail
            output_path = Path(self.config.output_file) if isinstance(self.config.output_file, str) else self.config.output_file
            output_dir = output_path.parent
            output_dir.mkdir(exist_ok=True)
            
            process = subprocess.Popen(
                command,
                cwd=str(self.config.working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )
            
            # Lecture de la sortie en temps réel avec optimisation
            import time
            last_progress_update = 0
            progress_update_interval = 0.5  # Mettre à jour la progression max toutes les 500ms
            
            for line in iter(process.stdout.readline, ''):
                if not self.is_running:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                # Debug : afficher seulement les lignes importantes (réduire le spam)
                if any(keyword in line.lower() for keyword in ["error", "warning"]):
                    self.log_message.emit(f"[RTKLIB] {line}")
                
                # Détection de la progression avec throttling
                if "processing" in line.lower():
                    self.processed_epochs += 1
                    current_time = time.time()
                    
                    # Mettre à jour la progression seulement si assez de temps s'est écoulé
                    if current_time - last_progress_update >= progress_update_interval:
                        message = "Traitement..."
                        
                        # Extraction de la qualité
                        quality_match = re.search(r'Q=(\d+)', line)
                        datetime_match = re.search(r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                        
                        if quality_match:
                            quality = quality_match.group(1)
                            if quality in self.quality_counts:
                                self.quality_counts[quality] += 1
                                # Mettre à jour le donut moins fréquemment
                                if self.processed_epochs % 10 == 0:  # Toutes les 10 époques
                                    self.quality_updated.emit(self.quality_counts.copy())
                            
                            if datetime_match:
                                datetime_str = datetime_match.group(1)
                                message = f"{datetime_str} Q={quality}"
                        
                        # Calcul du pourcentage (divisé par 2 car RTKLIB traite bidirectionnellement)
                        # RTKLIB traite ligne par ligne dans un sens puis revient en arrière
                        # donc la progression réelle est la moitié de ce qui est affiché
                        progress = min(
                            int((self.processed_epochs / (self.total_epochs * 2)) * 100), 
                            100
                        ) if self.total_epochs > 0 else 0
                        
                        self.progress_updated.emit(message, progress)
                        last_progress_update = current_time
            
            # Attente de la fin du processus
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.progress_updated.emit("✅ Traitement terminé", 100)
                self.log_message.emit("✅ Calcul RTKLIB terminé avec succès")
            else:
                self.log_message.emit(f"❌ Erreur RTKLIB (code: {return_code})")
            
            # Émettre le signal de fin seulement une fois
            if not self._finished_emitted:
                self.process_finished.emit(return_code)
                self._finished_emitted = True
            
        except FileNotFoundError:
            self.log_message.emit(f"❌ Exécutable introuvable: {self.config.exe_path}")
            if not self._finished_emitted:
                self.process_finished.emit(-1)
                self._finished_emitted = True
        except Exception as e:
            self.log_message.emit(f"❌ Erreur critique: {e}")
            if not self._finished_emitted:
                self.process_finished.emit(-1)
                self._finished_emitted = True
        finally:
            self.is_running = False
    
    def stop(self):
        """Arrête le calcul"""
        self.is_running = False


class RTKFileValidator:
    """Validateur de fichiers RINEX"""
    
    @staticmethod
    def validate_rinex_files(obs_file: Path) -> Tuple[bool, Dict[str, Path]]:
        """
        Valide qu'un fichier RINEX OBS a ses fichiers NAV et GNAV associés
        
        Returns:
            (is_valid, files_dict)
        """
        if not obs_file.exists():
            return False, {}
        
        files = {"obs": obs_file}
        
        # Recherche du fichier NAV
        nav_file = obs_file.with_suffix('.25N')
        if not nav_file.exists():
            nav_file = obs_file.with_suffix('.n')
        if not nav_file.exists():
            nav_file = obs_file.with_suffix('.nav')
        
        if nav_file.exists():
            files["nav"] = nav_file
        
        # Recherche du fichier GNAV
        gnav_file = obs_file.with_suffix('.25G')
        if not gnav_file.exists():
            gnav_file = obs_file.with_suffix('.g')
        if not gnav_file.exists():
            gnav_file = obs_file.with_suffix('.gnav')
        
        if gnav_file.exists():
            files["gnav"] = gnav_file
        
        # Validation: au moins OBS + NAV requis
        is_valid = len(files) >= 2 and "obs" in files and "nav" in files
        
        return is_valid, files
    
    @staticmethod
    def find_sp3_clk_files(data_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
        """Recherche les fichiers SP3 et CLK dans un répertoire"""
        sp3_file = None
        clk_file = None
        
        if not data_dir.exists():
            return sp3_file, clk_file
        
        # Recherche SP3 (priorité ULT sur RAP)
        sp3_files = list(data_dir.glob("*OPSULT*_02D_*.SP3"))
        if not sp3_files:
            sp3_files = list(data_dir.glob("*OPSRAP*_01D_*.SP3"))
        if sp3_files:
            sp3_file = sp3_files[0]
        
        # Recherche CLK
        clk_files = list(data_dir.glob("*OPSFIN*_01D_*_CLK.CLK"))
        if clk_files:
            clk_file = clk_files[0]
        
        return sp3_file, clk_file