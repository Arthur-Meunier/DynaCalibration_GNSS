"""
Page GNSS Post-Calcul - Finalisation des Calculs GPS

Étapes de finalisation :
1. Préparation des données (lecture fichiers .pos, filtrage qualité)
2. Calcul d'attitude (heading, pitch, roll)
3. Analyse des biais géométriques
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QTextEdit,
                             QProgressBar, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QThread, pyqtSlot
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPixmap

# Import pour matplotlib interactif
import matplotlib
matplotlib.use('Qt5Agg')  # Backend interactif PyQt5
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from pathlib import Path
from typing import Dict, Any, List
import json
import pandas as pd
import numpy as np
import os

from core.app_data import ApplicationData
from core.project_manager import ProjectManager


class InteractiveAttitudePlot(FigureCanvas):
    """Widget matplotlib interactif pour l'affichage des variations d'attitude"""
    
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        # Configuration du thème sombre
        plt.style.use('dark_background')
        
        # Créer la figure avec le thème sombre
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#2E3440')
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Couleurs du thème Nord
        self.colors = {
            'heading': '#81A1C1',    # Bleu clair
            'pitch': '#A3BE8C',      # Vert
            'roll': '#EBCB8B',       # Jaune
            'grid': '#4C566A',       # Gris
            'text': '#ECEFF4',       # Blanc
            'background': '#2E3440'  # Fond sombre
        }
        
        # Créer les sous-graphiques
        self.axes = self.fig.subplots(3, 1, sharex=True)
        self.fig.suptitle('Variations d\'attitude au cours du temps', 
                         fontsize=16, fontweight='bold', color=self.colors['text'])
        
        # Configuration des axes
        self._setup_axes()
        
        # Données
        self.attitude_data = None
        
    def _setup_axes(self):
        """Configure l'apparence des axes"""
        for i, (ax, title, ylabel, color) in enumerate(zip(
            self.axes, 
            ['Heading (Cap)', 'Pitch (Tangage)', 'Roll (Roulis)'],
            ['Heading (°)', 'Pitch (°)', 'Roll (°)'],
            [self.colors['heading'], self.colors['pitch'], self.colors['roll']]
        )):
            ax.set_title(title, fontsize=12, color=color, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=10, color=self.colors['text'], fontweight='bold')
            ax.grid(True, alpha=0.3, color=self.colors['grid'])
            ax.set_facecolor(self.colors['background'])
            ax.tick_params(colors=self.colors['text'])
            
            # Ligne de référence à zéro pour pitch et roll
            if i > 0:
                ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5)
        
        # Configuration de l'axe X (temps)
        self.axes[-1].set_xlabel('Temps', fontsize=10, color=self.colors['text'], fontweight='bold')
        
        # Formatage de l'axe temporel
        for ax in self.axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, color=self.colors['text'])
        
        # Ajustement de l'espacement
        self.fig.tight_layout()
    
    def update_data(self, attitude_data):
        """Met à jour les données d'attitude et redessine le graphique"""
        self.attitude_data = attitude_data
        
        if attitude_data is None or attitude_data.empty:
            return
        
        # Effacer les anciens graphiques
        for ax in self.axes:
            ax.clear()
        
        # Reconfigurer les axes
        self._setup_axes()
        
        # Convertir l'index en datetime si nécessaire
        time_index = attitude_data.index
        
        # Graphique Heading avec échelle adaptative
        self.axes[0].plot(time_index, attitude_data['heading'], 
                         color=self.colors['heading'], linewidth=2, alpha=0.8)
        
        # Calculer l'échelle adaptative pour le heading
        hdg_min = attitude_data['heading'].min()
        hdg_max = attitude_data['heading'].max()
        hdg_range = hdg_max - hdg_min
        
        # Ajouter une marge de 10% de chaque côté
        margin = hdg_range * 0.1
        y_min = max(0, hdg_min - margin)
        y_max = min(360, hdg_max + margin)
        
        # Si la plage est très petite, utiliser une plage minimale
        if hdg_range < 5:
            center = (hdg_min + hdg_max) / 2
            y_min = max(0, center - 2.5)
            y_max = min(360, center + 2.5)
        
        self.axes[0].set_ylim(y_min, y_max)
        
        # Graphique Pitch
        self.axes[1].plot(time_index, attitude_data['pitch'], 
                         color=self.colors['pitch'], linewidth=2, alpha=0.8)
        
        # Graphique Roll
        self.axes[2].plot(time_index, attitude_data['roll'], 
                         color=self.colors['roll'], linewidth=2, alpha=0.8)
        
        # Redessiner
        self.draw()
    
    def add_statistics(self, stats):
        """Ajoute des statistiques au graphique"""
        if not stats or not self.attitude_data:
            return
        
        # Ajouter les statistiques comme texte
        for i, (ax, param) in enumerate(zip(self.axes, ['heading', 'pitch', 'roll'])):
            if param in stats:
                stat_text = f"Min: {stats[param]['min']:.2f}° | Max: {stats[param]['max']:.2f}° | Moy: {stats[param]['mean']:.2f}° | σ: {stats[param]['std']:.2f}°"
                ax.text(0.02, 0.98, stat_text, transform=ax.transAxes, 
                       fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.7, edgecolor='none'),
                       color=self.colors['text'])
        
        self.draw()


class ProcrustesTransformSolver:
    """Solver pour l'analyse Procrustes"""
    
    def __init__(self):
        pass
    
    def procrustes_analysis(self, reference_points, observed_points):
        """
        Effectue l'analyse Procrustes pour trouver la transformation optimale
        
        Args:
            reference_points: Points de référence (géométrie du bateau)
            observed_points: Points observés (positions GPS)
            
        Returns:
            R: Matrice de rotation
            t: Vecteur de translation
            scale: Facteur d'échelle
        """
        # Centrer les points
        ref_centered = reference_points - np.mean(reference_points, axis=0)
        obs_centered = observed_points - np.mean(observed_points, axis=0)
        
        # Calculer la matrice de corrélation
        H = obs_centered.T @ ref_centered
        
        # Décomposition SVD
        U, S, Vt = np.linalg.svd(H)
        
        # Matrice de rotation
        R = U @ Vt
        
        # S'assurer que c'est une rotation (déterminant = 1)
        if np.linalg.det(R) < 0:
            U[:, -1] *= -1
            R = U @ Vt
        
        # Facteur d'échelle
        scale = np.sum(S) / np.sum(np.linalg.norm(ref_centered, axis=1)**2)
        
        # Translation
        t = np.mean(observed_points, axis=0) - scale * R @ np.mean(reference_points, axis=0)
        
        return R, t, scale


class GPSFinalizationWorker(QThread):
    """Worker thread pour la finalisation des calculs GPS"""
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    step_completed = pyqtSignal(str, dict)    # step_name, results
    finalization_completed = pyqtSignal(dict)  # final_results
    attitude_data_ready = pyqtSignal(object)  # données d'attitude prêtes pour affichage
    
    def __init__(self, data_path: str, quality_threshold: float = 0.1, project_manager=None):
        super().__init__()
        self.data_path = data_path
        self.quality_threshold = quality_threshold
        self.project_manager = project_manager
        self.gps_data = {}
        self.synchronized_data = None
        self.calculated_attitudes = None
        
        # Charger la géométrie depuis la configuration du projet
        self._load_boat_geometry()
        
        # Solver Procrustes
        self.transform_solver = ProcrustesTransformSolver()
    
    def _load_boat_geometry(self):
        """Charge la géométrie du bateau depuis la configuration DIMCON du projet"""
        # Géométrie par défaut (fallback)
        default_geometry = {
            'Bow': np.array([-0.269, -64.232, 10.888]),
            'Port': np.array([-9.347, -27.956, 13.491]),
            'Stb': np.array([9.392, -27.827, 13.506])
        }
        
        # Essayer de charger depuis le projet DIMCON
        if self.project_manager and self.project_manager.get_current_project():
            project = self.project_manager.get_current_project()
            dimcon_data = project.get('dimcon_data', {})
            points_data = dimcon_data.get('points', {})
            
            if points_data and len(points_data) >= 3:
                # Utiliser la géométrie DIMCON du projet
                geometry = {}
                for point_name, coords in points_data.items():
                    geometry[point_name] = np.array([coords['X'], coords['Y'], coords['Z']])
                
                print(f"[INFO] Géométrie DIMCON chargée depuis le projet:")
                for name, pos in geometry.items():
                    print(f"   {name}: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
            else:
                # Utiliser la géométrie par défaut
                geometry = default_geometry
                print(f"[INFO] Géométrie par défaut utilisée (DIMCON non trouvé):")
                for name, pos in geometry.items():
                    print(f"   {name}: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        else:
            # Utiliser la géométrie par défaut
            geometry = default_geometry
            print(f"[INFO] Géométrie par défaut utilisée (pas de projet):")
            for name, pos in geometry.items():
                print(f"   {name}: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        
        # Construire la matrice de géométrie (Bow=GPS1, Port=GPS2, Stb=GPS3)
        self.boat_geometry_matrix = np.array([
            geometry['Bow'],    # GPS1 (base)
            geometry['Port'],   # GPS2 (port)
            geometry['Stb']     # GPS3 (stbd)
        ])
        
        # Géométrie absolue du bateau (positions absolues incluant le tilt)
        self.boat_geometry_abs = {
            'GPS1': geometry['Bow'],
            'GPS2': geometry['Port'],
            'GPS3': geometry['Stb']
        }
        
        # Position de base ENH (à adapter selon votre projet)
        self.enh_Base = np.array([0.0, 0.0, 0.0])
        
    def run(self):
        """Exécute la finalisation des calculs GPS"""
        try:
            # Étape 1: Préparation des données
            self.progress_updated.emit(10, "Préparation des données...")
            if not self.prepare_data():
                self.finalization_completed.emit({"error": "Échec de la préparation des données"})
                return
            self.step_completed.emit("preparation", {"status": "success"})
            
            # Étape 2: Calcul d'attitude
            self.progress_updated.emit(50, "Calcul d'attitude...")
            attitudes = self.calculate_attitude_from_gps()
            if attitudes is None:
                self.finalization_completed.emit({"error": "Échec du calcul d'attitude"})
                return
            self.step_completed.emit("attitude", {"status": "success", "data": attitudes})
            
            # Étape 3: Analyse des biais géométriques
            self.progress_updated.emit(80, "Analyse des biais géométriques...")
            biases = self.calculate_geometric_bias()
            self.step_completed.emit("biases", {"status": "success", "data": biases})
            
            # Finalisation
            self.progress_updated.emit(100, "Finalisation terminée!")
            results = {
                "status": "success",
                "attitudes": attitudes,
                "biases": biases,
                "data_points": len(self.synchronized_data) if self.synchronized_data is not None else 0
            }
            self.finalization_completed.emit(results)
            
        except Exception as e:
            self.finalization_completed.emit({"error": f"Erreur lors de la finalisation: {str(e)}"})
    
    def _load_pos_file(self, filepath: str):
        """Charge un fichier .pos RTKLIB - Version robuste avec filtrage des lignes"""
        if not os.path.exists(filepath):
            print(f"[ERREUR] Fichier introuvable: {filepath}")
            return None
            
        print(f"[INFO] Lecture: {os.path.basename(filepath)}")
        try:
            # Lire le fichier ligne par ligne pour filtrer les données valides
            data_lines = []
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    # Ignorer les lignes d'en-tête et les lignes vides
                    if line.startswith('%') or line.startswith('program') or not line:
                        continue
                    
                    # Vérifier que la ligne contient des données numériques
                    parts = line.split()
                    if len(parts) >= 15:  # Au moins 15 colonnes attendues
                        try:
                            # Tester si la première partie est une date valide (YYYY/MM/DD)
                            if '/' in parts[0] and len(parts[0]) == 10:
                                data_lines.append(line)
                        except (ValueError, IndexError):
                            continue
            
            if not data_lines:
                print(f"[ERREUR] Aucune donnée valide trouvée dans {filepath}")
                return None
            
            # Créer un DataFrame à partir des lignes de données filtrées
            from io import StringIO
            data_text = '\n'.join(data_lines)
            df = pd.read_csv(StringIO(data_text), sep='\s+',
                           names=['date', 'time', 'e', 'n', 'u', 'Q', 'ns', 'sde', 'sdn', 'sdu', 'sden', 'sdnu', 'sdue', 'age', 'ratio'],
                           engine='python')
            
            # Créer le timestamp avec format explicite
            try:
                df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y/%m/%d %H:%M:%S.%f')
            except:
                try:
                    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y/%m/%d %H:%M:%S')
                except:
                    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            
            # Supprimer les lignes avec timestamp invalide
            df = df.dropna(subset=['timestamp'])
            df = df.set_index('timestamp')
            
            # Calculer SD 3D
            df['sd_3d'] = np.sqrt(df['sde']**2 + df['sdn']**2 + df['sdu']**2)
            initial_count = len(df)
            
            # Filtrage par qualité
            df = df[df['sd_3d'] <= self.quality_threshold]
            filtered_count = len(df)
            
            print(f"[OK] {initial_count} points, {filtered_count} conservés (SD < {self.quality_threshold}m).")
            return df[['e', 'n', 'u']]
            
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {filepath}: {e}")
            return None
    
    def _has_data(self, filepath: Path) -> bool:
        """Vérifie si un fichier .pos contient des données (pas seulement l'en-tête)"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    # Ignorer les lignes d'en-tête
                    if line.startswith('%') or line.startswith('program') or not line:
                        continue
                    
                    # Vérifier si c'est une ligne de données
                    parts = line.split()
                    if len(parts) >= 15 and '/' in parts[0] and len(parts[0]) == 10:
                        return True
            return False
        except Exception:
            return False
    
    def _load_octans_files(self, heading_file, pitchroll_file):
        """Charge les fichiers Octans pour la synchronisation"""
        try:
            # Charger le fichier heading
            heading_df = pd.read_csv(heading_file)
            heading_df['timestamp'] = pd.to_datetime(heading_df['timestamp'])
            heading_df = heading_df.set_index('timestamp')
            
            # Charger le fichier pitch/roll
            pitchroll_df = pd.read_csv(pitchroll_file)
            pitchroll_df['timestamp'] = pd.to_datetime(pitchroll_df['timestamp'])
            pitchroll_df = pitchroll_df.set_index('timestamp')
            
            # Fusionner les données Octans
            octans_df = pd.merge(heading_df, pitchroll_df, left_index=True, right_index=True, how='inner')
            print(f"[OK] Données Octans chargées: {len(octans_df)} points")
            return octans_df
            
        except Exception as e:
            print(f"[INFO] Fichiers Octans non disponibles: {e}")
            return None
    
    def prepare_data(self):
        """Prépare les données GPS pour le calcul d'attitude - Utilise les fichiers .pos générés par RTKLIB"""
        print("\n" + "="*60 + "\n[ÉTAPE 1] PRÉPARATION DES DONNÉES\n" + "="*60)
        
        # Chercher les fichiers .pos dans export/ et export/export/
        pos_files = []
        
        # Chercher dans export/
        export_dir = Path("export")
        if export_dir.exists():
            for file in export_dir.glob("*.pos"):
                if "_events.pos" not in file.name:
                    pos_files.append(file)
        
        # Chercher dans export/export/
        export_subdir = export_dir / "export"
        if export_subdir.exists():
            for file in export_subdir.glob("*.pos"):
                if "_events.pos" not in file.name and file not in pos_files:
                    pos_files.append(file)
        
        if len(pos_files) < 2:
            print(f"[ERREUR] Au moins 2 fichiers .pos requis, trouvé: {len(pos_files)}")
            print(f"[INFO] Recherche dans: export/ et export/export/")
            return False
        
        # Trier par date de modification (les plus récents en premier)
        pos_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Filtrer les fichiers qui contiennent des données
        valid_files = []
        for file in pos_files:
            if self._has_data(file):
                valid_files.append(file)
                if len(valid_files) >= 2:
                    break
        
        if len(valid_files) < 2:
            print(f"[ERREUR] Moins de 2 fichiers .pos avec des données trouvés")
            return False
        
        latest_files = valid_files[:2]
        print(f"[INFO] Utilisation des fichiers .pos les plus récents avec des données:")
        for i, file in enumerate(latest_files):
            print(f"   {i+1}. {file.name}")
        
        # Charger les fichiers .pos
        port_df = self._load_pos_file(str(latest_files[0]))
        if port_df is None: 
            return False
        port_df = port_df.rename(columns={'e':'e_port', 'n':'n_port', 'u':'u_port'})
        
        stbd_df = self._load_pos_file(str(latest_files[1]))
        if stbd_df is None: 
            return False
        stbd_df = stbd_df.rename(columns={'e':'e_stbd', 'n':'n_stbd', 'u':'u_stbd'})

        # Fusionner les données GPS (alignement temporel automatique)
        gps_baselines = pd.merge(port_df, stbd_df, left_index=True, right_index=True, how='inner')
        print(f"[INFO] {len(gps_baselines)} points temporellement alignés")

        # Pas besoin de fichiers Octans - on travaille directement avec les baselines GPS
        self.synchronized_data = gps_baselines

        print("\n[INFO] Reconstruction des positions ENH absolues...")
        df = self.synchronized_data
        self.gps_data['GPS1'] = pd.DataFrame({'E': self.enh_Base[0], 'N': self.enh_Base[1], 'H': self.enh_Base[2]}, index=df.index)
        self.gps_data['GPS2'] = pd.DataFrame({'E': self.enh_Base[0] + df['e_port'], 'N': self.enh_Base[1] + df['n_port'], 'H': self.enh_Base[2] + df['u_port']}, index=df.index)
        self.gps_data['GPS3'] = pd.DataFrame({'E': self.enh_Base[0] + df['e_stbd'], 'N': self.enh_Base[1] + df['n_stbd'], 'H': self.enh_Base[2] + df['u_stbd']}, index=df.index)
        print("[OK] Structure de données GPS reconstruite.")
        return True
    
    def calculate_attitude_from_gps(self):
        """Calcule l'attitude à partir des positions GPS - Version basée sur le script de référence"""
        print("\n" + "="*60 + "\n[ÉTAPE 2] CALCUL D'ATTITUDE\n" + "="*60)
        min_length = min(len(df) for df in self.gps_data.values())
        print(f"\n[INFO] Traitement de {min_length} positions...")

        attitudes = {'heading': [], 'pitch': [], 'roll': []}

        for i in range(min_length):
            try:
                observed_positions = np.array([
                    self.gps_data['GPS1'].iloc[i].values,
                    self.gps_data['GPS2'].iloc[i].values,
                    self.gps_data['GPS3'].iloc[i].values
                ])
                if np.any(np.isnan(observed_positions)): 
                    continue

                # Analyse Procrustes
                R, t, scale = self.transform_solver.procrustes_analysis(self.boat_geometry_matrix, observed_positions)

                # Calcul du heading
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

        valid_indices = self.synchronized_data.index[:len(attitudes['heading'])]
        self.calculated_attitudes = pd.DataFrame(attitudes, index=valid_indices)
        self.calculated_attitudes['heading'] = (self.calculated_attitudes['heading'] + 360) % 360
        print(f"[OK] Calcul terminé. {len(self.calculated_attitudes)} points d'attitude valides.")
        
        # Afficher les statistiques des variations
        self._print_attitude_statistics()
        
        return self.calculated_attitudes
    
    def _print_attitude_statistics(self):
        """Affiche les statistiques des variations d'attitude et crée un graphique"""
        if self.calculated_attitudes is None or len(self.calculated_attitudes) == 0:
            return
            
        print("\n" + "="*60 + "\n[STATISTIQUES] VARIATIONS D'ATTITUDE\n" + "="*60)
        
        # Calculer les statistiques
        hdg_stats = self.calculated_attitudes['heading'].describe()
        pitch_stats = self.calculated_attitudes['pitch'].describe()
        roll_stats = self.calculated_attitudes['roll'].describe()
        
        print(f"📊 HEADING (degrés):")
        print(f"   Min: {hdg_stats['min']:.2f}° | Max: {hdg_stats['max']:.2f}° | Moyenne: {hdg_stats['mean']:.2f}° | Écart-type: {hdg_stats['std']:.2f}°")
        
        print(f"📊 PITCH (degrés):")
        print(f"   Min: {pitch_stats['min']:.2f}° | Max: {pitch_stats['max']:.2f}° | Moyenne: {pitch_stats['mean']:.2f}° | Écart-type: {pitch_stats['std']:.2f}°")
        
        print(f"📊 ROLL (degrés):")
        print(f"   Min: {roll_stats['min']:.2f}° | Max: {roll_stats['max']:.2f}° | Moyenne: {roll_stats['mean']:.2f}° | Écart-type: {roll_stats['std']:.2f}°")
        
        # Émettre les données d'attitude pour affichage interactif
        self.attitude_data_ready.emit(self.calculated_attitudes)
    
    def _create_attitude_plot(self):
        """Crée un graphique des variations d'attitude au cours du temps"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend non-interactif pour éviter les problèmes GUI
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            
            # Configuration du graphique
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            fig.suptitle('Variations d\'attitude au cours du temps', fontsize=16, fontweight='bold')
            
            # Convertir l'index en datetime si nécessaire
            time_index = self.calculated_attitudes.index
            
            # Graphique Heading
            ax1.plot(time_index, self.calculated_attitudes['heading'], 'b-', linewidth=1, alpha=0.7)
            ax1.set_ylabel('Heading (°)', fontweight='bold')
            ax1.set_title('Heading (Cap)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 360)
            
            # Graphique Pitch
            ax2.plot(time_index, self.calculated_attitudes['pitch'], 'g-', linewidth=1, alpha=0.7)
            ax2.set_ylabel('Pitch (°)', fontweight='bold')
            ax2.set_title('Pitch (Tangage)', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            
            # Graphique Roll
            ax3.plot(time_index, self.calculated_attitudes['roll'], 'r-', linewidth=1, alpha=0.7)
            ax3.set_ylabel('Roll (°)', fontweight='bold')
            ax3.set_title('Roll (Roulis)', fontsize=12)
            ax3.set_xlabel('Temps', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
            
            # Formatage de l'axe temporel
            for ax in [ax1, ax2, ax3]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Ajustement de l'espacement
            plt.tight_layout()
            
            # Sauvegarder le graphique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attitude_variations_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📈 Graphique sauvegardé: {filename}")
            
            # Émettre le signal pour afficher le graphique
            self.graph_created.emit(filename)
            
            # Fermer la figure pour libérer la mémoire
            plt.close(fig)
            
        except ImportError:
            print("⚠️ Matplotlib non disponible - graphique non créé")
        except Exception as e:
            print(f"⚠️ Erreur lors de la création du graphique: {e}")
    
    def procrustes_analysis(self, X, Y):
        """Analyse Procrustes simplifiée"""
        # Centrer les données
        X_centered = X - np.mean(X, axis=0)
        Y_centered = Y - np.mean(Y, axis=0)
        
        # Calculer la matrice de corrélation
        H = X_centered.T @ Y_centered
        
        # Décomposition SVD
        U, S, Vt = np.linalg.svd(H)
        
        # Matrice de rotation
        R = Vt.T @ U.T
        
        # Vérifier le déterminant
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        
        # Translation et échelle
        t = np.mean(Y, axis=0) - R @ np.mean(X, axis=0)
        scale = np.trace(S) / np.trace(X_centered.T @ X_centered)
        
        return R, t, scale
    
    def calculate_geometric_bias(self):
        """Calcule les biais géométriques théoriques - Version basée sur le script de référence"""
        print("\n[ANALYSE] BIAIS GÉOMÉTRIQUE THÉORIQUE (MÉTHODE DU TILT DU PLAN)")
        
        # Utiliser la géométrie absolue du bateau (comme dans le script de référence)
        # Les positions absolues incluent déjà le tilt du bateau
        A1 = self.boat_geometry_abs['GPS1']
        A2 = self.boat_geometry_abs['GPS2'] 
        A3 = self.boat_geometry_abs['GPS3']

        print(f"Position GPS1 (Base): [{A1[0]:.3f}, {A1[1]:.3f}, {A1[2]:.3f}]")
        print(f"Position GPS2 (Port): [{A2[0]:.3f}, {A2[1]:.3f}, {A2[2]:.3f}]")
        print(f"Position GPS3 (Stbd): [{A3[0]:.3f}, {A3[1]:.3f}, {A3[2]:.3f}]")

        v1 = A2 - A1
        v2 = A3 - A1
        print(f"Vecteur v1 (GPS2-GPS1): [{v1[0]:.3f}, {v1[1]:.3f}, {v1[2]:.3f}]")
        print(f"Vecteur v2 (GPS3-GPS1): [{v2[0]:.3f}, {v2[1]:.3f}, {v2[2]:.3f}]")
        
        normal_vector = np.cross(v1, v2)
        print(f"Vecteur normal (produit vectoriel): [{normal_vector[0]:.3f}, {normal_vector[1]:.3f}, {normal_vector[2]:.3f}]")
        
        norm = np.linalg.norm(normal_vector)
        print(f"Norme du vecteur normal: {norm:.6f}")
        
        if norm < 1e-10:
            print("[ERREUR] Les antennes sont alignées - impossible de calculer le plan")
            return {'pitch_bias': 0.0, 'roll_bias': 0.0}
        
        if normal_vector[2] < 0:
            normal_vector *= -1
        normal_unit_vector = normal_vector / norm
        nx, ny, nz = normal_unit_vector

        roll_bias = np.degrees(np.arcsin(-nx))
        pitch_bias = np.degrees(np.arcsin(ny / np.cos(np.radians(roll_bias))))

        print(f"Vecteur normal au plan (unitaire): [{nx:.4f}, {ny:.4f}, {nz:.4f}]")
        print(f"Biais calculé: Pitch={pitch_bias:+.3f}°, Roll={roll_bias:+.3f}°")
        return {'pitch_bias': pitch_bias, 'roll_bias': roll_bias}


class GNSSPostCalcWidget(QWidget):
    """Widget pour la finalisation des calculs GNSS"""
    
    reset_requested = pyqtSignal()
    recalculate_requested = pyqtSignal()
    
    def __init__(self, app_data: ApplicationData = None, project_manager: ProjectManager = None, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.project_manager = project_manager
        self.finalization_worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titre principal
        title = QLabel("🛰️ Finalisation des Calculs GNSS")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ECEFF4;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Groupe de progression
        progress_group = QGroupBox("Progression de la Finalisation")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ECEFF4;
                border: 2px solid #4C566A;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        progress_layout = QVBoxLayout()
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4C566A;
                border-radius: 5px;
                text-align: center;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #5E81AC;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Message de statut
        self.status_label = QLabel("Prêt à démarrer la finalisation")
        self.status_label.setStyleSheet("color: #D8DEE9; font-size: 12px;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Zone de résultats
        results_group = QGroupBox("Résultats de la Finalisation")
        results_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ECEFF4;
                border: 2px solid #4C566A;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        results_layout = QVBoxLayout()
        
        # Zone de texte pour les résultats
        self.results_text = QTextEdit()
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #2E3440;
                border: 1px solid #4C566A;
                border-radius: 5px;
                color: #ECEFF4;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        # Zone d'affichage du graphique interactif
        self.attitude_plot = InteractiveAttitudePlot(self, width=10, height=6, dpi=100)
        self.attitude_plot.setMinimumHeight(400)
        self.attitude_plot.setMaximumHeight(600)
        results_layout.addWidget(self.attitude_plot)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Démarrer la Finalisation")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:disabled {
                background-color: #4C566A;
                color: #6C7A89;
            }
        """)
        self.start_btn.clicked.connect(self.start_finalization)
        buttons_layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("🔄 Réinitialiser")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #D08770;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EBCB8B;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        buttons_layout.addWidget(self.reset_btn)
        
        self.recalc_btn = QPushButton("🔄 Recalculer")
        self.recalc_btn.setStyleSheet("""
            QPushButton {
                background-color: #A3BE8C;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B48EAD;
            }
        """)
        self.recalc_btn.clicked.connect(self.recalculate_requested.emit)
        buttons_layout.addWidget(self.recalc_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #3B4252;
            }
        """)
    
    def start_finalization(self):
        """Démarre la finalisation des calculs GPS"""
        if self.finalization_worker and self.finalization_worker.isRunning():
            return
            
        # Vérifier les fichiers .pos via le ProjectManager
        if not self.project_manager:
            self.results_text.append("❌ Erreur: ProjectManager non disponible")
            return
        
        # Récupérer les fichiers .pos enregistrés dans le projet
        pos_status = self.project_manager.check_gnss_pos_files_exist()
        
        if not pos_status["has_pos_files"]:
            self.results_text.append("❌ Erreur: Aucun fichier .pos enregistré dans le projet")
            return
        
        if not pos_status["existing_files"]:
            self.results_text.append("❌ Erreur: Les fichiers .pos enregistrés n'existent plus")
            self.results_text.append(f"📄 Fichiers manquants: {pos_status['missing_files']}")
            return
            
        self.results_text.clear()
        self.results_text.append("🚀 Démarrage de la finalisation des calculs GPS...")
        self.results_text.append(f"📄 Fichiers .pos trouvés: {len(pos_status['existing_files'])}")
        
        # Utiliser le répertoire du premier fichier .pos comme base
        first_pos_file = Path(pos_status["existing_files"][0])
        data_dir = str(first_pos_file.parent)
        
        # Démarrer le worker avec les fichiers spécifiques
        project_manager = ProjectManager()
        self.finalization_worker = GPSFinalizationWorker(data_dir, project_manager=project_manager)
        self.finalization_worker.progress_updated.connect(self.update_progress)
        self.finalization_worker.step_completed.connect(self.on_step_completed)
        self.finalization_worker.finalization_completed.connect(self.on_finalization_completed)
        self.finalization_worker.attitude_data_ready.connect(self.update_attitude_plot)
        
        self.start_btn.setEnabled(False)
        self.finalization_worker.start()
    
    @pyqtSlot(int, str)
    def update_progress(self, progress: int, message: str):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.results_text.append(f"📊 {message}")
    
    @pyqtSlot(str, dict)
    def on_step_completed(self, step_name: str, results: dict):
        """Traite la completion d'une étape"""
        if step_name == "preparation":
            self.results_text.append("✅ Étape 1 terminée: Préparation des données")
        elif step_name == "attitude":
            self.results_text.append("✅ Étape 2 terminée: Calcul d'attitude")
            if "data" in results:
                attitudes = results["data"]
                self.results_text.append(f"📈 Points d'attitude calculés: {len(attitudes)}")
        elif step_name == "biases":
            self.results_text.append("✅ Étape 3 terminée: Analyse des biais géométriques")
            if "data" in results:
                biases = results["data"]
                self.results_text.append(f"🎯 Biais Pitch: {biases['pitch_bias']:+.3f}°")
                self.results_text.append(f"🎯 Biais Roll: {biases['roll_bias']:+.3f}°")
    
    @pyqtSlot(dict)
    def on_finalization_completed(self, results: dict):
        """Traite la completion de la finalisation"""
        self.start_btn.setEnabled(True)
        
        if "error" in results:
            self.results_text.append(f"❌ Erreur: {results['error']}")
            self.status_label.setText("Finalisation échouée")
        else:
            self.results_text.append("🎉 Finalisation terminée avec succès!")
            self.status_label.setText("Finalisation terminée")
            
            if "data_points" in results:
                self.results_text.append(f"📊 Points de données traités: {results['data_points']}")
    
    @pyqtSlot(object)
    def update_attitude_plot(self, attitude_data):
        """Met à jour le graphique interactif d'attitude"""
        try:
            if attitude_data is not None and not attitude_data.empty:
                # Mettre à jour le graphique avec les nouvelles données
                self.attitude_plot.update_data(attitude_data)
                
                # Calculer et ajouter les statistiques
                stats = {}
                for param in ['heading', 'pitch', 'roll']:
                    if param in attitude_data.columns:
                        stats[param] = {
                            'min': attitude_data[param].min(),
                            'max': attitude_data[param].max(),
                            'mean': attitude_data[param].mean(),
                            'std': attitude_data[param].std()
                        }
                
                self.attitude_plot.add_statistics(stats)
                self.results_text.append(f"📈 Graphique d'attitude interactif mis à jour avec {attitude_data.shape[0]} points")
            else:
                self.results_text.append("⚠️ Aucune donnée d'attitude à afficher")
        except Exception as e:
            self.results_text.append(f"❌ Erreur lors de la mise à jour du graphique: {e}")
    
    def load_project_stats(self):
        """Charge les statistiques du projet (méthode de compatibilité)"""
        # Cette méthode est appelée par main.py mais n'est plus nécessaire
        # car nous utilisons maintenant la finalisation des calculs
        pass