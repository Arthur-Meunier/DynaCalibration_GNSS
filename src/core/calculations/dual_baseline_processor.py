"""
Processeur RTKLIB pour deux lignes de base en parallèle
Intégration avec l'architecture existante du projet
"""

import sys
import subprocess
import re
import os
import math
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel,
    QPushButton, QTextEdit, QHBoxLayout, QGridLayout, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRectF, QObject
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

# Import des modules existants du projet
from .rtk_calculator import RTKConfig, RTKCalculator
from core.project_manager import ProjectManager
from core.app_data import ApplicationData


# --- Style de l'application (Thème sombre "Nord") ---
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
QGroupBox {
    font-weight: bold;
    border: 2px solid #4C566A;
    border-radius: 8px;
    margin-top: 1ex;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}
"""


class DualBaselineConfig:
    """
    Configuration pour le traitement de deux lignes de base
    """
    def __init__(self, project_manager: ProjectManager = None):
        self.project_manager = project_manager
        
        # Chemins de base
        self.working_dir = Path(__file__).parent.parent.parent.parent / "RTKlib"
        self.exe_path = self.working_dir / "rnx2rtkp.exe"
        self.conf_file = self.working_dir / "configs" / "conf.conf"
        
        # Configuration des trois positions GPS
        self.positions = {
            'base': {'name': 'Base', 'obs_file': None, 'nav_file': None, 'gnav_file': None},
            'rover1': {'name': 'Port', 'obs_file': None, 'nav_file': None, 'gnav_file': None},
            'rover2': {'name': 'Stbd', 'obs_file': None, 'nav_file': None, 'gnav_file': None}
        }
        
        # Fichiers d'orbites précises
        self.precise_eph_file = None
        self.precise_clk_file = None
        
        # Répertoire de sortie
        self.output_dir = None
        self.use_sp3_clk = False
        
        # Seuil de qualité
        self.quality_threshold = 0.1
        
    def set_project_paths(self, project_data: Dict[str, Any]):
        """Configure les chemins à partir des données du projet"""
        if not project_data:
            return
            
        # Récupérer les chemins depuis le projet
        gnss_config = project_data.get('gnss_config', {})
        project_structure = project_data.get('project_structure', {})
        base_path = Path(project_structure.get('base_path', ''))
        
        # Configuration des fichiers d'observation
        rinex_files = gnss_config.get('metadata', {}).get('rinex_files', {}).get('files_by_position', {})
        
        for pos_name, pos_config in self.positions.items():
            if pos_name in rinex_files:
                files = rinex_files[pos_name]
                pos_config['obs_file'] = base_path / files.get('obs', '')
                pos_config['nav_file'] = base_path / files.get('nav', '')
                pos_config['gnav_file'] = base_path / files.get('gnav', '')
        
        # Fichiers d'orbites précises
        sp3_metadata = gnss_config.get('sp3_metadata', {})
        if sp3_metadata.get('downloaded'):
            sp3_files = sp3_metadata['downloaded']
            if sp3_files:
                self.precise_eph_file = base_path / sp3_files[0] if len(sp3_files) > 0 else None
                self.precise_clk_file = base_path / sp3_files[1] if len(sp3_files) > 1 else None
                self.use_sp3_clk = True
        
        # Répertoire de sortie
        self.output_dir = base_path / "export"
        self.output_dir.mkdir(exist_ok=True)
    
    def get_baselines(self) -> List[Dict[str, Any]]:
        """Retourne la liste des lignes de base à traiter"""
        baselines = []
        
        # Ligne de base 1: Base -> Port
        if (self.positions['base']['obs_file'] and 
            self.positions['rover1']['obs_file']):
            baselines.append({
                'name': 'Base-Port',
                'base_obs': self.positions['base']['obs_file'],
                'rover_obs': self.positions['rover1']['obs_file'],
                'rover_nav': self.positions['rover1']['nav_file'],
                'rover_gnav': self.positions['rover1']['gnav_file'],
                'output_suffix': 'Port'
            })
        
        # Ligne de base 2: Base -> Stbd
        if (self.positions['base']['obs_file'] and 
            self.positions['rover2']['obs_file']):
            baselines.append({
                'name': 'Base-Stbd',
                'base_obs': self.positions['base']['obs_file'],
                'rover_obs': self.positions['rover2']['obs_file'],
                'rover_nav': self.positions['rover2']['nav_file'],
                'rover_gnav': self.positions['rover2']['gnav_file'],
                'output_suffix': 'Stbd'
            })
        
        return baselines


class DualBaselineProcessor(QThread):
    """
    Processeur principal pour deux lignes de base en parallèle
    """
    
    # Signaux
    progress_updated = pyqtSignal(str, int)  # message, pourcentage global
    baseline_progress_updated = pyqtSignal(str, int, str)  # baseline_name, progress, message
    quality_updated = pyqtSignal(dict)  # données qualité globales
    process_finished = pyqtSignal(dict)  # résultats finaux
    log_message = pyqtSignal(str)  # message de log
    
    def __init__(self, config: DualBaselineConfig):
        super().__init__()
        self.config = config
        self.baseline_processors = []
        self.global_quality_counts = {str(k): 0 for k in range(7)}
        self.results = {}
        self.is_running = False
        
    def run(self):
        """Exécute le traitement des deux lignes de base"""
        try:
            self.is_running = True
            self.progress_updated.emit("Initialisation...", 0)
            
            # Obtenir les lignes de base
            baselines = self.config.get_baselines()
            if not baselines:
                self.process_finished.emit({"error": "Aucune ligne de base configurée"})
                return
            
            self.log_message.emit(f"Démarrage du traitement de {len(baselines)} lignes de base")
            
            # Créer et démarrer les processeurs pour chaque ligne de base
            self.baseline_processors = []
            for i, baseline in enumerate(baselines):
                processor = BaselineProcessor(baseline, self.config, i)
                processor.progress_updated.connect(
                    lambda progress, msg, idx=i: self._on_baseline_progress(baseline['name'], progress, msg)
                )
                processor.quality_updated.connect(self._on_baseline_quality)
                processor.process_finished.connect(
                    lambda result, idx=i: self._on_baseline_finished(baseline['name'], result)
                )
                processor.start()
                self.baseline_processors.append(processor)
            
            # Attendre la fin de tous les processeurs
            for processor in self.baseline_processors:
                processor.wait()
            
            # Vérifier les résultats
            if len(self.results) == len(baselines):
                self.progress_updated.emit("Traitement terminé", 100)
                self.process_finished.emit({
                    "status": "success",
                    "baselines": self.results,
                    "global_quality": self.global_quality_counts
                })
            else:
                self.process_finished.emit({
                    "status": "error",
                    "message": "Certains traitements ont échoué"
                })
                
        except Exception as e:
            self.process_finished.emit({"error": f"Erreur critique: {str(e)}"})
        finally:
            self.is_running = False
    
    def _on_baseline_progress(self, baseline_name: str, progress: int, message: str):
        """Gère la progression d'une ligne de base"""
        self.baseline_progress_updated.emit(baseline_name, progress, message)
        
        # Calculer la progression globale
        if self.baseline_processors:
            total_progress = sum(
                getattr(p, 'current_progress', 0) for p in self.baseline_processors
            )
            global_progress = total_progress // len(self.baseline_processors)
            self.progress_updated.emit(f"Traitement global...", global_progress)
    
    def _on_baseline_quality(self, quality_data: Dict[str, int]):
        """Met à jour les compteurs de qualité globaux"""
        for quality, count in quality_data.items():
            if quality in self.global_quality_counts:
                self.global_quality_counts[quality] += count
        self.quality_updated.emit(self.global_quality_counts.copy())
    
    def _on_baseline_finished(self, baseline_name: str, result: Dict[str, Any]):
        """Gère la fin du traitement d'une ligne de base"""
        self.results[baseline_name] = result
        self.log_message.emit(f"Ligne de base {baseline_name} terminée")


class BaselineProcessor(QThread):
    """
    Processeur pour une ligne de base individuelle
    """
    
    # Signaux
    progress_updated = pyqtSignal(int, str)  # progress, message
    quality_updated = pyqtSignal(dict)  # données qualité
    process_finished = pyqtSignal(dict)  # résultat
    
    def __init__(self, baseline_config: Dict[str, Any], dual_config: DualBaselineConfig, index: int):
        super().__init__()
        self.baseline_config = baseline_config
        self.dual_config = dual_config
        self.index = index
        self.current_progress = 0
        
        # Créer la configuration RTK pour cette ligne de base
        self.rtk_config = RTKConfig()
        self.rtk_config.working_dir = dual_config.working_dir
        self.rtk_config.exe_path = dual_config.exe_path
        self.rtk_config.conf_file = dual_config.conf_file
        self.rtk_config.rover_obs_file = baseline_config['rover_obs']
        self.rtk_config.base_obs_file = baseline_config['base_obs']
        self.rtk_config.rover_nav_file = baseline_config['rover_nav']
        self.rtk_config.rover_gnav_file = baseline_config['rover_gnav']
        self.rtk_config.precise_eph_file = dual_config.precise_eph_file
        self.rtk_config.precise_clk_file = dual_config.precise_clk_file
        self.rtk_config.use_sp3_clk = dual_config.use_sp3_clk
        
        # Fichier de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.rtk_config.output_file = (
            dual_config.output_dir / 
            f"rtk_output_{baseline_config['output_suffix']}_{timestamp}.pos"
        )
        
        # Calculateur RTK
        self.rtk_calculator = RTKCalculator(self.rtk_config)
        self.rtk_calculator.progress_updated.connect(self._on_rtk_progress)
        self.rtk_calculator.quality_updated.connect(self.quality_updated.emit)
        self.rtk_calculator.process_finished.connect(self._on_rtk_finished)
    
    def run(self):
        """Exécute le traitement RTK pour cette ligne de base"""
        try:
            self.progress_updated.emit(0, f"Démarrage {self.baseline_config['name']}...")
            self.rtk_calculator.start()
            self.rtk_calculator.wait()
        except Exception as e:
            self.process_finished.emit({"error": f"Erreur: {str(e)}"})
    
    def _on_rtk_progress(self, message: str, progress: int):
        """Gère la progression RTK"""
        self.current_progress = progress
        self.progress_updated.emit(progress, message)
    
    def _on_rtk_finished(self, return_code: int):
        """Gère la fin du traitement RTK"""
        if return_code == 0:
            result = {
                "status": "success",
                "output_file": str(self.rtk_config.output_file),
                "baseline_name": self.baseline_config['name']
            }
        else:
            result = {
                "status": "error",
                "return_code": return_code,
                "baseline_name": self.baseline_config['name']
            }
        
        self.process_finished.emit(result)


class DonutChartWidget(QWidget):
    """Widget pour afficher un diagramme circulaire de qualité"""
    
    def __init__(self):
        super().__init__()
        self.quality_data = {}
        self.colors = {
            '1': QColor("#A3BE8C"), '2': QColor("#EBCB8B"), '5': QColor("#D08770"),
            '4': QColor("#B48EAD"), '3': QColor("#8FBCBB"), '6': QColor("#88C0D0"),
            '0': QColor("#BF616A"),
        }
        self.setMinimumSize(80, 80)
    
    def update_data(self, quality_data: Dict[str, int]):
        """Met à jour les données du diagramme"""
        self.quality_data = quality_data.copy()
        self.update()
    
    def paintEvent(self, event):
        """Dessine le diagramme circulaire"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        side = min(rect.width(), rect.height())
        chart_rect = QRectF(
            (rect.width() - side) / 2 + 5,
            (rect.height() - side) / 2 + 5,
            side - 10,
            side - 10
        )
        
        total = sum(self.quality_data.values())
        
        if total == 0:
            painter.setPen(QPen(QColor("#4C566A"), 2))
            painter.drawEllipse(chart_rect)
            return
        
        cumulative_angle = 90.0 * 16.0
        for quality, count in sorted(self.quality_data.items()):
            if count > 0:
                angle = (count / total) * 360.0 * 16.0
                painter.setBrush(self.colors.get(quality, QColor("gray")))
                painter.setPen(Qt.NoPen)
                painter.drawPie(chart_rect, round(cumulative_angle), round(angle))
                cumulative_angle += angle
        
        # Dessiner le trou central
        hole_radius = chart_rect.width() * 0.4
        hole_rect = QRectF(
            chart_rect.center().x() - hole_radius,
            chart_rect.center().y() - hole_radius,
            hole_radius * 2,
            hole_radius * 2
        )
        painter.setBrush(QColor("#2E3440"))
        painter.drawEllipse(hole_rect)
        
        # Afficher le total
        painter.setPen(QColor("#ECEFF4"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(hole_rect, Qt.AlignCenter, f"{total}")


class DualBaselineMonitorWidget(QWidget):
    """Widget principal pour le monitoring des deux lignes de base"""
    
    def __init__(self, project_manager: ProjectManager = None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.processor = None
        self.init_ui()
        self.setStyleSheet(APP_STYLESHEET)
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle('Moniteur RTK - Deux Lignes de Base')
        self.setGeometry(100, 100, 900, 200)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Barre de progression globale
        self.global_progress_bar = QProgressBar()
        self.global_progress_bar.setTextVisible(True)
        self.global_progress_bar.setFormat("Initialisation...")
        main_layout.addWidget(self.global_progress_bar)
        
        # Layout horizontal pour les baselines
        baseline_layout = QHBoxLayout()
        
        # Groupe pour chaque ligne de base
        self.baseline_groups = {}
        baselines = ['Base-Port', 'Base-Stbd']
        
        for baseline_name in baselines:
            group = QGroupBox(f"Ligne de base: {baseline_name}")
            group_layout = QVBoxLayout(group)
            
            # Barre de progression pour cette baseline
            progress_bar = QProgressBar()
            progress_bar.setTextVisible(True)
            progress_bar.setFormat("En attente...")
            group_layout.addWidget(progress_bar)
            
            # Diagramme circulaire
            donut_chart = DonutChartWidget()
            donut_chart.setFixedSize(80, 80)
            group_layout.addWidget(donut_chart)
            
            self.baseline_groups[baseline_name] = {
                'group': group,
                'progress_bar': progress_bar,
                'donut_chart': donut_chart
            }
            
            baseline_layout.addWidget(group)
        
        main_layout.addLayout(baseline_layout)
        
        # Boutons de contrôle
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Démarrer le traitement")
        self.start_button.clicked.connect(self.start_processing)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Arrêter")
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(control_layout)
    
    def start_processing(self):
        """Démarre le traitement des deux lignes de base"""
        try:
            # Créer la configuration
            config = DualBaselineConfig(self.project_manager)
            
            # Configurer les chemins depuis le projet
            if self.project_manager and self.project_manager.current_project:
                config.set_project_paths(self.project_manager.current_project)
            
            # Vérifier que les fichiers existent
            baselines = config.get_baselines()
            if not baselines:
                self.global_progress_bar.setFormat("Erreur: Aucune ligne de base configurée")
                return
            
            # Créer et démarrer le processeur
            self.processor = DualBaselineProcessor(config)
            self.processor.progress_updated.connect(self.update_global_progress)
            self.processor.baseline_progress_updated.connect(self.update_baseline_progress)
            self.processor.quality_updated.connect(self.update_global_quality)
            self.processor.process_finished.connect(self.on_processing_finished)
            self.processor.log_message.connect(self.on_log_message)
            
            # Mettre à jour l'interface
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Démarrer le traitement
            self.processor.start()
            
        except Exception as e:
            self.global_progress_bar.setFormat(f"Erreur: {str(e)}")
    
    def stop_processing(self):
        """Arrête le traitement"""
        if self.processor and self.processor.isRunning():
            self.processor.quit()
            self.processor.wait()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.global_progress_bar.setFormat("Traitement arrêté")
    
    def update_global_progress(self, message: str, progress: int):
        """Met à jour la barre de progression globale"""
        self.global_progress_bar.setValue(progress)
        self.global_progress_bar.setFormat(message)
    
    def update_baseline_progress(self, baseline_name: str, progress: int, message: str):
        """Met à jour la progression d'une ligne de base"""
        if baseline_name in self.baseline_groups:
            group_data = self.baseline_groups[baseline_name]
            group_data['progress_bar'].setValue(progress)
            group_data['progress_bar'].setFormat(message)
    
    def update_global_quality(self, quality_data: Dict[str, int]):
        """Met à jour les diagrammes de qualité"""
        for baseline_name, group_data in self.baseline_groups.items():
            group_data['donut_chart'].update_data(quality_data)
    
    def on_processing_finished(self, results: Dict[str, Any]):
        """Gère la fin du traitement"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if results.get("status") == "success":
            self.global_progress_bar.setFormat("Traitement terminé avec succès")
        else:
            self.global_progress_bar.setFormat(f"Erreur: {results.get('message', 'Inconnue')}")
    
    def on_log_message(self, message: str):
        """Affiche un message de log"""
        print(f"[DualBaseline] {message}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DualBaselineMonitorWidget()
    window.show()
    sys.exit(app.exec_())
