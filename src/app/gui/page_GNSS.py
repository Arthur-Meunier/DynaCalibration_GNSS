# page_gnss.py - VERSION COMPLÈTEMENT CORRIGÉE
import os
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTableWidget, 
    QTableWidgetItem, QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSplitter, QMessageBox, QHeaderView, QGridLayout, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from import_gnss import GNSSImportDialog  # Importer le dialogue d'import

class GnssWidget(QWidget):
    """Widget pour configurer les paramètres GNSS et importer des données"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_data = None  # Sera défini par set_data_model
        self.setupUI()
    
    def set_data_model(self, app_data):
        """Définit le modèle de données utilisé par ce widget"""
        self.app_data = app_data
        
        # S'assurer que la structure GNSS est correcte
        self.ensure_gnss_structure()
        
        # Connecter aux signaux de mise à jour si disponibles
        if hasattr(self.app_data, 'data_changed'):
            self.app_data.data_changed.connect(self.on_app_data_changed)
        
        # Initialiser l'interface avec les données
        self.sync_with_model()
    
    def ensure_gnss_structure(self):
        """S'assure que la structure des données GNSS est correcte"""
        if not self.app_data:
            return
        
        # Vérifier et corriger mobile_points
        if ('mobile_points' not in self.app_data.gnss_data or 
            self.app_data.gnss_data['mobile_points'] is None):
            self.app_data.gnss_data['mobile_points'] = {}
        
        # Vérifier et corriger mobile_positions
        if 'mobile_positions' not in self.app_data.gnss_data:
            self.app_data.gnss_data['mobile_positions'] = ["Bow", "Bow"]
        
        # Vérifier et corriger fixed_point
        if 'fixed_point' not in self.app_data.gnss_data:
            self.app_data.gnss_data['fixed_point'] = {"E": 0.0, "N": 0.0, "h": 0.0}
        
        # Vérifier les paramètres par défaut
        default_params = {
            'meridian_convergence': 0.0,
            'scale_factor': 1.0,
            'time_offset': 0.0
        }
        
        for param, default_value in default_params.items():
            if param not in self.app_data.gnss_data:
                self.app_data.gnss_data[param] = default_value
    
    def setupUI(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Titre principal
        title_label = QLabel("Configuration GNSS")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Panneau d'information
        info_box = QGroupBox("Informations sur les paramètres GNSS")
        info_box.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
                color: white;
            }
        """)
        
        info_layout = QVBoxLayout(info_box)
        info_text = QLabel(
            "<p>Les paramètres suivants sont utilisés pour le traitement des données GNSS:</p>"
            "<ul>"
            "<li><b>Méridien de convergence:</b> Angle entre le Nord Géographique et le Nord du système de projection (en degrés).</li>"
            "<li><b>Facteur d'échelle:</b> Facteur appliqué aux distances dans le système de projection.</li>"
            "<li><b>Décalage temporel:</b> Ajustement temporel appliqué aux données GNSS (en secondes).</li>"
            "</ul>"
            "<p>Les zones géodésiques doivent être cohérentes entre tous les points de mesure.</p>"
        )
        info_text.setStyleSheet("color: white;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        main_layout.addWidget(info_box)
        
        # Paramètres GNSS globaux
        params_box = QGroupBox("Paramètres GNSS")
        params_box.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
                color: white;
            }
        """)
        
        params_layout = QFormLayout(params_box)
        
        # Méridien de convergence
        meridian_label = QLabel("Méridien de convergence (°):")
        meridian_label.setStyleSheet("color: white;")
        self.meridian_input = QDoubleSpinBox()
        self.meridian_input.setRange(-180, 180)
        self.meridian_input.setDecimals(4)
        self.meridian_input.setSingleStep(0.1)
        self.meridian_input.setValue(0.0)
        self.meridian_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        params_layout.addRow(meridian_label, self.meridian_input)
        
        # Facteur d'échelle
        scale_label = QLabel("Facteur d'échelle:")
        scale_label.setStyleSheet("color: white;")
        self.scale_input = QDoubleSpinBox()
        self.scale_input.setRange(0.9, 1.1)
        self.scale_input.setDecimals(6)
        self.scale_input.setSingleStep(0.000001)
        self.scale_input.setValue(1.0)
        self.scale_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        params_layout.addRow(scale_label, self.scale_input)
        
        # Décalage temporel
        time_offset_label = QLabel("Décalage temporel (s):")
        time_offset_label.setStyleSheet("color: white;")
        self.time_offset_input = QDoubleSpinBox()
        self.time_offset_input.setRange(-3600, 3600)
        self.time_offset_input.setDecimals(3)
        self.time_offset_input.setSingleStep(0.001)
        self.time_offset_input.setValue(0.0)
        self.time_offset_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        params_layout.addRow(time_offset_label, self.time_offset_input)
        
        main_layout.addWidget(params_box)
        
        # Point fixe
        fixed_point_box = QGroupBox("Point fixe (référence)")
        fixed_point_box.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
                color: white;
            }
        """)
        
        fixed_point_layout = QFormLayout(fixed_point_box)
        
        # Position du point fixe
        position_label = QLabel("Position:")
        position_label.setStyleSheet("color: white;")
        self.fixed_point_selector = QComboBox()
        self.fixed_point_selector.addItems(["Bow", "Port", "STB", "Stern"])
        self.fixed_point_selector.setStyleSheet("""
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #444444;
                color: white;
                selection-background-color: #8e44ad;
            }
        """)
        fixed_point_layout.addRow(position_label, self.fixed_point_selector)
        
        # Coordonnées E, N, h du point fixe
        e_label = QLabel("E (m):")
        e_label.setStyleSheet("color: white;")
        self.fixed_e_input = QDoubleSpinBox()
        self.fixed_e_input.setRange(-1000000, 1000000)
        self.fixed_e_input.setDecimals(3)
        self.fixed_e_input.setSingleStep(0.1)
        self.fixed_e_input.setValue(0.0)
        self.fixed_e_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        fixed_point_layout.addRow(e_label, self.fixed_e_input)
        
        n_label = QLabel("N (m):")
        n_label.setStyleSheet("color: white;")
        self.fixed_n_input = QDoubleSpinBox()
        self.fixed_n_input.setRange(-1000000, 1000000)
        self.fixed_n_input.setDecimals(3)
        self.fixed_n_input.setSingleStep(0.1)
        self.fixed_n_input.setValue(0.0)
        self.fixed_n_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        fixed_point_layout.addRow(n_label, self.fixed_n_input)
        
        h_label = QLabel("h (m):")
        h_label.setStyleSheet("color: white;")
        self.fixed_h_input = QDoubleSpinBox()
        self.fixed_h_input.setRange(-1000, 10000)
        self.fixed_h_input.setDecimals(3)
        self.fixed_h_input.setSingleStep(0.1)
        self.fixed_h_input.setValue(0.0)
        self.fixed_h_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border-radius: 2px;
                background-color: #555555;
            }
        """)
        fixed_point_layout.addRow(h_label, self.fixed_h_input)
        
        main_layout.addWidget(fixed_point_box)
        
        # Points mobiles
        mobile_points_box = QGroupBox("Points mobiles")
        mobile_points_box.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
                color: white;
            }
        """)
        
        mobile_points_layout = QVBoxLayout(mobile_points_box)
        
        # Tableau des points mobiles
        self.mobile_table = QTableWidget(2, 4)  # 2 lignes, 4 colonnes
        self.mobile_table.setHorizontalHeaderLabels(["Point", "Position", "Statut", "Import"])
        
        # Configurer l'apparence du tableau
        self.mobile_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mobile_table.verticalHeader().setVisible(False)
        self.mobile_table.setStyleSheet("""
            QTableWidget {
                background-color: #353535;
                color: white;
                gridline-color: #555555;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget QHeaderView::section {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
        """)
        
        # Remplir le tableau avec les noms des points mobiles et les sélecteurs de position
        for i, point_name in enumerate(["Mobile 1", "Mobile 2"]):
            # Nom du point
            name_item = QTableWidgetItem(point_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.mobile_table.setItem(i, 0, name_item)
            
            # Sélecteur de position pour le point mobile
            position_selector = QComboBox()
            position_selector.addItems(["Bow", "Port", "STB", "Stern"])
            position_selector.setStyleSheet("""
                QComboBox {
                    background-color: #444444;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                QComboBox::drop-down {
                    border: 0px;
                }
                QComboBox QAbstractItemView {
                    background-color: #444444;
                    color: white;
                    selection-background-color: #8e44ad;
                }
            """)
            self.mobile_table.setCellWidget(i, 1, position_selector)
            
            # Statut du point
            status_item = QTableWidgetItem("Non importé")
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_item.setBackground(QColor("#aa4444"))
            self.mobile_table.setItem(i, 2, status_item)
            
            # Bouton d'import
            import_button = QPushButton("Importer")
            import_button.setStyleSheet("""
                QPushButton {
                    background-color: #8e44ad;
                    color: white;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #9b59b6;
                }
            """)
            # Utiliser une fonction lambda pour capturer l'index de ligne
            import_button.clicked.connect(lambda checked, row=i: self.on_import_button_clicked(row))
            
            # Créer un widget conteneur pour le bouton
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)
            button_layout.addWidget(import_button)
            
            self.mobile_table.setCellWidget(i, 3, button_widget)
        
        mobile_points_layout.addWidget(self.mobile_table)
        main_layout.addWidget(mobile_points_box)
        
        # Boutons de sauvegarde/réinitialisation
        buttons_layout = QHBoxLayout()
        
        reset_button = QPushButton("Réinitialiser")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_button.clicked.connect(self.reset_form)
        
        save_button = QPushButton("Enregistrer")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        
        buttons_layout.addWidget(reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()
    
    def on_import_button_clicked(self, row_index):
        """Gère le clic sur le bouton d'import des points mobiles - VERSION COMPLÈTEMENT CORRIGÉE"""
        try:
            print(f"Import déclenché pour la ligne {row_index}")
            
            # S'assurer que la structure GNSS est correcte avant l'import
            self.ensure_gnss_structure()
            
            # Ouvrir le dialogue d'import GNSS
            import_dialog = GNSSImportDialog(self)
            
            # Configurer le dialogue avec un titre spécifique
            import_dialog.setWindowTitle(f"Importer les données GNSS - Point mobile {row_index + 1}")
            
            result = import_dialog.exec_()
            
            if result == import_dialog.Accepted:
                # Récupérer les données importées
                imported_data = import_dialog.get_imported_data()
                
                if imported_data is not None and not imported_data.empty:
                    # Mettre à jour le modèle de données
                    if self.app_data:
                        # Stocker les données avec une clé unique
                        point_key = f"mobile_{row_index + 1}"
                        
                        # DEBUG: Afficher l'état avant modification
                        print(f"État mobile_points avant: {type(self.app_data.gnss_data.get('mobile_points'))}")
                        
                        # S'assurer que mobile_points est un dictionnaire
                        if not isinstance(self.app_data.gnss_data['mobile_points'], dict):
                            print("Correction: mobile_points n'était pas un dictionnaire, conversion...")
                            self.app_data.gnss_data['mobile_points'] = {}
                        
                        # Obtenir la position sélectionnée
                        position_selector = self.mobile_table.cellWidget(row_index, 1)
                        selected_position = position_selector.currentText() if position_selector else "Bow"
                        
                        # Stocker les données
                        self.app_data.gnss_data['mobile_points'][point_key] = {
                            'data': imported_data,
                            'position': selected_position,
                            'import_timestamp': pd.Timestamp.now(),
                            'file_info': {
                                'rows': len(imported_data),
                                'columns': list(imported_data.columns)
                            }
                        }
                        
                        print(f"Données stockées pour {point_key}: {len(imported_data)} lignes")
                        
                        # Émettre le signal de changement (si disponible)
                        if hasattr(self.app_data, 'data_changed'):
                            self.app_data.data_changed.emit("gnss")
                        
                        # Mettre à jour l'interface
                        self.update_mobile_status(
                            row_index, 
                            f"Importé ({len(imported_data)} pts)", 
                            True
                        )
                        
                        # Message de succès
                        QtWidgets.QMessageBox.information(
                            self, 
                            "Succès", 
                            f"Données GNSS importées avec succès pour le point mobile {row_index + 1}:\n"
                            f"- {len(imported_data)} points de données\n"
                            f"- Colonnes: {', '.join(imported_data.columns)}\n"
                            f"- Position: {selected_position}"
                        )
                        
                        print(f"Import réussi pour le point mobile {row_index + 1}")
                    else:
                        QtWidgets.QMessageBox.warning(
                            self, 
                            "Erreur", 
                            "Le modèle de données n'est pas disponible."
                        )
                else:
                    QtWidgets.QMessageBox.warning(
                        self, 
                        "Avertissement", 
                        "Aucune donnée valide n'a été importée."
                    )
            else:
                print("Import annulé par l'utilisateur")
        
        except Exception as e:
            error_msg = f"Une erreur est survenue lors de l'import: {str(e)}"
            print(f"Erreur dans on_import_button_clicked: {e}")
            import traceback
            traceback.print_exc()
            
            # Afficher l'erreur à l'utilisateur
            QtWidgets.QMessageBox.critical(self, "Erreur d'import", error_msg)
            
            # Mettre à jour le statut en cas d'erreur
            self.update_mobile_status(row_index, "Erreur d'import", False)

    def update_mobile_status(self, row, status_text, success=False):
        """Met à jour le statut d'un point mobile dans le tableau"""
        if 0 <= row < self.mobile_table.rowCount():
            status_item = self.mobile_table.item(row, 2)
            if status_item:
                status_item.setText(status_text)
                if success:
                    status_item.setBackground(QColor("#44aa44"))  # Vert pour succès
                else:
                    status_item.setBackground(QColor("#aa4444"))  # Rouge pour échec
    
    def on_app_data_changed(self):
        """Réagit aux changements dans les données de l'application"""
        self.sync_with_model()
    
    def sync_with_model(self):
        """Synchronise l'interface avec le modèle de données - VERSION ROBUSTE"""
        if not self.app_data:
            return
        
        try:
            # S'assurer que la structure est correcte
            self.ensure_gnss_structure()
            
            # Obtenir les données GNSS
            gnss_data = self.app_data.gnss_data
            
            # Synchroniser les paramètres globaux
            self.meridian_input.setValue(gnss_data.get('meridian_convergence', 0.0))
            self.scale_input.setValue(gnss_data.get('scale_factor', 1.0))
            self.time_offset_input.setValue(gnss_data.get('time_offset', 0.0))
            
            # Synchroniser le point fixe
            fixed_point = gnss_data.get('fixed_point', {})
            if isinstance(fixed_point, dict):
                if 'position' in fixed_point:
                    position_text = fixed_point['position']
                    index = self.fixed_point_selector.findText(position_text)
                    if index >= 0:
                        self.fixed_point_selector.setCurrentIndex(index)
                
                self.fixed_e_input.setValue(fixed_point.get('E', 0.0))
                self.fixed_n_input.setValue(fixed_point.get('N', 0.0))
                self.fixed_h_input.setValue(fixed_point.get('h', 0.0))
            
            # Synchroniser les positions des points mobiles
            mobile_positions = gnss_data.get('mobile_positions', ["Bow", "Bow"])
            for i, position in enumerate(mobile_positions):
                if i < self.mobile_table.rowCount():
                    position_selector = self.mobile_table.cellWidget(i, 1)
                    if position_selector:
                        index = position_selector.findText(position)
                        if index >= 0:
                            position_selector.setCurrentIndex(index)
            
            # Synchroniser les statuts des points mobiles
            mobile_points = gnss_data.get('mobile_points', {})
            
            # Réinitialiser tous les statuts
            for i in range(self.mobile_table.rowCount()):
                self.update_mobile_status(i, "Non importé", False)
            
            # Mettre à jour les statuts pour les points importés
            if isinstance(mobile_points, dict):
                for key, point_data in mobile_points.items():
                    if key.startswith('mobile_'):
                        try:
                            index = int(key.split('_')[1]) - 1  # mobile_1 -> index 0
                            if 0 <= index < self.mobile_table.rowCount():
                                if isinstance(point_data, dict) and 'data' in point_data:
                                    data = point_data['data']
                                    if data is not None and hasattr(data, '__len__'):
                                        rows_count = len(data)
                                        self.update_mobile_status(
                                            index, 
                                            f"Importé ({rows_count} pts)", 
                                            True
                                        )
                        except (ValueError, IndexError) as e:
                            print(f"Erreur lors de la synchronisation du point {key}: {e}")
            
            print("Synchronisation avec le modèle terminée")
            
        except Exception as e:
            print(f"Erreur lors de la synchronisation: {e}")
            import traceback
            traceback.print_exc()
    
    def reset_form(self):
        """Réinitialise le formulaire"""
        # Réinitialiser les paramètres
        self.meridian_input.setValue(0.0)
        self.scale_input.setValue(1.0)
        self.time_offset_input.setValue(0.0)
        
        # Réinitialiser le point fixe
        self.fixed_point_selector.setCurrentIndex(0)
        self.fixed_e_input.setValue(0.0)
        self.fixed_n_input.setValue(0.0)
        self.fixed_h_input.setValue(0.0)
        
        # Réinitialiser les positions des points mobiles
        for i in range(self.mobile_table.rowCount()):
            position_selector = self.mobile_table.cellWidget(i, 1)
            if position_selector:
                position_selector.setCurrentIndex(0)
            
            # Réinitialiser le statut
            self.update_mobile_status(i, "Non importé", False)
        
        # Réinitialiser les données dans le modèle
        if self.app_data:
            self.app_data.gnss_data.update({
                'meridian_convergence': 0.0,
                'scale_factor': 1.0,
                'time_offset': 0.0,
                'fixed_point': {
                    'position': 'Bow',
                    'E': 0.0,
                    'N': 0.0,
                    'h': 0.0
                },
                'mobile_points': {},  # Dictionnaire vide
                'mobile_positions': ['Bow', 'Bow']
            })
            
            # Émettre le signal de changement
            if hasattr(self.app_data, 'data_changed'):
                self.app_data.data_changed.emit("gnss")
    
    def save_settings(self):
        """Enregistre les paramètres GNSS dans le modèle de données"""
        if not self.app_data:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder les données: app_data n'est pas défini")
            return
        
        try:
            # S'assurer que la structure est correcte
            self.ensure_gnss_structure()
            
            # Sauvegarder les paramètres globaux
            self.app_data.gnss_data['meridian_convergence'] = self.meridian_input.value()
            self.app_data.gnss_data['scale_factor'] = self.scale_input.value()
            self.app_data.gnss_data['time_offset'] = self.time_offset_input.value()
            
            # Sauvegarder le point fixe
            self.app_data.gnss_data['fixed_point'] = {
                'position': self.fixed_point_selector.currentText(),
                'E': self.fixed_e_input.value(),
                'N': self.fixed_n_input.value(),
                'h': self.fixed_h_input.value()
            }
            
            # Sauvegarder les positions des points mobiles
            mobile_positions = []
            for i in range(self.mobile_table.rowCount()):
                position_selector = self.mobile_table.cellWidget(i, 1)
                if position_selector:
                    mobile_positions.append(position_selector.currentText())
                else:
                    mobile_positions.append("Bow")  # Valeur par défaut
            
            self.app_data.gnss_data['mobile_positions'] = mobile_positions
            
            # Émettre le signal de changement si disponible
            if hasattr(self.app_data, 'data_changed'):
                self.app_data.data_changed.emit("gnss")
            
            QtWidgets.QMessageBox.information(self, "Sauvegarde", "Les paramètres GNSS ont été enregistrés avec succès")
            
            print("Paramètres GNSS sauvegardés:")
            print(f"- Méridien: {self.meridian_input.value()}°")
            print(f"- Facteur d'échelle: {self.scale_input.value()}")
            print(f"- Décalage temporel: {self.time_offset_input.value()}s")
            print(f"- Point fixe: {self.app_data.gnss_data['fixed_point']}")
            print(f"- Positions mobiles: {mobile_positions}")
            
        except Exception as e:
            error_msg = f"Erreur lors de la sauvegarde: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Erreur de sauvegarde", error_msg)