"""
Module de préparation des données après les calculs RTKLIB
Intégration avec le système de gestion de projet
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QTextEdit

# Import des modules existants
from core.project_manager import ProjectManager
from core.app_data import ApplicationData

logger = logging.getLogger(__name__)


class DataPreparationWorker(QThread):
    """
    Worker thread pour la préparation des données après RTKLIB
    """
    
    # Signaux
    progress_updated = pyqtSignal(int, str)  # progress, message
    step_completed = pyqtSignal(str, dict)  # step_name, result
    preparation_completed = pyqtSignal(dict)  # final_results
    log_message = pyqtSignal(str)  # log message
    
    def __init__(self, project_manager: ProjectManager, data_path: str, quality_threshold: float = 0.1):
        super().__init__()
        self.project_manager = project_manager
        self.data_path = Path(data_path)
        self.quality_threshold = quality_threshold
        
        # Données de sortie
        self.synchronized_data = None
        self.gps_data = {}
        self.calculated_attitudes = None
        self.geometric_biases = None
        
        # Configuration de géométrie du bateau
        self.boat_geometry_matrix = None
        self.boat_geometry_abs = None
        self.enh_Base = None
        
        # Solver Procrustes
        self.transform_solver = None
        
    def run(self):
        """Exécute la préparation des données"""
        try:
            # Étape 1: Préparation des données
            self.progress_updated.emit(10, "Préparation des données...")
            if not self.prepare_data():
                self.preparation_completed.emit({"error": "Échec de la préparation des données"})
                return
            self.step_completed.emit("preparation", {"status": "success"})
            
            # Étape 2: Calcul d'attitude
            self.progress_updated.emit(50, "Calcul d'attitude...")
            attitudes = self.calculate_attitude_from_gps()
            if attitudes is None:
                self.preparation_completed.emit({"error": "Échec du calcul d'attitude"})
                return
            self.step_completed.emit("attitude", {"status": "success", "data": attitudes})
            
            # Étape 3: Analyse des biais géométriques
            self.progress_updated.emit(80, "Analyse des biais géométriques...")
            biases = self.calculate_geometric_bias()
            self.step_completed.emit("biases", {"status": "success", "data": biases})
            
            # Finalisation
            self.progress_updated.emit(100, "Préparation terminée!")
            results = {
                "status": "success",
                "attitudes": attitudes,
                "biases": biases,
                "synchronized_data": self.synchronized_data,
                "gps_data": self.gps_data,
                "data_points": len(self.synchronized_data) if self.synchronized_data is not None else 0
            }
            self.preparation_completed.emit(results)
            
        except Exception as e:
            self.preparation_completed.emit({"error": f"Erreur lors de la préparation: {str(e)}"})
    
    def _load_pos_file(self, filepath: str):
        """Charge un fichier .pos RTKLIB"""
        if not os.path.exists(filepath):
            self.log_message.emit(f"[ERREUR] Fichier introuvable: {filepath}")
            return None
            
        self.log_message.emit(f"[INFO] Lecture: {os.path.basename(filepath)}")
        
        try:
            # Trouver la fin de l'en-tête
            header_end = 0
            with open(filepath, 'r') as f:
                for i, line in enumerate(f):
                    if not line.strip().startswith('%'):
                        header_end = i
                        break
            
            # Lire les données
            df = pd.read_csv(
                filepath, 
                skiprows=header_end, 
                sep='\s+',
                names=['date', 'time', 'e', 'n', 'u', 'Q', 'ns', 'sde', 'sdn', 'sdu', 
                       'sden', 'sdnu', 'sdue', 'age', 'ratio'],
                engine='python'
            )
            
            # Créer l'index temporel
            df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            df = df.set_index('timestamp')
            
            # Calculer l'écart-type 3D
            df['sd_3d'] = np.sqrt(df['sde']**2 + df['sdn']**2 + df['sdu']**2)
            
            # Filtrer par qualité
            initial_count = len(df)
            df = df[df['sd_3d'] <= self.quality_threshold]
            filtered_count = len(df)
            
            self.log_message.emit(
                f"[OK] {initial_count} points, {filtered_count} conservés (SD < {self.quality_threshold}m)."
            )
            
            return df[['e', 'n', 'u']]
            
        except Exception as e:
            self.log_message.emit(f"[ERREUR] Lecture fichier {filepath}: {str(e)}")
            return None
    
    def _load_octans_files(self, heading_file: str, pitchroll_file: str):
        """Charge les fichiers Octans pour la synchronisation"""
        try:
            if not os.path.exists(heading_file) or not os.path.exists(pitchroll_file):
                self.log_message.emit("[INFO] Fichiers Octans non trouvés, synchronisation GPS uniquement")
                return None
            
            # Charger les données de cap
            heading_df = pd.read_csv(heading_file)
            heading_df['timestamp'] = pd.to_datetime(heading_df['timestamp'])
            heading_df = heading_df.set_index('timestamp')
            
            # Charger les données de pitch/roll
            pitchroll_df = pd.read_csv(pitchroll_file)
            pitchroll_df['timestamp'] = pd.to_datetime(pitchroll_df['timestamp'])
            pitchroll_df = pitchroll_df.set_index('timestamp')
            
            # Fusionner les données Octans
            octans_df = pd.merge(heading_df, pitchroll_df, left_index=True, right_index=True, how='inner')
            
            self.log_message.emit(f"[OK] Données Octans chargées: {len(octans_df)} points")
            return octans_df
            
        except Exception as e:
            self.log_message.emit(f"[ERREUR] Chargement Octans: {str(e)}")
            return None
    
    def prepare_data(self):
        """Prépare les données GPS et Octans"""
        self.log_message.emit("\n" + "="*60 + "\n[ÉTAPE 1] PRÉPARATION DES DONNÉES\n" + "="*60)
        
        # Charger les fichiers .pos
        port_df = self._load_pos_file(os.path.join(self.data_path, "Port-9205.pos"))
        if port_df is None:
            return False
        
        stbd_df = self._load_pos_file(os.path.join(self.data_path, "Stbd-9205.pos"))
        if stbd_df is None:
            return False
        
        # Renommer les colonnes
        port_df = port_df.rename(columns={'e': 'e_port', 'n': 'n_port', 'u': 'u_port'})
        stbd_df = stbd_df.rename(columns={'e': 'e_stbd', 'n': 'n_stbd', 'u': 'u_stbd'})
        
        # Fusionner les données GPS
        gps_baselines = pd.merge(port_df, stbd_df, left_index=True, right_index=True, how='inner')
        
        # Charger les données Octans si disponibles
        octans_df = self._load_octans_files(
            os.path.join(self.data_path, "Thialf-Octans_1-Heading.csv"),
            os.path.join(self.data_path, "Thialf-Octans_1-PitchRoll.csv")
        )
        
        if octans_df is not None:
            self.synchronized_data = pd.merge_asof(
                left=gps_baselines.sort_index(),
                right=octans_df.sort_index(),
                left_index=True,
                right_index=True,
                direction='nearest',
                tolerance=pd.Timedelta('0.5s')
            ).dropna()
        else:
            self.synchronized_data = gps_baselines
        
        # Reconstruire les positions ENH absolues
        self.log_message.emit("\n[INFO] Reconstruction des positions ENH absolues...")
        df = self.synchronized_data
        
        # Configuration de géométrie du bateau (à adapter selon le projet)
        self._setup_boat_geometry()
        
        # Reconstruire les positions GPS
        self.gps_data['GPS1'] = pd.DataFrame({
            'E': self.enh_Base[0],
            'N': self.enh_Base[1],
            'H': self.enh_Base[2]
        }, index=df.index)
        
        self.gps_data['GPS2'] = pd.DataFrame({
            'E': self.enh_Base[0] + df['e_port'],
            'N': self.enh_Base[1] + df['n_port'],
            'H': self.enh_Base[2] + df['u_port']
        }, index=df.index)
        
        self.gps_data['GPS3'] = pd.DataFrame({
            'E': self.enh_Base[0] + df['e_stbd'],
            'N': self.enh_Base[1] + df['n_stbd'],
            'H': self.enh_Base[2] + df['u_stbd']
        }, index=df.index)
        
        self.log_message.emit("[OK] Structure de données GPS reconstruite.")
        return True
    
    def _setup_boat_geometry(self):
        """Configure la géométrie du bateau"""
        # Configuration par défaut (à adapter selon le projet)
        self.boat_geometry_matrix = np.array([
            [0.0, 0.0, 0.0],      # GPS1 (Base)
            [0.0, 10.0, 0.0],     # GPS2 (Port)
            [0.0, -10.0, 0.0]     # GPS3 (Stbd)
        ])
        
        self.boat_geometry_abs = {
            'GPS1': np.array([0.0, 0.0, 0.0]),
            'GPS2': np.array([0.0, 10.0, 0.0]),
            'GPS3': np.array([0.0, -10.0, 0.0])
        }
        
        # Position de base (à configurer selon le projet)
        self.enh_Base = np.array([0.0, 0.0, 0.0])
        
        # Initialiser le solver Procrustes
        try:
            from core.calculations.procrustes_solver import ProcrustesTransformSolver
            self.transform_solver = ProcrustesTransformSolver()
        except ImportError:
            self.log_message.emit("[ATTENTION] ProcrustesTransformSolver non disponible")
            self.transform_solver = None
    
    def calculate_attitude_from_gps(self):
        """Calcule l'attitude à partir des données GPS"""
        self.log_message.emit("\n" + "="*60 + "\n[ÉTAPE 2] CALCUL D'ATTITUDE\n" + "="*60)
        
        if not self.transform_solver:
            self.log_message.emit("[ERREUR] ProcrustesTransformSolver non disponible")
            return None
        
        min_length = min(len(df) for df in self.gps_data.values())
        self.log_message.emit(f"\n[INFO] Traitement de {min_length} positions...")
        
        attitudes = {'heading': [], 'pitch': [], 'roll': []}
        
        for i in range(min_length):
            try:
                # Positions observées
                observed_positions = np.array([
                    self.gps_data['GPS1'].iloc[i].values,
                    self.gps_data['GPS2'].iloc[i].values,
                    self.gps_data['GPS3'].iloc[i].values
                ])
                
                if np.any(np.isnan(observed_positions)):
                    continue
                
                # Analyse Procrustes
                R, t, scale = self.transform_solver.procrustes_analysis(
                    self.boat_geometry_matrix, observed_positions
                )
                
                # Calcul du cap
                forward_enh = R @ np.array([0, 1, 0])
                heading_rad = np.arctan2(forward_enh[0], forward_enh[1])
                
                # Calcul du pitch et roll
                V12 = observed_positions[1] - observed_positions[0]
                V13 = observed_positions[2] - observed_positions[0]
                N_GPS_unit = np.cross(V12, V13)
                N_GPS_unit /= np.linalg.norm(N_GPS_unit)
                
                cos_h, sin_h = np.cos(heading_rad), np.sin(heading_rad)
                N_plan_YZ = np.array([cos_h, -sin_h, 0])
                N_plan_XZ = np.array([sin_h, cos_h, 0])
                
                D_pitch = np.cross(N_GPS_unit, N_plan_YZ)
                D_roll = np.cross(N_GPS_unit, N_plan_XZ)
                
                pitch_rad = np.arctan2(D_pitch[2], np.sqrt(D_pitch[0]**2 + D_pitch[1]**2))
                if np.dot(D_pitch, forward_enh) < 0:
                    pitch_rad *= -1
                
                roll_rad = np.arcsin(np.clip(-D_roll[2], -1.0, 1.0))
                if np.dot(D_roll, R @ np.array([1, 0, 0])) < 0:
                    roll_rad *= -1
                
                attitudes['heading'].append(np.degrees(heading_rad))
                attitudes['pitch'].append(np.degrees(pitch_rad))
                attitudes['roll'].append(np.degrees(roll_rad))
                
            except Exception as e:
                continue
        
        # Créer le DataFrame des attitudes
        valid_indices = self.synchronized_data.index[:len(attitudes['heading'])]
        self.calculated_attitudes = pd.DataFrame(attitudes, index=valid_indices)
        self.calculated_attitudes['heading'] = (self.calculated_attitudes['heading'] + 360) % 360
        
        self.log_message.emit(f"[OK] Calcul terminé. {len(self.calculated_attitudes)} points d'attitude valides.")
        return self.calculated_attitudes
    
    def calculate_geometric_bias(self):
        """Calcule les biais géométriques théoriques"""
        self.log_message.emit("\n[ANALYSE] BIAIS GÉOMÉTRIQUE THÉORIQUE (MÉTHODE DU TILT DU PLAN)")
        
        A1 = self.boat_geometry_abs['GPS1']
        A2 = self.boat_geometry_abs['GPS2']
        A3 = self.boat_geometry_abs['GPS3']
        
        v1 = A2 - A1
        v2 = A3 - A1
        normal_vector = np.cross(v1, v2)
        
        if normal_vector[2] < 0:
            normal_vector *= -1
        
        normal_unit_vector = normal_vector / np.linalg.norm(normal_vector)
        nx, ny, nz = normal_unit_vector
        
        roll_bias = np.degrees(np.arcsin(-nx))
        pitch_bias = np.degrees(np.arcsin(ny / np.cos(np.radians(roll_bias))))
        
        self.log_message.emit(f"Vecteur normal au plan (unitaire): [{nx:.4f}, {ny:.4f}, {nz:.4f}]")
        self.log_message.emit(f"Biais calculé: Pitch={pitch_bias:+.3f}°, Roll={roll_bias:+.3f}°")
        
        self.geometric_biases = {
            'pitch_bias': pitch_bias,
            'roll_bias': roll_bias
        }
        
        return self.geometric_biases


class DataPreparationWidget(QWidget):
    """Widget pour la préparation des données après RTKLIB"""
    
    def __init__(self, project_manager: ProjectManager = None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.worker = None
        self.init_ui()
        self.setStyleSheet(APP_STYLESHEET)
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle('Préparation des Données GNSS')
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title_label = QLabel("Préparation des Données après RTKLIB")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("En attente...")
        layout.addWidget(self.progress_bar)
        
        # Zone de log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Boutons de contrôle
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton
        
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Démarrer la préparation")
        self.start_button.clicked.connect(self.start_preparation)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Arrêter")
        self.stop_button.clicked.connect(self.stop_preparation)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
    
    def start_preparation(self):
        """Démarre la préparation des données"""
        try:
            # Obtenir le chemin des données depuis le projet
            if not self.project_manager or not self.project_manager.current_project:
                self.log_text.append("Erreur: Aucun projet chargé")
                return
            
            project_structure = self.project_manager.current_project.get('project_structure', {})
            data_path = project_structure.get('base_path', '')
            
            if not data_path:
                self.log_text.append("Erreur: Chemin des données non configuré")
                return
            
            # Créer le worker
            self.worker = DataPreparationWorker(
                self.project_manager,
                data_path,
                quality_threshold=0.1
            )
            
            # Connecter les signaux
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.step_completed.connect(self.on_step_completed)
            self.worker.preparation_completed.connect(self.on_preparation_completed)
            self.worker.log_message.connect(self.on_log_message)
            
            # Mettre à jour l'interface
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Démarrer le worker
            self.worker.start()
            
        except Exception as e:
            self.log_text.append(f"Erreur: {str(e)}")
    
    def stop_preparation(self):
        """Arrête la préparation"""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setFormat("Préparation arrêtée")
    
    def update_progress(self, progress: int, message: str):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(message)
    
    def on_step_completed(self, step_name: str, result: dict):
        """Gère la fin d'une étape"""
        self.log_text.append(f"✓ Étape {step_name} terminée: {result.get('status', 'unknown')}")
    
    def on_preparation_completed(self, results: dict):
        """Gère la fin de la préparation"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if results.get("status") == "success":
            self.progress_bar.setFormat("Préparation terminée avec succès")
            self.log_text.append("✅ Préparation des données terminée avec succès")
            
            # Sauvegarder les résultats dans le projet
            if self.project_manager:
                self._save_results_to_project(results)
        else:
            self.progress_bar.setFormat(f"Erreur: {results.get('error', 'Inconnue')}")
            self.log_text.append(f"❌ Erreur: {results.get('error', 'Inconnue')}")
    
    def on_log_message(self, message: str):
        """Affiche un message de log"""
        self.log_text.append(message)
    
    def _save_results_to_project(self, results: dict):
        """Sauvegarde les résultats dans le projet"""
        try:
            if not self.project_manager.current_project:
                return
            
            # Ajouter les résultats à la configuration GNSS
            if 'gnss_config' not in self.project_manager.current_project:
                self.project_manager.current_project['gnss_config'] = {}
            
            self.project_manager.current_project['gnss_config']['data_preparation'] = {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'attitudes_count': results.get('data_points', 0),
                'geometric_biases': results.get('biases', {}),
                'quality_threshold': 0.1
            }
            
            # Marquer l'étape comme terminée
            self.project_manager.current_project['workflow_status']['gnss_finalized'] = {
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                'progress': 100
            }
            
            # Sauvegarder le projet
            self.project_manager.save_project(auto=True)
            self.log_text.append("✅ Résultats sauvegardés dans le projet")
            
        except Exception as e:
            self.log_text.append(f"⚠️ Erreur lors de la sauvegarde: {str(e)}")


# Style pour l'interface
APP_STYLESHEET = """
QWidget {
    background-color: #2E3440;
    color: #ECEFF4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}
QProgressBar {
    border: 1px solid #4C566A;
    border-radius: 8px;
    text-align: center;
    padding: 1px;
    background-color: #3B4252;
    height: 40px;
    font-size: 11pt;
}
QProgressBar::chunk {
    background-color: qlineargradient(
        x1: 0, y1: 0.5, x2: 1, y2: 0.5,
        stop: 0 #81A1C1, stop: 1 #88C0D0
    );
    border-radius: 7px;
}
QPushButton {
    background-color: #4C566A;
    border: 1px solid #5E81AC;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5E81AC;
}
QPushButton:pressed {
    background-color: #3B4252;
}
QTextEdit {
    background-color: #3B4252;
    border: 1px solid #4C566A;
    border-radius: 6px;
    padding: 8px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 9pt;
}
"""
