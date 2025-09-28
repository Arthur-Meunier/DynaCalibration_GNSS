#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page GNSS - Interface pour le traitement RTK
Version propre et fonctionnelle
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QCheckBox, QProgressBar, QFrame, QTextEdit,
    QGroupBox, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRectF, QThread
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush

# Imports locaux
from core.calculations.rtk_calculator import RTKCalculator, RTKConfig, RTKFileValidator
from core.project_manager import ProjectManager

# Configuration du logging
logger = logging.getLogger(__name__)

# Stylesheet global pour l'application
APP_STYLESHEET = """
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #555555;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #505050;
}

QPushButton:pressed {
    background-color: #353535;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666666;
}

QComboBox {
    background-color: #404040;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 5px;
    min-width: 120px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #ffffff;
    margin-right: 5px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #666666;
    background-color: #404040;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    border: 2px solid #4CAF50;
    background-color: #4CAF50;
    border-radius: 3px;
}

QProgressBar {
    border: 2px solid #666666;
    border-radius: 5px;
    text-align: center;
    background-color: #404040;
}

QProgressBar::chunk {
    background-color: #4CAF50;
    border-radius: 3px;
}

QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #666666;
    border-radius: 4px;
    padding: 5px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 10px;
}
"""


class SimpleDonutWidget(QWidget):
    """Widget donut simple pour afficher les statistiques de qualité"""
    
    def __init__(self, baseline_name: str = "", parent=None):
        super().__init__(parent)
        self.baseline_name = baseline_name
        self.quality_data = {}
        self.epoch_count = 0
        self.setMinimumSize(200, 200)
        self.setMaximumSize(250, 250)
        
    def update_data(self, quality_data: Dict[str, int], epoch_count: int = 0):
        """Met à jour les données de qualité"""
        self.quality_data = quality_data
        self.epoch_count = epoch_count
        self.update()
    
    def paintEvent(self, event):
        """Dessine le widget donut"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Couleurs pour les différents types de solutions
        colors = {
            'Fix': QColor(76, 175, 80),      # Vert
            'Float': QColor(255, 193, 7),   # Jaune
            'SBAS': QColor(33, 150, 243),    # Bleu
            'DGPS': QColor(156, 39, 176),    # Violet
            'Single': QColor(244, 67, 54),  # Rouge
            'PPP': QColor(255, 152, 0),      # Orange
        }
        
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(center_x, center_y) - 20
        
        # Dessine le cercle de fond
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(center_x - radius, center_y - radius, 
                           radius * 2, radius * 2)
        
        # Dessine les segments de qualité
        if self.quality_data:
            total = sum(self.quality_data.values())
            if total > 0:
                start_angle = 0
                for quality_type, count in self.quality_data.items():
                    if count > 0:
                        span_angle = int(360 * count / total)
                        color = colors.get(quality_type, QColor(128, 128, 128))
                        
                        painter.setPen(QPen(color, 8))
                        painter.drawArc(center_x - radius + 4, center_y - radius + 4,
                                      radius * 2 - 8, radius * 2 - 8,
                                      start_angle * 16, span_angle * 16)
                        start_angle += span_angle
        
        # Dessine le texte au centre
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        
        # Nom de la baseline
        if self.baseline_name:
            painter.drawText(center_x - 50, center_y - 20, 100, 20, 
                           Qt.AlignCenter, self.baseline_name)
        
        # Nombre d'époques
        epoch_text = f"{self.epoch_count} époques"
        painter.drawText(center_x - 50, center_y + 5, 100, 20, 
                       Qt.AlignCenter, epoch_text)


class GnssWidget(QWidget):
    """Widget principal pour le traitement GNSS RTK"""
    
    # Signaux
    sp3_progress_updated = pyqtSignal()
    baseline_progress_updated = pyqtSignal(str, int, str)  # baseline_name, progress, message
    processing_completed = pyqtSignal(dict)  # results
    
    def __init__(self, project_manager: ProjectManager, app_data=None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.app_data = app_data
        
        # Données des fichiers
        self.files = {
            'port_obs': None,
            'bow_obs': None,
            'stbd_obs': None,
            'port_nav': None,
            'bow_nav': None,
            'stbd_nav': None,
            'port_gnav': None,
            'bow_gnav': None,
            'stbd_gnav': None,
            'sp3_file': None,
            'clk_file': None
        }
        
        # Calculateurs RTK
        self.rtk_calculators = []
        self._all_finished_called = False
        
        # Configuration
        self.fixed_point = "Port"  # Point fixe par défaut
        
        self.init_ui()
        self.setStyleSheet(APP_STYLESHEET)
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 15, 20, 20)
        
        # Titre
        title = QLabel("Traitement GNSS RTK")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Configuration des fichiers
        self.create_file_configuration(layout)
        
        # Configuration du traitement
        self.create_processing_configuration(layout)
        
        # Zone de progression dynamique
        self.create_progress_area(layout)
        
        # Boutons de contrôle
        self.create_control_buttons(layout)
        
        # Zone de logs
        self.create_log_area(layout)
        
        # Espaceur flexible
        layout.addStretch()
        
    def create_file_configuration(self, parent_layout):
        """Crée la section de configuration des fichiers"""
        group = QGroupBox("Configuration des fichiers")
        layout = QGridLayout(group)
        
        # Fichiers d'observation
        layout.addWidget(QLabel("Fichiers d'observation:"), 0, 0)
        
        # Port
        layout.addWidget(QLabel("Port:"), 1, 0)
        self.port_obs_btn = QPushButton("Sélectionner")
        self.port_obs_btn.clicked.connect(lambda: self.browse_file('port_obs'))
        layout.addWidget(self.port_obs_btn, 1, 1)
        self.port_obs_label = QLabel("Aucun fichier sélectionné")
        self.port_obs_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self.port_obs_label, 1, 2)
        
        # Bow
        layout.addWidget(QLabel("Bow:"), 2, 0)
        self.bow_obs_btn = QPushButton("Sélectionner")
        self.bow_obs_btn.clicked.connect(lambda: self.browse_file('bow_obs'))
        layout.addWidget(self.bow_obs_btn, 2, 1)
        self.bow_obs_label = QLabel("Aucun fichier sélectionné")
        self.bow_obs_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self.bow_obs_label, 2, 2)
        
        # Stbd
        layout.addWidget(QLabel("Stbd:"), 3, 0)
        self.stbd_obs_btn = QPushButton("Sélectionner")
        self.stbd_obs_btn.clicked.connect(lambda: self.browse_file('stbd_obs'))
        layout.addWidget(self.stbd_obs_btn, 3, 1)
        self.stbd_obs_label = QLabel("Aucun fichier sélectionné")
        self.stbd_obs_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(self.stbd_obs_label, 3, 2)
        
        # Point fixe
        layout.addWidget(QLabel("Point fixe:"), 4, 0)
        self.fixed_point_combo = QComboBox()
        self.fixed_point_combo.addItems(["Port", "Bow", "Stbd"])
        self.fixed_point_combo.setCurrentText("Port")
        self.fixed_point_combo.currentTextChanged.connect(self.on_fixed_point_changed)
        layout.addWidget(self.fixed_point_combo, 4, 1)
        
        parent_layout.addWidget(group)
        
    def create_processing_configuration(self, parent_layout):
        """Crée la section de configuration du traitement"""
        group = QGroupBox("Configuration du traitement")
        layout = QHBoxLayout(group)
        
        # SP3/CLK
        self.sp3_checkbox = QCheckBox("Utiliser SP3/CLK (recommandé)")
        self.sp3_checkbox.setChecked(True)  # Coché par défaut
        layout.addWidget(self.sp3_checkbox)
        
        layout.addStretch()
        
        parent_layout.addWidget(group)
        
    def create_progress_area(self, parent_layout):
        """Crée la zone de progression dynamique"""
        group = QGroupBox("Progression des calculs")
        layout = QVBoxLayout(group)
        
        # Container pour les barres de progression dynamiques
        self.progress_container = QVBoxLayout()
        layout.addLayout(self.progress_container)
        
        parent_layout.addWidget(group)
        
    def create_control_buttons(self, parent_layout):
        """Crée les boutons de contrôle"""
        layout = QHBoxLayout()
        
        # Bouton démarrer
        self.start_btn = QPushButton("🚀 Démarrer les calculs")
        self.start_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold; padding: 10px 20px;")
        self.start_btn.clicked.connect(self.start_calculation)
        layout.addWidget(self.start_btn)
        
        # Bouton arrêter
        self.stop_btn = QPushButton("⏹️ Arrêter")
        self.stop_btn.setStyleSheet("background-color: #f44336; font-weight: bold; padding: 10px 20px;")
        self.stop_btn.clicked.connect(self.stop_calculation)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        layout.addStretch()
        
        parent_layout.addLayout(layout)
        
    def create_log_area(self, parent_layout):
        """Crée la zone de logs"""
        group = QGroupBox("Logs de traitement")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
        parent_layout.addWidget(group)
    
    def browse_file(self, file_type: str):
        """Ouvre le dialogue de sélection de fichier"""
        # Détermine les filtres selon le type de fichier
        if 'obs' in file_type:
            filters = "Fichiers RINEX (*.obs *.25o *.o *.txt);;Tous les fichiers (*.*)"
        elif 'nav' in file_type:
            filters = "Fichiers Navigation (*.nav *.25N *.N);;Tous les fichiers (*.*)"
        elif 'gnav' in file_type:
            filters = "Fichiers GNAV (*.gnav *.25G *.G);;Tous les fichiers (*.*)"
        elif file_type == 'sp3_file':
            filters = "Fichiers SP3 (*.sp3 *.SP3);;Tous les fichiers (*.*)"
        elif file_type == 'clk_file':
            filters = "Fichiers CLK (*.clk *.CLK);;Tous les fichiers (*.*)"
        else:
            filters = "Tous les fichiers (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner le fichier {file_type}", "", filters
        )
        
        if file_path:
            self.select_file(file_type, file_path)
            
    def select_file(self, file_type: str, file_path: str):
        """Sélectionne et valide un fichier"""
        try:
            # Validation adaptative selon le type de fichier
            if 'obs' in file_type:
                # Validation RINEX pour les fichiers d'observation
                if not self._is_rinex_file(Path(file_path)):
                    QMessageBox.warning(self, "Format de fichier incorrect", 
                                      f"Le fichier sélectionné n'est pas un fichier RINEX valide.\n\n"
                                      f"RTKLIB nécessite des fichiers RINEX (.obs, .25o, .nav, .25n, etc.)\n"
                                      f"Les fichiers CSV ou TXT ne sont pas supportés.\n\n"
                                      f"Fichier: {Path(file_path).name}")
                    return
                
                # Validation complète pour les fichiers d'observation
                validator = RTKFileValidator()
                is_valid, files_dict = validator.validate_rinex_files(Path(file_path))
                if not is_valid:
                    QMessageBox.warning(self, "Fichiers associés manquants", 
                                      f"Le fichier RINEX est valide mais ses fichiers associés sont manquants.\n\n"
                                      f"Fichiers requis: .nav (navigation), .gnav (Galileo)\n"
                                      f"Fichier: {Path(file_path).name}")
                    # Permettre quand même la sélection, les fichiers NAV peuvent être trouvés ailleurs
            else:
                # Validation simple pour les autres fichiers (existence)
                if not os.path.exists(file_path):
                    QMessageBox.warning(self, "Erreur", f"Le fichier {file_path} n'existe pas.")
                    return
            
            # Sauvegarde du fichier
            self.files[file_type] = file_path
            
            # Mise à jour de l'interface
            self.update_file_labels()
            
            # Recherche automatique des fichiers associés
            self.find_associated_files(file_type, file_path)
            
            logger.info(f"✅ Fichier {file_type} sélectionné: {Path(file_path).name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sélection du fichier {file_type}: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sélection du fichier: {e}")
    
    def _is_rinex_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier est un fichier RINEX valide"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                # Un fichier RINEX commence par une version et un type
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
            
    def find_associated_files(self, file_type: str, file_path: str):
        """Recherche automatiquement les fichiers associés"""
        base_path = Path(file_path).parent
        base_name = Path(file_path).stem
        
        if 'obs' in file_type:
            # Recherche des fichiers NAV et GNAV associés
            nav_file = self.find_nav_file(file_path)
            gnav_file = self.find_gnav_file(file_path)
            
            if nav_file:
                file_key = file_type.replace('obs', 'nav')
                self.files[file_key] = nav_file
                logger.info(f"✅ Fichier NAV associé trouvé: {Path(nav_file).name}")
                
            if gnav_file:
                file_key = file_type.replace('obs', 'gnav')
                self.files[file_key] = gnav_file
                logger.info(f"✅ Fichier GNAV associé trouvé: {Path(gnav_file).name}")
                
        elif file_type == 'sp3_file':
            # Recherche du fichier CLK associé
            clk_file = self.find_clk_file(file_path)
            if clk_file:
                self.files['clk_file'] = clk_file
                logger.info(f"✅ Fichier CLK associé trouvé: {Path(clk_file).name}")
                
        self.update_file_labels()
        
    def find_nav_file(self, obs_file_path: str) -> Optional[str]:
        """Recherche le fichier NAV correspondant"""
        base_path = Path(obs_file_path).parent
        base_name = Path(obs_file_path).stem
        
        # Patterns possibles pour les fichiers NAV
        nav_patterns = [
            f"{base_name}.nav",
            f"{base_name}.25N",
            f"{base_name}.N",
            f"{base_name.replace('.25o', '.25N')}",
            f"{base_name.replace('.o', '.nav')}"
        ]
        
        for pattern in nav_patterns:
            nav_path = base_path / pattern
            if nav_path.exists():
                return str(nav_path)
                
        return None
        
    def find_gnav_file(self, obs_file_path: str) -> Optional[str]:
        """Recherche le fichier GNAV correspondant"""
        base_path = Path(obs_file_path).parent
        base_name = Path(obs_file_path).stem
        
        # Patterns possibles pour les fichiers GNAV
        gnav_patterns = [
            f"{base_name}.gnav",
            f"{base_name}.25G",
            f"{base_name}.G",
            f"{base_name.replace('.25o', '.25G')}",
            f"{base_name.replace('.o', '.gnav')}"
        ]
        
        for pattern in gnav_patterns:
            gnav_path = base_path / pattern
            if gnav_path.exists():
                return str(gnav_path)
                
        return None
        
    def find_clk_file(self, sp3_file_path: str) -> Optional[str]:
        """Recherche le fichier CLK correspondant"""
        base_path = Path(sp3_file_path).parent
        base_name = Path(sp3_file_path).stem
        
        # Patterns possibles pour les fichiers CLK
        clk_patterns = [
            f"{base_name.replace('.sp3', '.clk')}",
            f"{base_name.replace('.SP3', '.CLK')}",
            f"{base_name}.clk",
            f"{base_name}.CLK"
        ]
        
        for pattern in clk_patterns:
            clk_path = base_path / pattern
            if clk_path.exists():
                return str(clk_path)
                
        return None
        
    def find_sp3_clk_files(self, obs_file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Recherche les fichiers SP3 et CLK dans le répertoire"""
        base_path = Path(obs_file_path).parent
        
        # Recherche des fichiers SP3
        sp3_files = list(base_path.glob("*.sp3")) + list(base_path.glob("*.SP3"))
        sp3_file = str(sp3_files[0]) if sp3_files else None
        
        # Recherche des fichiers CLK
        clk_files = list(base_path.glob("*.clk")) + list(base_path.glob("*.CLK"))
        clk_file = str(clk_files[0]) if clk_files else None
        
        return sp3_file, clk_file
        
    def update_file_labels(self):
        """Met à jour les labels des fichiers sélectionnés"""
        # Port
        if self.files['port_obs']:
            self.port_obs_label.setText(Path(self.files['port_obs']).name)
            self.port_obs_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.port_obs_label.setText("Aucun fichier sélectionné")
            self.port_obs_label.setStyleSheet("color: #888888; font-style: italic;")
            
        # Bow
        if self.files['bow_obs']:
            self.bow_obs_label.setText(Path(self.files['bow_obs']).name)
            self.bow_obs_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.bow_obs_label.setText("Aucun fichier sélectionné")
            self.bow_obs_label.setStyleSheet("color: #888888; font-style: italic;")
            
        # Stbd
        if self.files['stbd_obs']:
            self.stbd_obs_label.setText(Path(self.files['stbd_obs']).name)
            self.stbd_obs_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.stbd_obs_label.setText("Aucun fichier sélectionné")
            self.stbd_obs_label.setStyleSheet("color: #888888; font-style: italic;")
            
    def on_fixed_point_changed(self, fixed_point: str):
        """Gère le changement du point fixe"""
        self.fixed_point = fixed_point
        logger.info(f"Point fixe changé: {fixed_point}")
    
    def start_calculation(self):
        """Démarre les calculs RTK"""
        try:
            # Validation des fichiers requis
            if not self.validate_files():
                return
            
            logger.info("🚀 Démarrage des calculs GNSS...")
            
            # Détermine les baselines à calculer
            baselines = self.determine_baselines()
            
            if not baselines:
                QMessageBox.warning(self, "Erreur", "Aucune baseline valide trouvée.")
                return
            
            # Démarre les calculs parallèles
            self._start_parallel_calculations(baselines)
            
            # Met à jour l'interface
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage des calculs: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage: {e}")
            
    def validate_files(self) -> bool:
        """Valide que tous les fichiers requis sont présents"""
        required_files = ['port_obs', 'bow_obs', 'stbd_obs']
        
        for file_type in required_files:
            if not self.files[file_type]:
                QMessageBox.warning(self, "Fichiers manquants", 
                                  f"Le fichier {file_type} est requis.")
                return False
                
        return True
        
    def determine_baselines(self) -> List[Dict]:
        """Détermine les baselines à calculer avec logs détaillés"""
        baselines = []
        
        # Détermine les points rover (non-fixes)
        all_points = ['Port', 'Bow', 'Stbd']
        rover_points = [p for p in all_points if p != self.fixed_point]
        
        logger.info(f"🎯 Configuration des baselines:")
        logger.info(f"   Point fixe: {self.fixed_point}")
        logger.info(f"   Points rover: {', '.join(rover_points)}")
        
        # Crée les baselines
        for rover in rover_points:
            baseline = {
                'name': f"{self.fixed_point}→{rover}",
                'fixed_point': self.fixed_point,
                'rover_point': rover,
                'fixed_obs': self.files[f'{self.fixed_point.lower()}_obs'],
                'rover_obs': self.files[f'{rover.lower()}_obs'],
                'fixed_nav': self.files.get(f'{self.fixed_point.lower()}_nav'),
                'rover_nav': self.files.get(f'{rover.lower()}_nav'),
                'fixed_gnav': self.files.get(f'{self.fixed_point.lower()}_gnav'),
                'rover_gnav': self.files.get(f'{rover.lower()}_gnav')
            }
            baselines.append(baseline)
            
            # Log détaillé de la baseline
            logger.info(f"   📋 Baseline {baseline['name']}:")
            logger.info(f"      Base OBS: {Path(baseline['fixed_obs']).name}")
            logger.info(f"      Rover OBS: {Path(baseline['rover_obs']).name}")
            
        logger.info(f"✅ {len(baselines)} baselines configurées")
        return baselines
        
    def _start_parallel_calculations(self, baselines: List[Dict]):
        """Démarre les calculs parallèles pour toutes les baselines"""
        self.rtk_calculators = []
        self._all_finished_called = False
        
        # Crée les barres de progression dynamiques
        self._create_dynamic_progress_bars(baselines)
        
        # Démarre chaque calculateur
        for i, baseline in enumerate(baselines):
            config = self._create_rtk_config(baseline, i)
            calculator = RTKCalculator(config)
            calculator.baseline_name = baseline['name']
            calculator.baseline_index = i
            
            # Connecte les signaux
            self._connect_calculator_signals(calculator, i, baseline['name'])
            
            # Démarre le calculateur
            calculator.start()
            self.rtk_calculators.append(calculator)
            
        logger.info(f"✅ {len(baselines)} calculateurs RTK démarrés")
        
    def _create_rtk_config(self, baseline: Dict, index: int) -> RTKConfig:
        """Crée la configuration RTK pour une baseline avec détection automatique"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"export/rtk_{baseline['name'].replace('→', '_to_')}_{timestamp}.pos"
        
        config = RTKConfig()
        
        # Configure les fichiers principaux
        config.rover_obs_file = baseline['rover_obs']
        config.base_obs_file = baseline['fixed_obs']
        config.output_file = output_file
        config.working_dir = Path("RTKlib")
        
        # Détection automatique des fichiers associés
        self._detect_associated_files(config, baseline)
        
        # Configuration SP3/CLK
        config.use_sp3_clk = self.sp3_checkbox.isChecked()
        
        # Log de la configuration
        logger.info(f"🔧 Configuration {baseline['name']}:")
        logger.info(f"   Rover OBS: {Path(baseline['rover_obs']).name}")
        logger.info(f"   Base OBS: {Path(baseline['fixed_obs']).name}")
        if config.rover_nav_file:
            logger.info(f"   Rover NAV: {Path(config.rover_nav_file).name}")
        if config.rover_gnav_file:
            logger.info(f"   Rover GNAV: {Path(config.rover_gnav_file).name}")
        logger.info(f"   SP3/CLK: {'Activé' if config.use_sp3_clk else 'Désactivé'}")
        
        return config
    
    def _detect_associated_files(self, config: RTKConfig, baseline: Dict):
        """Détecte automatiquement les fichiers NAV/GNAV associés"""
        rover_obs_path = Path(baseline['rover_obs'])
        base_obs_path = Path(baseline['fixed_obs'])
        
        # Détection des fichiers NAV
        rover_nav = self._find_nav_file(rover_obs_path)
        if rover_nav:
            config.rover_nav_file = str(rover_nav)
            logger.info(f"   ✅ NAV rover détecté: {rover_nav.name}")
        else:
            logger.warning(f"   ⚠️ NAV rover non trouvé pour {rover_obs_path.name}")
        
        # Détection des fichiers GNAV
        rover_gnav = self._find_gnav_file(rover_obs_path)
        if rover_gnav:
            config.rover_gnav_file = str(rover_gnav)
            logger.info(f"   ✅ GNAV rover détecté: {rover_gnav.name}")
        else:
            logger.warning(f"   ⚠️ GNAV rover non trouvé pour {rover_obs_path.name}")
    
    def _find_nav_file(self, obs_file_path: Path) -> Optional[Path]:
        """Recherche le fichier NAV correspondant"""
        base_path = obs_file_path.parent
        base_name = obs_file_path.stem
        
        # Patterns possibles pour les fichiers NAV
        nav_patterns = [
            f"{base_name}.nav",
            f"{base_name}.25N",
            f"{base_name}.N",
            f"{base_name.replace('.25o', '.25N')}",
            f"{base_name.replace('.o', '.nav')}"
        ]
        
        for pattern in nav_patterns:
            nav_path = base_path / pattern
            if nav_path.exists():
                return nav_path
                
        return None
    
    def _find_gnav_file(self, obs_file_path: Path) -> Optional[Path]:
        """Recherche le fichier GNAV correspondant"""
        base_path = obs_file_path.parent
        base_name = obs_file_path.stem
        
        # Patterns possibles pour les fichiers GNAV
        gnav_patterns = [
            f"{base_name}.gnav",
            f"{base_name}.25G",
            f"{base_name}.G",
            f"{base_name.replace('.25o', '.25G')}",
            f"{base_name.replace('.o', '.gnav')}"
        ]
        
        for pattern in gnav_patterns:
            gnav_path = base_path / pattern
            if gnav_path.exists():
                return gnav_path
                
        return None
        
    def _create_dynamic_progress_bars(self, baselines: List[Dict]):
        """Crée les barres de progression dynamiques"""
        # Nettoie le container existant
        for i in reversed(range(self.progress_container.count())):
            child = self.progress_container.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        # Crée les nouvelles barres
        for i, baseline in enumerate(baselines):
            # Container horizontal pour chaque baseline
            baseline_layout = QHBoxLayout()
            baseline_layout.setSpacing(10)
            
            # Label de la baseline
            label = QLabel(f"{baseline['name']}:")
            label.setMinimumWidth(120)
            label.setStyleSheet("font-weight: bold;")
            baseline_layout.addWidget(label)
            
            # Barre de progression
            progress_bar = QProgressBar()
            progress_bar.setMinimumWidth(200)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #666666;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #404040;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
            """)
            baseline_layout.addWidget(progress_bar)
            
            # Widget donut
            donut = SimpleDonutWidget(baseline['name'])
            baseline_layout.addWidget(donut)
            
            # Label de statut
            status_label = QLabel("En attente...")
            status_label.setMinimumWidth(150)
            status_label.setStyleSheet("color: #888888; font-style: italic;")
            baseline_layout.addWidget(status_label)
            
            # Ajoute au container principal
            self.progress_container.addLayout(baseline_layout)
            
            # Stocke les références pour mise à jour
            setattr(self, f'progress_bar_{i}', progress_bar)
            setattr(self, f'donut_{i}', donut)
            setattr(self, f'status_label_{i}', status_label)
            
    def _connect_calculator_signals(self, calculator: RTKCalculator, index: int, baseline_name: str):
        """Connecte les signaux d'un calculateur"""
        # Gestionnaire de progression (message, pourcentage)
        def progress_handler(message, progress):
            self.update_parallel_progress(index, baseline_name, progress, message)
        calculator.progress_updated.connect(progress_handler)
        
        # Gestionnaire de qualité
        def quality_handler(quality_data):
            self.update_parallel_quality(index, baseline_name, quality_data)
        calculator.quality_updated.connect(quality_handler)
        
        # Gestionnaire de fin (code de retour seulement)
        def finished_handler(return_code):
            success = return_code == 0
            message = "Terminé avec succès" if success else f"Erreur (code: {return_code})"
            self.on_parallel_baseline_finished(index, baseline_name, success, message)
        calculator.process_finished.connect(finished_handler)
        
        # Gestionnaire de logs
        def log_handler(message):
            self.add_log_message(f"[{baseline_name}] {message}")
        calculator.log_message.connect(log_handler)
        
    def update_parallel_progress(self, index: int, baseline_name: str, progress: int, message: str):
        """Met à jour la progression d'une baseline"""
        progress_bar = getattr(self, f'progress_bar_{index}', None)
        status_label = getattr(self, f'status_label_{index}', None)
        
        if progress_bar:
            progress_bar.setValue(progress)
            
        if status_label:
            status_label.setText(message)
            status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
        # Émet le signal pour le menu vertical
        self.baseline_progress_updated.emit(baseline_name, progress, message)
        
    def update_parallel_quality(self, index: int, baseline_name: str, quality_data: Dict):
        """Met à jour les données de qualité d'une baseline"""
        donut = getattr(self, f'donut_{index}', None)
        
        if donut:
            donut.update_data(quality_data)
            
    def on_parallel_baseline_finished(self, index: int, baseline_name: str, success: bool, message: str):
        """Gère la fin d'un calcul de baseline"""
        status_label = getattr(self, f'status_label_{index}', None)
        
        if status_label:
            if success:
                status_label.setText("✅ Terminé")
                status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                status_label.setText("❌ Erreur")
                status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                
        logger.info(f"✅ {baseline_name} terminé avec succès" if success else f"❌ {baseline_name} échoué")
        
        # Vérifie si tous les calculs sont terminés
        self._check_all_finished()
        
    def _check_all_finished(self):
        """Vérifie si tous les calculs sont terminés"""
        if not self.rtk_calculators:
            return
            
        # Vérifie si tous les calculateurs sont terminés
        all_finished = all(not calc.isRunning() for calc in self.rtk_calculators)
        
        if all_finished and not self._all_finished_called:
            self._all_finished_called = True
            self._on_all_parallel_baselines_finished()
            
    def _on_all_parallel_baselines_finished(self):
        """Gère la fin de tous les calculs parallèles"""
        logger.info("🎉 Tous les calculs RTK terminés")
        
        # Sauvegarde les fichiers .pos dans le projet
        self._save_pos_files_to_project()
        
        # Prépare les résultats
        results = {
            'success': True,
            'baselines': len(self.rtk_calculators),
            'timestamp': datetime.now().isoformat()
        }
        
        # Émet le signal de fin de traitement
        self.processing_completed.emit(results)
        
        # Met à jour l'interface
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Programme la navigation automatique vers la page post-calcul
        QTimer.singleShot(2000, lambda: self.trigger_auto_navigation(results))
        
    def _save_pos_files_to_project(self):
        """Sauvegarde les chemins des fichiers .pos dans le projet"""
        try:
            pos_files = []
            export_dir = Path("export")
            
            # Recherche les fichiers .pos
            if export_dir.exists():
                pos_files.extend([str(f) for f in export_dir.glob("*.pos")])
                
            # Si pas trouvé, cherche dans export/export/
            if not pos_files:
                export_subdir = export_dir / "export"
                if export_subdir.exists():
                    pos_files.extend([str(f) for f in export_subdir.glob("*.pos")])
                    
            if pos_files:
                self.project_manager.add_gnss_pos_files(pos_files)
                logger.info(f"✅ {len(pos_files)} fichiers .pos sauvegardés dans le projet")
            else:
                logger.warning("⚠️ Aucun fichier .pos trouvé à sauvegarder")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des fichiers .pos: {e}")
            
    def trigger_auto_navigation(self, results: Dict):
        """Déclenche la navigation automatique vers la page de finalisation"""
        try:
            if self.project_manager.should_navigate_to_finalization():
                logger.info("🔄 Navigation automatique vers la page de finalisation...")
                # Le signal processing_completed sera écouté par main.py
                # qui déclenchera la navigation
            else:
                logger.info("ℹ️ Navigation automatique non requise")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la navigation automatique: {e}")
    
    def stop_calculation(self):
        """Arrête tous les calculs en cours"""
        logger.info("⏹️ Arrêt des calculs RTK...")
        
        # Arrête tous les calculateurs
        for calculator in self.rtk_calculators:
            if calculator.isRunning():
                calculator.stop()
                
        # Remet à zéro les barres de progression
        for i in range(len(self.rtk_calculators)):
            progress_bar = getattr(self, f'progress_bar_{i}', None)
            donut = getattr(self, f'donut_{i}', None)
            status_label = getattr(self, f'status_label_{i}', None)
            
            if progress_bar:
                progress_bar.setValue(0)
            if donut:
                donut.update_data({})
            if status_label:
                status_label.setText("Arrêté")
                status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                
        # Met à jour l'interface
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Nettoie les calculateurs
        self.rtk_calculators = []
        self._all_finished_called = False
        
        logger.info("✅ Calculs RTK arrêtés")
        
    def add_log_message(self, message: str):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        self.log_text.append(log_message)
        
        # Scroll vers le bas
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def set_app_data(self, app_data):
        """Définit les données de l'application"""
        self.app_data = app_data
        
    def load_project_data(self):
        """Charge les données du projet"""
        if self.project_manager and self.project_manager.current_project:
            # Charge les métadonnées GNSS du projet
            gnss_metadata = self.project_manager.get_gnss_metadata()
            if gnss_metadata:
                logger.info("✅ Métadonnées GNSS chargées depuis le projet")
            else:
                logger.info("ℹ️ Aucune métadonnée GNSS trouvée dans le projet")
