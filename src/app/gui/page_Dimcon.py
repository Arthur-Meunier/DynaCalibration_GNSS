# src/ui/page_Dimcon.py - Version thème sombre avec vue 3D maximisée

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QGroupBox, QFormLayout, QHeaderView, QSplitter,
    QLineEdit, QMessageBox, QCheckBox, QDialog, QFrame,
    QGridLayout, QSizePolicy, QScrollArea, QToolButton
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, pyqtSlot, QPoint
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QPalette, QDoubleValidator

import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from functools import partial

# Import du gestionnaire de projet
from core.project_manager import ProjectManager

# Configuration simple du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DIMCON - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FloatingCoordinatesPanel(QWidget):
    """
    Panneau flottant ultra-compact pour la saisie des coordonnées
    """
    coordinates_changed = pyqtSignal(str, str, float)  # point_id, coord, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setObjectName("FloatingPanel")
        
        # Position par défaut
        self.default_position = QPoint(10, 10)
        
        # Données des points
        self.points_data = {
            "Bow": {"X": -0.269, "Y": -64.232, "Z": 10.888},
            "Port": {"X": -9.347, "Y": -27.956, "Z": 13.491},
            "Stb": {"X": 9.392, "Y": -27.827, "Z": 13.506}
        }
        
        self.line_edits = {}
        self.setup_ui()
        self.apply_dark_style()
        
        # Permettre le déplacement
        self.dragging = False
        self.drag_position = QPoint()
        
        # Mode réduit par défaut pour économiser l'espace
        self.is_minimized = False
    
    def setup_ui(self):
        """Interface ultra-compacte du panneau flottant"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        
        # === HEADER MINIMAL ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        # Titre compact
        title_label = QLabel("📐 DIMCON")
        title_label.setFont(QFont("Arial", 9, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; background: transparent;")
        
        # Bouton de réduction/fermeture
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("−")
        self.toggle_btn.setFixedSize(16, 16)
        self.toggle_btn.clicked.connect(self.toggle_panel)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        
        main_layout.addLayout(header_layout)
        
        # === CONTENU PRINCIPAL ===
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(2)
        
        # Grille ultra-compacte des coordonnées
        coords_widget = self.create_compact_coordinates_widget()
        content_layout.addWidget(coords_widget)
        
        # Métriques en une ligne
        metrics_widget = self.create_inline_metrics_widget()
        content_layout.addWidget(metrics_widget)
        
        # Statut minimal
        status_widget = self.create_minimal_status_widget()
        content_layout.addWidget(status_widget)
        
        main_layout.addWidget(self.content_widget)
        
        # Taille ultra-compacte
        self.resize(240, 180)
    
    def create_compact_coordinates_widget(self):
        """Grille ultra-compacte pour les coordonnées"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # Configuration des points avec couleurs
        point_config = {
            "Bow": {"color": "#e74c3c", "name": "🔴", "icon": "P"},
            "Port": {"color": "#f39c12", "name": "🟠", "icon": "B"},
            "Stb": {"color": "#3498db", "name": "🔵", "icon": "T"}
        }
        
        for point_id in ["Bow", "Port", "Stb"]:
            config = point_config[point_id]
            
            # Frame compacte pour chaque point
            point_frame = QFrame()
            point_frame.setFrameStyle(QFrame.Box)
            point_frame.setFixedHeight(35)
            point_frame.setStyleSheet(f"""
                QFrame {{
                    border: 1px solid {config["color"]};
                    border-radius: 3px;
                    background-color: rgba({int(config["color"][1:3], 16)}, {int(config["color"][3:5], 16)}, {int(config["color"][5:7], 16)}, 0.1);
                }}
            """)
            
            point_layout = QHBoxLayout(point_frame)
            point_layout.setContentsMargins(3, 2, 3, 2)
            point_layout.setSpacing(2)
            
            # Label du point minimal
            point_label = QLabel(config["name"])
            point_label.setFont(QFont("Arial", 8, QFont.Bold))
            point_label.setFixedWidth(12)
            point_layout.addWidget(point_label)
            
            # Coordonnées X, Y, Z en ligne
            self.line_edits[point_id] = {}
            
            for coord in ['X', 'Y', 'Z']:
                # Champ de saisie ultra-compact
                line_edit = QLineEdit()
                line_edit.setText(f"{self.points_data[point_id][coord]:.3f}")
                line_edit.setFixedWidth(50)
                line_edit.setFixedHeight(20)
                
                # Validateur
                validator = QDoubleValidator(-500.0, 500.0, 6)
                validator.setNotation(QDoubleValidator.StandardNotation)
                line_edit.setValidator(validator)
                
                # Connexions
                line_edit.editingFinished.connect(
                    partial(self.on_coordinate_editing_finished, point_id, coord)
                )
                
                self.line_edits[point_id][coord] = line_edit
                point_layout.addWidget(line_edit)
            
            layout.addWidget(point_frame)
        
        return widget
    
    def create_inline_metrics_widget(self):
        """Métriques en une seule ligne compacte"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Titre mini
        title = QLabel("📊")
        title.setFont(QFont("Arial", 8))
        layout.addWidget(title)
        
        # Labels compacts pour les métriques principales
        self.metrics_labels = {}
        
        metrics_config = [
            ("triangle_area", "A:", "0.00"),
            ("port_stb_distance", "P-S:", "0.00")
        ]
        
        for key, label_text, default_value in metrics_config:
            # Label titre
            title_lbl = QLabel(label_text)
            title_lbl.setStyleSheet("color: #bdc3c7; font-size: 7px;")
            layout.addWidget(title_lbl)
            
            # Label valeur
            value_lbl = QLabel(default_value)
            value_lbl.setStyleSheet("color: #ffffff; font-family: monospace; font-size: 7px; font-weight: bold;")
            value_lbl.setFixedWidth(30)
            
            self.metrics_labels[key] = value_lbl
            layout.addWidget(value_lbl)
        
        layout.addStretch()
        return widget
    
    def create_minimal_status_widget(self):
        """Statut ultra-minimal"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Indicateur de validation compact
        self.validation_indicator = QLabel("❌")
        self.validation_indicator.setFixedSize(16, 16)
        self.validation_indicator.setAlignment(Qt.AlignCenter)
        self.validation_indicator.setStyleSheet("""
            QLabel {
                background-color: #dc3545;
                color: white;
                border-radius: 8px;
                font-size: 8px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.validation_indicator)
        
        # Status text minimal
        self.status_text = QLabel("Non validé")
        self.status_text.setStyleSheet("color: #bdc3c7; font-size: 7px;")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        return widget
    
    def apply_dark_style(self):
        """Style sombre ultra-compact"""
        self.setStyleSheet("""
            #FloatingPanel {
                background-color: rgba(35, 35, 38, 250);
                border: 1px solid #555555;
                border-radius: 6px;
            }
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #444444;
                border-radius: 2px;
                padding: 1px 3px;
                color: #ffffff;
                font-family: monospace;
                font-size: 8px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #007acc;
                background-color: #383838;
            }
            QLineEdit:hover {
                border-color: #666666;
            }
            QToolButton {
                background-color: #555555;
                border: none;
                color: white;
                font-weight: bold;
                border-radius: 2px;
                font-size: 10px;
            }
            QToolButton:hover {
                background-color: #777777;
            }
        """)
    
    def on_coordinate_editing_finished(self, point_id, coord):
        """Validation et émission du signal"""
        line_edit = self.line_edits[point_id][coord]
        text = line_edit.text().strip()
        
        try:
            value = float(text) if text else 0.0
            self.points_data[point_id][coord] = value
            
            # Format compact à 3 décimales
            line_edit.setText(f"{value:.3f}")
            
            # Émettre le signal
            self.coordinates_changed.emit(point_id, coord, value)
            
        except ValueError:
            # Restaurer la valeur précédente
            old_value = self.points_data[point_id][coord]
            line_edit.setText(f"{old_value:.3f}")
    
    def update_metrics(self, metrics):
        """Met à jour les métriques compactes"""
        try:
            self.metrics_labels["triangle_area"].setText(f"{metrics['triangle_area']:.1f}")
            self.metrics_labels["port_stb_distance"].setText(f"{metrics['port_stb_distance']:.1f}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur mise à jour métriques: {e}")
    
    def update_validation_status(self, is_validated):
        """Met à jour le statut compact"""
        if is_validated:
            self.validation_indicator.setText("✅")
            self.validation_indicator.setStyleSheet("""
                QLabel {
                    background-color: #28a745;
                    color: white;
                    border-radius: 8px;
                    font-size: 8px;
                    font-weight: bold;
                }
            """)
            self.status_text.setText("Validé")
        else:
            self.validation_indicator.setText("❌")
            self.validation_indicator.setStyleSheet("""
                QLabel {
                    background-color: #dc3545;
                    color: white;
                    border-radius: 8px;
                    font-size: 8px;
                    font-weight: bold;
                }
            """)
            self.status_text.setText("Non validé")
    
    def set_points_data(self, points_data):
        """Met à jour les données depuis l'extérieur"""
        self.points_data = points_data.copy()
        
        # Mettre à jour les line edits
        for point_id in ["Bow", "Port", "Stb"]:
            for coord in ['X', 'Y', 'Z']:
                if point_id in self.points_data and coord in self.points_data[point_id]:
                    value = self.points_data[point_id][coord]
                    self.line_edits[point_id][coord].setText(f"{value:.3f}")
    
    def toggle_panel(self):
        """Réduit/agrandit le panneau"""
        if self.content_widget.isVisible():
            self.content_widget.hide()
            self.toggle_btn.setText("+")
            self.resize(240, 25)  # Hauteur minimale
            self.is_minimized = True
        else:
            self.content_widget.show()
            self.toggle_btn.setText("−")
            self.resize(240, 180)
            self.is_minimized = False
    
    # Méthodes de déplacement inchangées
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()


class DimconWidget(QWidget):
    """
    Page DIMCON avec vue 3D maximisée et panneau flottant
    Thème sombre cohérent avec le reste de l'application
    """
    
    # Signaux pour communication avec l'application
    dimcon_data_changed = pyqtSignal(dict)
    validation_completed = pyqtSignal(dict)
    
    def __init__(self, app_data=None, parent=None):
        super().__init__(parent)
        self.setObjectName("DimconWidget")
        
        logger.info("🚀 Initialisation page DIMCON avec thème sombre")
        
        # === CONNEXIONS SYSTÈME ===
        self.app_data = app_data
        self.project_manager = ProjectManager.instance() if ProjectManager else None
        
        # === DONNÉES ===
        self.points_data = {
            "Bow": {"X": -0.269, "Y": -64.232, "Z": 10.888},
            "Port": {"X": -9.347, "Y": -27.956, "Z": 13.491},
            "Stb": {"X": 9.392, "Y": -27.827, "Z": 13.506}
        }
        
        self.is_validated = False
        self.validation_history = []
        
        # === INTERFACE ===
        self.setup_ui()
        self.setup_connections()
        self.load_from_app_data()
        self.apply_dark_theme()
        
        logger.info("✅ Page DIMCON initialisée avec thème sombre")
    
    def setup_ui(self):
        """Interface avec vue 3D maximisée et panneau flottant"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === HEADER COMPACT ===
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # === VUE 3D MAXIMISÉE ===
        self.view_3d_container = QWidget()
        view_layout = QVBoxLayout(self.view_3d_container)
        view_layout.setContentsMargins(2, 2, 2, 2)
        view_layout.setSpacing(0)
        
        # Configuration de la vue 3D
        self.setup_3d_view()
        view_layout.addWidget(self.gl_widget)
        
        # Contrôles de vue en bas
        controls_layout = self.create_3d_controls()
        view_layout.addLayout(controls_layout)
        
        main_layout.addWidget(self.view_3d_container, 1)
        
        # === PANNEAU FLOTTANT POSITIONNÉ OPTIMALEMENT ===
        self.floating_panel = FloatingCoordinatesPanel(self)
        self.floating_panel.move(10, 50)  # Position haute à gauche, plus proche du bord
        self.floating_panel.show()
        
        # === FOOTER STATUS ===
        footer_layout = self.create_footer()
        main_layout.addLayout(footer_layout)
    
    def create_header(self):
        """Crée l'en-tête ultra-compact"""
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 4, 6, 4)  # Marges réduites
        layout.setSpacing(10)
        
        # Titre compact
        title_layout = QHBoxLayout()
        title_icon = QLabel("📐")
        title_icon.setFont(QFont("Arial", 12))
        
        title_text = QLabel("DIMCON")
        title_text.setFont(QFont("Arial", 11, QFont.Bold))
        title_text.setStyleSheet("color: #ffffff;")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Contrôles d'affichage compacts
        self.show_boat_cb = QCheckBox("🚢 Navire")
        self.show_boat_cb.setChecked(True)
        self.show_boat_cb.stateChanged.connect(self.update_3d_view)
        
        
        
        # Boutons d'action compacts
        reset_btn = QPushButton("🔄")
        reset_btn.setToolTip("Restaurer les valeurs par défaut")
        reset_btn.setFixedSize(32, 28)
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.validate_btn = QPushButton("✅ Valider")
        self.validate_btn.setObjectName("validateButton")
        self.validate_btn.setFixedHeight(28)
        self.validate_btn.clicked.connect(self.validate_and_save)
        
        layout.addWidget(self.show_boat_cb)
        
        layout.addWidget(reset_btn)
        layout.addWidget(self.validate_btn)
        
        return layout
    
    def create_3d_controls(self):
        """Crée les contrôles compacts pour la vue 3D"""
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 2, 6, 2)  # Marges très réduites
        layout.setSpacing(6)
        
        # Info compact sur les contrôles
        info_label = QLabel("💡 Clic droit: rotation | Molette: zoom")
        info_label.setStyleSheet("color: #bdc3c7; font-size: 8px; font-style: italic;")
        
        layout.addWidget(info_label)
        layout.addStretch()
        
        # Boutons de vue compacts
        views = [
            ("🔭", lambda: self.set_3d_view(distance=140, elevation=25, azimuth=-30)),
            ("⬆️", lambda: self.set_3d_view(distance=110, elevation=90, azimuth=0)),
            ("➡️", lambda: self.set_3d_view(distance=110, elevation=5, azimuth=0)),
            ("🎯", self.reset_camera_view)
        ]
        
        tooltips = ["Vue générale", "Vue dessus", "Vue côté", "Centrer"]
        
        for i, (text, callback) in enumerate(views):
            btn = QPushButton(text)
            btn.setFixedSize(24, 24)  # Boutons carrés compacts
            btn.setToolTip(tooltips[i])
            btn.clicked.connect(callback)
            layout.addWidget(btn)
        
        return layout
    
    def reset_camera_view(self):
        """Recentre la caméra sur les points DIMCON - Version corrigée"""
        try:
            # Calculer le centre des points DIMCON
            points = []
            for point_data in self.points_data.values():
                points.append([point_data["X"], point_data["Y"], point_data["Z"]])
            
            if points:
                points_array = np.array(points)
                center = np.mean(points_array, axis=0)
                
                # Calculer une distance appropriée
                max_range = np.max(np.ptp(points_array, axis=0))
                optimal_distance = max(120, max_range * 2.5)
                
                # CORRECTION: Ne pas passer le paramètre pos, juste ajuster la distance
                # PyQtGraph gère automatiquement le centrage
                self.gl_widget.setCameraPosition(
                    distance=optimal_distance,
                    elevation=25,
                    azimuth=-30
                )
                
                logger.info(f"📍 Vue recentrée à distance {optimal_distance:.1f}")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur recentrage vue: {e}")
            # Fallback vers vue par défaut
            self.set_3d_view(distance=140, elevation=25, azimuth=-30)
    
    def create_footer(self):
        """Crée le pied de page ultra-compact"""
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 2, 6, 2)  # Marges très réduites
        layout.setSpacing(10)
        
        # Statut général compact
        self.status_label = QLabel("📊 Prêt")
        self.status_label.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 9px;")
        
        # Info projet compact
        self.project_label = QLabel("📁 Aucun projet")
        self.project_label.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 9px;")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.project_label)
        
        return layout
    
    def setup_3d_view(self):
        """Configure la vue 3D optimisée pour thème sombre"""
        try:
            # Configuration PyQtGraph pour thème sombre
            pg.setConfigOption('background', (0.12, 0.12, 0.12))  # Gris très sombre
            pg.setConfigOption('foreground', (1.0, 1.0, 1.0))     # Blanc
            pg.setConfigOption('antialias', True)
            
            # Widget 3D avec paramètres optimisés
            self.gl_widget = gl.GLViewWidget()
            self.gl_widget.setCameraPosition(distance=120, elevation=25, azimuth=-30)
            self.gl_widget.opts['fov'] = 60
            self.gl_widget.opts['elevation'] = 25
            self.gl_widget.opts['azimuth'] = -30
            self.gl_widget.opts['distance'] = 120
            
            # Configuration de la couleur de fond OpenGL
            self.gl_widget.setBackgroundColor((0.12, 0.12, 0.12, 1.0))
            
            # Style sans bordure pour maximiser l'espace
            self.gl_widget.setStyleSheet("""
                QOpenGLWidget {
                    background-color: rgb(30, 30, 30);
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }
            """)
            
            # Éléments de base
            self.setup_3d_elements()
            self.update_3d_view()
            
        except Exception as e:
            logger.error(f"❌ Erreur setup vue 3D: {e}")
            # Fallback avec style sombre
            self.gl_widget = QLabel("❌ Vue 3D indisponible\nVérifiez l'installation d'OpenGL")
            self.gl_widget.setAlignment(Qt.AlignCenter)
            self.gl_widget.setStyleSheet("""
                QLabel {
                    background-color: rgb(30, 30, 30); 
                    border: 2px dashed #555555; 
                    color: #dc3545;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 40px;
                }
            """)
    
    def setup_3d_elements(self):
        """Configure les éléments 3D de base avec style sombre optimisé"""
        try:
                    
            
            # Axes XYZ plus épais et plus visibles
            axis_length = 60
            axis_width = 6
            
            # Axe X (rouge vif)
            self.axis_x = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [axis_length, 0, 0]], dtype=np.float32),
                color=(1.0, 0.2, 0.2, 1.0), 
                width=axis_width,
                antialias=True
            )
            
            # Axe Y (vert vif)
            self.axis_y = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, axis_length, 0]], dtype=np.float32),
                color=(0.2, 1.0, 0.2, 1.0), 
                width=axis_width,
                antialias=True
            )
            
            # Axe Z (bleu vif)
            self.axis_z = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, axis_length]], dtype=np.float32),
                color=(0.2, 0.4, 1.0, 1.0), 
                width=axis_width,
                antialias=True
            )
            
            # Ajouter les axes à la vue
            self.gl_widget.addItem(self.axis_x)
            self.gl_widget.addItem(self.axis_y)
            self.gl_widget.addItem(self.axis_z)
            
            # Ajouter des labels pour les axes (optionnel)
            self.add_axis_labels()
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur éléments 3D: {e}")
    
    def add_axis_labels(self):
        """Ajoute des labels textuels pour les axes"""
        try:
            # Texte pour les axes (si supporté)
            axis_length = 65
            
            # Note: GLTextItem peut ne pas être disponible partout
            # On utilise des marqueurs à la place
            
            # Marqueurs de fin d'axe plus visibles
            marker_size = 2
            
            # Fin axe X
            x_marker = gl.GLScatterPlotItem(
                pos=np.array([[axis_length, 0, 0]], dtype=np.float32),
                color=(1.0, 0.2, 0.2, 1.0),
                size=marker_size * 3
            )
            self.gl_widget.addItem(x_marker)
            
            # Fin axe Y  
            y_marker = gl.GLScatterPlotItem(
                pos=np.array([[0, axis_length, 0]], dtype=np.float32),
                color=(0.2, 1.0, 0.2, 1.0),
                size=marker_size * 3
            )
            self.gl_widget.addItem(y_marker)
            
            # Fin axe Z
            z_marker = gl.GLScatterPlotItem(
                pos=np.array([[0, 0, axis_length]], dtype=np.float32),
                color=(0.2, 0.4, 1.0, 1.0),
                size=marker_size * 3
            )
            self.gl_widget.addItem(z_marker)
            
        except Exception as e:
            logger.debug(f"Labels d'axes non ajoutés: {e}")
    
    def setup_connections(self):
        """Configure les connexions"""
        try:
            # Connexion avec le panneau flottant
            self.floating_panel.coordinates_changed.connect(self.on_coordinate_changed)
            
            # Connexion avec ApplicationData
            if self.app_data and hasattr(self.app_data, 'data_changed'):
                self.app_data.data_changed.connect(self.on_app_data_changed)
                logger.info("🔗 Connexion ApplicationData établie")
            
            # Connexion avec ProjectManager
            if self.project_manager:
                if hasattr(self.project_manager, 'project_loaded'):
                    self.project_manager.project_loaded.connect(self.on_project_loaded)
                if hasattr(self.project_manager, 'workflow_step_completed'):
                    self.project_manager.workflow_step_completed.connect(self.on_workflow_updated)
                logger.info("🔗 Connexion ProjectManager établie")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur setup connexions: {e}")
    
    def apply_dark_theme(self):
        """Applique le thème sombre cohérent et ultra-optimisé"""
        self.setStyleSheet("""
            /* Widget principal */
            DimconWidget {
                background-color: rgb(30, 30, 30);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Container - maximiser l'espace */
            QWidget {
                background-color: rgb(30, 30, 30);
                border: none;
                margin: 0px;
                padding: 0px;
            }
            
            /* Header et footer compacts */
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            
            /* CheckBoxes compactes */
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
                spacing: 6px;
                background: transparent;
                font-size: 10px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #2d2d30;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            
            QCheckBox::indicator:hover {
                border-color: #777777;
                background-color: #383838;
            }
            
            /* Boutons standards */
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 10px;
                min-height: 22px;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #004577;
            }
            
            /* Bouton de validation */
            QPushButton#validateButton {
                background-color: #28a745;
                font-size: 11px;
                padding: 8px 14px;
                font-weight: bold;
            }
            
            QPushButton#validateButton:hover {
                background-color: #1e7e34;
            }
            
            QPushButton#validateButton:pressed {
                background-color: #155724;
            }
            
            /* Boutons de vue 3D compacts */
            QPushButton[text="🔭"], 
            QPushButton[text="⬆️"], 
            QPushButton[text="➡️"], 
            QPushButton[text="🎯"] {
                background-color: #6c757d;
                font-size: 12px;
                padding: 2px;
                min-height: 20px;
                min-width: 20px;
                border-radius: 3px;
            }
            
            QPushButton[text="🔭"]:hover, 
            QPushButton[text="⬆️"]:hover, 
            QPushButton[text="➡️"]:hover, 
            QPushButton[text="🎯"]:hover {
                background-color: #545b62;
            }
            
            /* Bouton de reset compact */
            QPushButton[text="🔄"] {
                background-color: #17a2b8;
                padding: 4px;
                min-height: 24px;
                min-width: 28px;
            }
            
            QPushButton[text="🔄"]:hover {
                background-color: #138496;
            }
        """)
    
    # ==========================================
    # GESTION DES ÉVÉNEMENTS ET MISES À JOUR
    # ==========================================
    
    def on_coordinate_changed(self, point_id, coord, value):
        """Appelée quand une coordonnée change dans le panneau flottant"""
        # Mettre à jour les données locales
        self.points_data[point_id][coord] = value
        
        # Marquer comme non validé
        self.is_validated = False
        self.floating_panel.update_validation_status(False)
        
        # Mettre à jour la vue 3D
        self.update_3d_view()
        
        # Recalculer les métriques
        self.update_metrics()
        
        # Synchroniser avec ApplicationData
        self.sync_to_app_data()
        
        # Émettre signal
        self.dimcon_data_changed.emit(self.points_data.copy())
        
        # Mise à jour du statut
        self.status_label.setText("📊 Coordonnées modifiées - Validation requise")
        
        logger.debug(f"📝 {point_id}.{coord} = {value:.6f}")
    
    def update_3d_view(self):
        """Met à jour la vue 3D complète"""
        try:
            # Supprimer les anciens éléments (sauf base)
            items_to_remove = []
            base_items = [ self.axis_x, self.axis_y, self.axis_z]
            
            for item in self.gl_widget.items[:]:
                if item not in base_items:
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                try:
                    self.gl_widget.removeItem(item)
                except:
                    pass
            
            
            
            # Dessiner la forme du navire si activée
            if self.show_boat_cb.isChecked():
                self.draw_boat_shape()
            
            # Dessiner les points et connexions
            self.draw_points_and_connections()
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur mise à jour vue 3D: {e}")
    
    def draw_boat_shape(self):
        """Dessine une représentation simplifiée du navire - Version corrigée sans GLMeshItem"""
        try:
            # Récupérer les positions
            bow_y = self.points_data["Bow"]["Y"]
            port_x = self.points_data["Port"]["X"]
            stb_x = self.points_data["Stb"]["X"]
            
            # Forme simplifiée du navire avec proportions réalistes
            scale_factor = 1.1
            boat_points = np.array([
                [0, abs(bow_y) * 1.3, 0],                        # Proue (étrave)
                [port_x * 0.7, abs(bow_y) * 0.8, 0],            # Avant bâbord
                [port_x * scale_factor, abs(bow_y) * 0.3, 0],   # Milieu avant bâbord
                [port_x * scale_factor, 0, 0],                  # Milieu bâbord
                [port_x * scale_factor, -abs(bow_y) * 0.3, 0],  # Milieu arrière bâbord
                [port_x * 0.9, -abs(bow_y) * 0.9, 0],          # Arrière bâbord
                [0, -abs(bow_y) * 0.9, 0],                      # Poupe (arrière)
                [stb_x * 0.9, -abs(bow_y) * 0.9, 0],           # Arrière tribord
                [stb_x * scale_factor, -abs(bow_y) * 0.3, 0],  # Milieu arrière tribord
                [stb_x * scale_factor, 0, 0],                  # Milieu tribord
                [stb_x * scale_factor, abs(bow_y) * 0.3, 0],   # Milieu avant tribord
                [stb_x * 0.7, abs(bow_y) * 0.8, 0],            # Avant tribord
                [0, abs(bow_y) * 1.3, 0]                        # Retour proue
            ])
            
            # Contour principal du navire - plus épais et plus visible
            boat_line = gl.GLLinePlotItem(
                pos=boat_points,
                color=(0.3, 0.9, 0.3, 1.0),  # Vert vif et opaque
                width=4,
                mode='line_strip',
                antialias=True
            )
            self.gl_widget.addItem(boat_line)
            
            # Ligne centrale du navire (axe longitudinal)
            center_line = np.array([
                [0, abs(bow_y) * 1.3, 0],    # De la proue
                [0, -abs(bow_y) * 0.9, 0]    # À la poupe
            ])
            center_line_item = gl.GLLinePlotItem(
                pos=center_line,
                color=(0.2, 0.7, 0.2, 0.9),  # Vert plus sombre
                width=3,
                mode='lines',
                antialias=True
            )
            self.gl_widget.addItem(center_line_item)
            
            # Ligne transversale au milieu du navire (axe transversal)
            transverse_line = np.array([
                [port_x * scale_factor, 0, 0],  # Bâbord
                [stb_x * scale_factor, 0, 0]    # Tribord
            ])
            transverse_line_item = gl.GLLinePlotItem(
                pos=transverse_line,
                color=(0.2, 0.7, 0.2, 0.7),
                width=2,
                mode='lines',
                antialias=True
            )
            self.gl_widget.addItem(transverse_line_item)
            
            # Marqueurs pour proue et poupe
            # Proue (avant)
            bow_marker = gl.GLScatterPlotItem(
                pos=np.array([[0, abs(bow_y) * 1.3, 0]], dtype=np.float32),
                color=(0.3, 0.9, 0.3, 1.0),
                size=6,
                pxMode=True
            )
            self.gl_widget.addItem(bow_marker)
            
            # Poupe (arrière)
            stern_marker = gl.GLScatterPlotItem(
                pos=np.array([[0, -abs(bow_y) * 0.9, 0]], dtype=np.float32),
                color=(0.3, 0.9, 0.3, 1.0),
                size=6,
                pxMode=True
            )
            self.gl_widget.addItem(stern_marker)
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur forme navire: {e}")
    
    def draw_points_and_connections(self):
        """Dessine les points DIMCON et leurs connexions avec visibilité optimisée"""
        try:
            # Configuration des couleurs (très vives pour thème sombre)
            point_colors = {
                "Bow": (1.0, 0.1, 0.1, 1.0),   # Rouge très vif
                "Port": (1.0, 0.6, 0.0, 1.0),  # Orange très vif
                "Stb": (0.2, 0.6, 1.0, 1.0)    # Bleu très vif
            }
            
            # Tailles ajustées
            cross_size = 5.0
            line_width = 7
            projection_width = 3
            
            # Dessiner chaque point avec meilleur contraste
            for point_id, coords in self.points_data.items():
                px, py, pz = coords["X"], coords["Y"], coords["Z"]
                color = point_colors[point_id]
                
                # Marqueur en croix 3D plus épais
                cross_lines = [
                    # Croix X
                    [[px-cross_size, py, pz], [px+cross_size, py, pz]],
                    # Croix Y  
                    [[px, py-cross_size, pz], [px, py+cross_size, pz]],
                    # Croix Z
                    [[px, py, pz-cross_size], [px, py, pz+cross_size]]
                ]
                
                for line_coords in cross_lines:
                    line = gl.GLLinePlotItem(
                        pos=np.array(line_coords, dtype=np.float32),
                        color=color,
                        width=line_width,
                        mode='lines',
                        antialias=True
                    )
                    self.gl_widget.addItem(line)
                
                # Point central plus visible
                center_point = gl.GLScatterPlotItem(
                    pos=np.array([[px, py, pz]], dtype=np.float32),
                    color=color,
                    size=8,
                    pxMode=True
                )
                self.gl_widget.addItem(center_point)
                
                # Projection sur le plan Z=0 plus contrastée
                if abs(pz) > 0.001:
                    projection_line = gl.GLLinePlotItem(
                        pos=np.array([[px, py, pz], [px, py, 0]], dtype=np.float32),
                        color=(0.9, 0.9, 0.9, 0.7),  # Blanc cassé plus visible
                        width=projection_width,
                        mode='lines',
                        antialias=True
                    )
                    self.gl_widget.addItem(projection_line)
                    
                    # Marqueur de projection au sol
                    proj_marker = gl.GLScatterPlotItem(
                        pos=np.array([[px, py, 0]], dtype=np.float32),
                        color=(0.7, 0.7, 0.7, 0.8),
                        size=4,
                        pxMode=True
                    )
                    self.gl_widget.addItem(proj_marker)
            
            # Triangle des points DIMCON plus épais et plus visible
            triangle_points = np.array([
                [self.points_data["Bow"]["X"], self.points_data["Bow"]["Y"], self.points_data["Bow"]["Z"]],
                [self.points_data["Port"]["X"], self.points_data["Port"]["Y"], self.points_data["Port"]["Z"]],
                [self.points_data["Stb"]["X"], self.points_data["Stb"]["Y"], self.points_data["Stb"]["Z"]],
                [self.points_data["Bow"]["X"], self.points_data["Bow"]["Y"], self.points_data["Bow"]["Z"]]
            ])
            
            triangle_line = gl.GLLinePlotItem(
                pos=triangle_points,
                color=(0.9, 0.3, 1.0, 1.0),  # Violet très vif
                width=5,
                mode='line_strip',
                antialias=True
            )
            self.gl_widget.addItem(triangle_line)
            
            # Ajouter les distances comme lignes pointillées (optionnel)
            self.draw_distance_lines()
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur points et connexions: {e}")
    
    def draw_distance_lines(self):
        """Dessine les lignes de distance entre les points"""
        try:
            # Lignes entre tous les points avec style pointillé simulé
            bow_pos = np.array([self.points_data["Bow"]["X"], self.points_data["Bow"]["Y"], self.points_data["Bow"]["Z"]])
            port_pos = np.array([self.points_data["Port"]["X"], self.points_data["Port"]["Y"], self.points_data["Port"]["Z"]])
            stb_pos = np.array([self.points_data["Stb"]["X"], self.points_data["Stb"]["Y"], self.points_data["Stb"]["Z"]])
            
            # Lignes de référence plus fines
            reference_color = (0.6, 0.6, 0.6, 0.5)
            reference_width = 2
            
            # Port vers Stb (base du triangle)
            port_stb_line = gl.GLLinePlotItem(
                pos=np.array([port_pos, stb_pos], dtype=np.float32),
                color=reference_color,
                width=reference_width,
                mode='lines',
                antialias=True
            )
            self.gl_widget.addItem(port_stb_line)
            
            # Centre entre Port et Stb vers Bow
            center_pos = (port_pos + stb_pos) / 2
            center_bow_line = gl.GLLinePlotItem(
                pos=np.array([center_pos, bow_pos], dtype=np.float32),
                color=(0.8, 0.8, 0.2, 0.6),  # Jaune pour la ligne de référence
                width=reference_width,
                mode='lines',
                antialias=True
            )
            self.gl_widget.addItem(center_bow_line)
            
        except Exception as e:
            logger.debug(f"Lignes de distance non ajoutées: {e}")
    
    def update_metrics(self):
        """Met à jour les métriques calculées"""
        try:
            metrics = self.calculate_validation_metrics()
            self.floating_panel.update_metrics(metrics)
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur calcul métriques: {e}")
    
    def calculate_validation_metrics(self) -> Dict[str, float]:
        """Calcule les métriques de validation"""
        try:
            bow = np.array([self.points_data["Bow"]["X"], self.points_data["Bow"]["Y"], self.points_data["Bow"]["Z"]])
            port = np.array([self.points_data["Port"]["X"], self.points_data["Port"]["Y"], self.points_data["Port"]["Z"]])
            stb = np.array([self.points_data["Stb"]["X"], self.points_data["Stb"]["Y"], self.points_data["Stb"]["Z"]])
            
            # Centre entre Port et Stb
            center = (port + stb) / 2
            
            # Distances
            dist_port_stb = np.linalg.norm(stb - port)
            dist_bow_port = np.linalg.norm(port - bow)
            dist_bow_stb = np.linalg.norm(stb - bow)
            dist_bow_center = np.linalg.norm(center - bow)
            
            # Aire du triangle
            v1 = port - bow
            v2 = stb - bow
            area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            
            return {
                "triangle_area": area,
                "port_stb_distance": dist_port_stb,
                "bow_port_distance": dist_bow_port,
                "bow_stb_distance": dist_bow_stb,
                "bow_center_distance": dist_bow_center,
                "max_dimension": max(dist_port_stb, dist_bow_port, dist_bow_stb),
                "min_dimension": min(dist_port_stb, dist_bow_port, dist_bow_stb)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul métriques: {e}")
            return {key: 0.0 for key in [
                "triangle_area", "port_stb_distance", "bow_port_distance", 
                "bow_stb_distance", "bow_center_distance", "max_dimension", "min_dimension"
            ]}
    
    def set_3d_view(self, distance, elevation, azimuth):
        """Change la vue 3D selon les paramètres donnés - Version corrigée"""
        try:
            # S'assurer que les paramètres sont des nombres simples
            self.gl_widget.setCameraPosition(
                distance=float(distance), 
                elevation=float(elevation), 
                azimuth=float(azimuth)
            )
            logger.debug(f"🎥 Vue 3D: distance={distance}, elevation={elevation}°, azimuth={azimuth}°")
        except Exception as e:
            logger.warning(f"⚠️ Erreur changement vue 3D: {e}")
            # Fallback sécurisé
            try:
                self.gl_widget.setCameraPosition(distance=140, elevation=25, azimuth=-30)
            except:
                logger.error("❌ Impossible de réinitialiser la vue 3D")
    
    # ==========================================
    # ACTIONS PRINCIPALES
    # ==========================================
    
    def reset_to_defaults(self):
        """Remet les valeurs par défaut"""
        default_points = {
            "Bow": {"X": -0.269, "Y": -64.232, "Z": 10.888},
            "Port": {"X": -9.347, "Y": -27.956, "Z": 13.491},
            "Stb": {"X": 9.392, "Y": -27.827, "Z": 13.506}
        }
        
        # Mettre à jour les données
        self.points_data = default_points.copy()
        self.is_validated = False
        
        # Mettre à jour le panneau flottant
        self.floating_panel.set_points_data(self.points_data)
        self.floating_panel.update_validation_status(False)
        
        # Rafraîchir l'interface
        self.update_3d_view()
        self.update_metrics()
        self.sync_to_app_data()
        
        self.status_label.setText("🔄 Valeurs par défaut restaurées")
        logger.info("🔄 Valeurs par défaut restaurées")
    
    def validate_and_save(self):
        """Valide et sauvegarde dans le projet et ApplicationData"""
        logger.info("✅ Début validation et sauvegarde DIMCON")
        
        try:
            # === VALIDATION PROJET ===
            if not self.project_manager or not self.project_manager.current_project:
                QMessageBox.warning(self, "Aucun projet", 
                                  "Aucun projet n'est chargé. Créez ou ouvrez un projet d'abord.")
                logger.warning("⚠️ Tentative de sauvegarde sans projet")
                return
            
            # === CALCUL MÉTRIQUES ===
            metrics = self.calculate_validation_metrics()
            
            # === VALIDATION BASIQUE ===
            validation_issues = []
            
            # Vérifier les distances minimales
            if metrics["port_stb_distance"] < 1.0:
                validation_issues.append("Distance Port-Tribord trop faible (< 1m)")
            
            if metrics["triangle_area"] < 1.0:
                validation_issues.append("Aire du triangle trop faible (< 1m²)")
            
            # Si des problèmes détectés
            if validation_issues:
                reply = QMessageBox.warning(
                    self, "Validation avec avertissements",
                    f"Problèmes détectés:\n• " + "\n• ".join(validation_issues) + 
                    "\n\nContinuer quand même ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # === ENREGISTREMENT HISTORIQUE ===
            validation_entry = {
                "timestamp": datetime.now().isoformat(),
                "points": self.points_data.copy(),
                "metrics": metrics,
                "issues": validation_issues
            }
            self.validation_history.append(validation_entry)
            
            # === SAUVEGARDE APPLICATIONDATA ===
            if self.app_data:
                self.app_data.dimcon = self.points_data.copy()
                
                # Sauvegarde HDF5 automatique si configuré
                if hasattr(self.app_data, 'save_all_to_hdf5') and self.app_data.hdf5_file_path:
                    self.app_data.save_all_to_hdf5()
                    logger.info("💾 Sauvegarde HDF5 automatique effectuée")
                
                # Émettre signal de changement
                self.app_data.data_changed.emit("dimcon")
            
            # === SAUVEGARDE PROJET ===
            success = self.project_manager.update_dimcon_data(self.points_data)
            
            if success:
                # Marquer l'étape workflow comme terminée
                self.project_manager.update_workflow_status("dimcon", True, 100.0)
                
                # Émettre le signal workflow_step_completed pour mettre à jour le dashboard
                if hasattr(self.project_manager, 'workflow_step_completed'):
                    self.project_manager.workflow_step_completed.emit("dimcon", True)
                    print("📊 Signal workflow_step_completed émis pour DIMCON")
                
                # Mise à jour interface
                self.is_validated = True
                self.floating_panel.update_validation_status(True)
                
                self.status_label.setText("✅ Points validés et sauvegardés")
                self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
                
                # Émission du signal de validation
                self.validation_completed.emit({
                    "points": self.points_data.copy(),
                    "metrics": metrics,
                    "timestamp": validation_entry["timestamp"]
                })
                
                # Message de succès
                QMessageBox.information(
                    self, "Validation réussie",
                    f"✅ Points DIMCON validés et sauvegardés\n\n"
                    f"📊 Métriques:\n"
                    f"• Aire triangle: {metrics['triangle_area']:.3f} m²\n"
                    f"• Distance Port-Tribord: {metrics['port_stb_distance']:.3f} m\n"
                    f"• Distance Proue-Centre: {metrics['bow_center_distance']:.3f} m"
                )
                
                logger.info(f"✅ Validation #{len(self.validation_history)} réussie")
                
                # Reset style après 5 secondes
                QTimer.singleShot(5000, lambda: self.status_label.setStyleSheet("color: #bdc3c7; font-style: italic;"))
                
            else:
                logger.error("❌ Échec sauvegarde projet")
                QMessageBox.critical(self, "Erreur", "Impossible de sauvegarder dans le projet.")
                
        except Exception as e:
            logger.error(f"❌ Erreur validation: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la validation:\n{str(e)}")
    
    # ==========================================
    # SYNCHRONISATION AVEC SYSTÈME
    # ==========================================
    
    def sync_to_app_data(self):
        """Synchronise les données locales vers ApplicationData"""
        if self.app_data and hasattr(self.app_data, 'dimcon'):
            self.app_data.dimcon = self.points_data.copy()
            logger.debug("🔄 Synchronisation ApplicationData")
    
    def load_from_app_data(self):
        """Charge les données depuis ApplicationData"""
        if self.app_data and hasattr(self.app_data, 'dimcon'):
            self.points_data = self.app_data.dimcon.copy()
            self.refresh_interface_from_data()
            logger.info("📂 Données chargées depuis ApplicationData")
    
    def refresh_interface_from_data(self):
        """Rafraîchit l'interface depuis les données actuelles"""
        try:
            # Mise à jour du panneau flottant
            self.floating_panel.set_points_data(self.points_data)
            
            # Mise à jour des vues
            self.update_3d_view()
            self.update_metrics()
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur refresh interface: {e}")
    
    # ==========================================
    # CALLBACKS SYSTÈME
    # ==========================================
    
    @pyqtSlot(str)
    def on_app_data_changed(self, section):
        """Callback quand ApplicationData change"""
        if section in ["dimcon", "all"]:
            self.load_from_app_data()
            logger.debug(f"🔄 ApplicationData changé: {section}")
    
    @pyqtSlot(dict)
    def on_project_loaded(self, project_data):
        """Callback quand un projet est chargé"""
        try:
            # Charger données DIMCON du projet
            dimcon_data = project_data.get("dimcon_data", {})
            
            if "points" in dimcon_data:
                self.points_data = dimcon_data["points"].copy()
                self.refresh_interface_from_data()
                self.status_label.setText("📂 Points chargés depuis le projet")
            
            # Mise à jour info projet
            metadata = project_data.get("metadata", {})
            vessel = metadata.get("vessel", "Projet")
            self.project_label.setText(f"📁 {vessel}")
            
            logger.info(f"📂 Projet chargé: {vessel}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement projet: {e}")
    
    @pyqtSlot(str, bool)
    def on_workflow_updated(self, step_name, completed):
        """Callback quand le workflow est mis à jour"""
        if step_name == "dimcon" and completed:
            self.is_validated = True
            self.floating_panel.update_validation_status(True)
            logger.info("✅ Workflow DIMCON marqué comme terminé")
    
    # ==========================================
    # MÉTHODES PUBLIQUES POUR INTÉGRATION
    # ==========================================
    
    def set_data_model(self, app_data):
        """Compatibilité avec l'ancien système"""
        self.app_data = app_data
        self.setup_connections()
        self.load_from_app_data()
        logger.info("🔗 Modèle de données connecté")
    
    def get_points_data(self) -> Dict[str, Dict[str, float]]:
        """Retourne les données des points actuelles"""
        return self.points_data.copy()
    
    def set_points_data(self, points_data: Dict[str, Dict[str, float]]):
        """Définit les données des points (usage externe)"""
        self.points_data = points_data.copy()
        self.refresh_interface_from_data()
        self.sync_to_app_data()
    
    def get_validation_metrics(self) -> Dict[str, float]:
        """Retourne les métriques de validation actuelles"""
        return self.calculate_validation_metrics()
    
    def is_valid_configuration(self) -> Tuple[bool, List[str]]:
        """Vérifie si la configuration actuelle est valide"""
        metrics = self.calculate_validation_metrics()
        issues = []
        
        if metrics["port_stb_distance"] < 1.0:
            issues.append("Distance Port-Tribord insuffisante")
        
        if metrics["triangle_area"] < 1.0:
            issues.append("Aire du triangle insuffisante")
        
        return len(issues) == 0, issues
    
    def resizeEvent(self, event):
        """Gère le redimensionnement de la fenêtre avec positionnement optimisé"""
        super().resizeEvent(event)
        
        # Repositionner le panneau flottant si nécessaire
        if hasattr(self, 'floating_panel'):
            panel_rect = self.floating_panel.geometry()
            widget_rect = self.rect()
            
            # Calculer une position optimale par défaut
            optimal_x = 10  # Près du bord gauche
            optimal_y = 50  # Sous le header
            
            # Si le panneau sort complètement des limites, le repositionner
            if (panel_rect.right() > widget_rect.right() - 10 or 
                panel_rect.bottom() > widget_rect.bottom() - 10 or
                panel_rect.left() < 0 or panel_rect.top() < 40):
                
                # S'assurer que le panneau reste visible
                new_x = max(5, min(optimal_x, widget_rect.width() - panel_rect.width() - 10))
                new_y = max(40, min(optimal_y, widget_rect.height() - panel_rect.height() - 0))
                
                self.floating_panel.move(new_x, new_y)


# Classe pour compatibilité (si nécessaire)
DimconPage = DimconWidget