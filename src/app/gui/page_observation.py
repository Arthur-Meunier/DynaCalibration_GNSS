# page_observation.py
import os
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSplitter, QMessageBox, QHeaderView, QGridLayout, QFrame, QComboBox,
    QSpinBox, QCheckBox, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
from core.importers.import_observation import ObservationImportDialog
from core.calculations.calculs_observation import ObservationCalculator
class ObservationWidget(QWidget):
    """Widget pour gérer les observations des capteurs et les calculs associés"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_data = None
        self.calculator = ObservationCalculator()
        self.setupUI()
        
        # Timer pour les calculs en arrière-plan
        self.calc_timer = QTimer()
        self.calc_timer.setSingleShot(True)
        self.calc_timer.timeout.connect(self.perform_background_calculation)
        
        print("✓ Page Observation initialisée")
    
    def set_data_model(self, app_data):
        """Définit le modèle de données utilisé par ce widget"""
        self.app_data = app_data
        self.calculator.set_data_model(app_data)
        
        # Connecter aux signaux de mise à jour
        if hasattr(self.app_data, 'data_changed'):
            self.app_data.data_changed.connect(self.on_app_data_changed)
        
        # Initialiser la structure des données
        self.ensure_observation_structure()
        
        # Synchroniser avec le modèle
        self.sync_with_model()
        
        print("✓ Modèle de données connecté à Observation")
    
    def ensure_observation_structure(self):
        """S'assure que la structure des données d'observation est correcte"""
        if not self.app_data:
            return
        
        if not hasattr(self.app_data, 'observation_data'):
            self.app_data.observation_data = {}
        
        # Structure par défaut pour les observations
        default_structure = {
            'sensors': {},  # Stockage des capteurs par ID
            'sensor_types': {},  # Type de chaque capteur (MRU, Compas, Octans)
            'sign_conventions': {},  # Conventions de signe par capteur
            'calculations': {},  # Résultats des calculs
            'active_sensors': []  # Liste des capteurs actifs
        }
        
        for key, default_value in default_structure.items():
            if key not in self.app_data.observation_data:
                self.app_data.observation_data[key] = default_value
    
    def setupUI(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Titre principal
        title_label = QLabel("Gestion des Observations")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Informations sur les conventions
        info_box = self.create_info_box()
        main_layout.addWidget(info_box)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panneau gauche - Configuration des capteurs
        left_panel = self.create_sensor_config_panel()
        main_splitter.addWidget(left_panel)
        
        # Panneau droit - Résultats et visualisations
        right_panel = self.create_results_panel()
        main_splitter.addWidget(right_panel)
        
        # Proportions du splitter
        main_splitter.setSizes([400, 600])
        
        main_layout.addWidget(main_splitter)
        
        # Boutons de contrôle
        control_layout = self.create_control_buttons()
        main_layout.addLayout(control_layout)
    
    def create_info_box(self):
        """Crée la boîte d'information sur les conventions"""
        info_box = QGroupBox("Conventions du Système")
        info_box.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
            }
        """)
        
        info_layout = QVBoxLayout(info_box)
        info_text = QLabel(
            "<p><b>Conventions du repère bateau (après conversion automatique):</b></p>"
            "<ul>"
            "<li><b>X+ Tribord</b> : Axe positif vers tribord (droite du navire)</li>"
            "<li><b>Y+ Avant</b> : Axe positif vers l'avant du navire</li>"
            "<li><b>Z+ Haut</b> : Axe positif vers le haut</li>"
            "<li><b>Pitch Bow Up +</b> : Tangage positif = nez vers le haut</li>"
            "<li><b>Roll Port Up +</b> : Roulis positif = bâbord vers le haut</li>"
            "<li><b>Heading 0°N</b> : Cap 0° = Nord géographique</li>"
            "</ul>"
            "<p><i>Les données de tous les capteurs sont automatiquement converties vers ces conventions.</i></p>"
        )
        info_text.setStyleSheet("color: white;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        return info_box
    
    def create_sensor_config_panel(self):
        """Crée le panneau de configuration des capteurs"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Sélection du nombre de capteurs par type
        sensor_count_box = QGroupBox("Configuration des Capteurs")
        sensor_count_box.setStyleSheet(self.get_groupbox_style())
        sensor_count_layout = QFormLayout(sensor_count_box)
        
        # Nombre de capteurs MRU
        self.mru_count_spin = QSpinBox()
        self.mru_count_spin.setRange(0, 10)
        self.mru_count_spin.setValue(0)
        self.mru_count_spin.valueChanged.connect(self.update_sensor_table)
        self.mru_count_spin.setStyleSheet(self.get_spinbox_style())
        sensor_count_layout.addRow("Nombre de MRU:", self.mru_count_spin)
        
        # Nombre de compas
        self.compass_count_spin = QSpinBox()
        self.compass_count_spin.setRange(0, 10)
        self.compass_count_spin.setValue(0)
        self.compass_count_spin.valueChanged.connect(self.update_sensor_table)
        self.compass_count_spin.setStyleSheet(self.get_spinbox_style())
        sensor_count_layout.addRow("Nombre de Compas:", self.compass_count_spin)
        
        # Nombre d'octans
        self.octans_count_spin = QSpinBox()
        self.octans_count_spin.setRange(0, 10)
        self.octans_count_spin.setValue(0)
        self.octans_count_spin.valueChanged.connect(self.update_sensor_table)
        self.octans_count_spin.setStyleSheet(self.get_spinbox_style())
        sensor_count_layout.addRow("Nombre d'Octans:", self.octans_count_spin)
        
        config_layout.addWidget(sensor_count_box)
        
        # Tableau des capteurs
        sensors_box = QGroupBox("Liste des Capteurs")
        sensors_box.setStyleSheet(self.get_groupbox_style())
        sensors_layout = QVBoxLayout(sensors_box)
        
        self.sensors_table = QTableWidget()
        self.sensors_table.setStyleSheet(self.get_table_style())
        sensors_layout.addWidget(self.sensors_table)
        
        config_layout.addWidget(sensors_box)
        
        return config_widget
    
    def create_results_panel(self):
        """Crée le panneau des résultats"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Onglets pour les différents types de résultats
        self.results_tabs = QTabWidget()
        self.results_tabs.setStyleSheet(self.get_tabs_style())
        
        # Onglet Données brutes
        self.raw_data_tab = self.create_raw_data_tab()
        self.results_tabs.addTab(self.raw_data_tab, "Données Brutes")
        
        # Onglet Matrices de rotation
        self.matrices_tab = self.create_matrices_tab()
        self.results_tabs.addTab(self.matrices_tab, "Matrices de Rotation")
        
        # Onglet Statistiques
        self.stats_tab = self.create_stats_tab()
        self.results_tabs.addTab(self.stats_tab, "Statistiques")
        
        # Onglet Graphiques
        self.plots_tab = self.create_plots_tab()
        self.results_tabs.addTab(self.plots_tab, "Graphiques")
        
        results_layout.addWidget(self.results_tabs)
        
        return results_widget
    
    def create_raw_data_tab(self):
        """Crée l'onglet des données brutes"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Sélecteur de capteur
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Capteur:"))
        
        self.sensor_selector = QComboBox()
        self.sensor_selector.setStyleSheet(self.get_combobox_style())
        self.sensor_selector.currentTextChanged.connect(self.update_raw_data_display)
        selector_layout.addWidget(self.sensor_selector)
        
        selector_layout.addStretch()
        tab_layout.addLayout(selector_layout)
        
        # Tableau des données
        self.raw_data_table = QTableWidget()
        self.raw_data_table.setStyleSheet(self.get_table_style())
        tab_layout.addWidget(self.raw_data_table)
        
        return tab_widget
    
    def create_matrices_tab(self):
        """Crée l'onglet des matrices de rotation"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Zone de texte pour afficher les matrices
        self.matrices_text = QTextEdit()
        self.matrices_text.setStyleSheet("""
            QTextEdit {
                background-color: #353535;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.matrices_text.setReadOnly(True)
        tab_layout.addWidget(self.matrices_text)
        
        return tab_widget
    
    def create_stats_tab(self):
        """Crée l'onglet des statistiques"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Tableau des statistiques
        self.stats_table = QTableWidget()
        self.stats_table.setStyleSheet(self.get_table_style())
        tab_layout.addWidget(self.stats_table)
        
        return tab_widget
    
    def create_plots_tab(self):
        """Crée l'onglet des graphiques"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Placeholder pour les graphiques matplotlib
        placeholder_label = QLabel("Graphiques des séries temporelles\n(À implémenter avec matplotlib)")
        placeholder_label.setStyleSheet("color: #888888; font-style: italic; text-align: center;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(placeholder_label)
        
        return tab_widget
    
    def create_control_buttons(self):
        """Crée les boutons de contrôle"""
        buttons_layout = QHBoxLayout()
        
        # Bouton de recalcul manuel
        recalc_btn = QPushButton("Recalculer Tout")
        recalc_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        recalc_btn.clicked.connect(self.perform_manual_calculation)
        buttons_layout.addWidget(recalc_btn)
        
        # Bouton d'export
        export_btn = QPushButton("Exporter Résultats")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        export_btn.clicked.connect(self.export_results)
        buttons_layout.addWidget(export_btn)
        
        # Bouton de reset
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_btn.clicked.connect(self.reset_all_data)
        buttons_layout.addWidget(reset_btn)
        
        buttons_layout.addStretch()
        
        return buttons_layout
    
    def update_sensor_table(self):
        """Met à jour le tableau des capteurs selon la configuration"""
        # Calculer le nombre total de capteurs
        total_sensors = (self.mru_count_spin.value() + 
                        self.compass_count_spin.value() + 
                        self.octans_count_spin.value())
        
        if total_sensors == 0:
            self.sensors_table.setRowCount(0)
            return
        
        # Configuration du tableau
        self.sensors_table.setRowCount(total_sensors)
        self.sensors_table.setColumnCount(6)
        self.sensors_table.setHorizontalHeaderLabels([
            "ID", "Type", "Nom", "Statut", "Conv. Signe", "Import"
        ])
        
        # Ajuster les colonnes
        header = self.sensors_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Statut
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Conv
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Import
        
        # Remplir le tableau
        row = 0
        sensor_types = [
            ("MRU", self.mru_count_spin.value()),
            ("Compas", self.compass_count_spin.value()),
            ("Octans", self.octans_count_spin.value())
        ]
        
        for sensor_type, count in sensor_types:
            for i in range(count):
                sensor_id = f"{sensor_type}_{i+1}"
                
                # ID du capteur
                id_item = QTableWidgetItem(sensor_id)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.sensors_table.setItem(row, 0, id_item)
                
                # Type de capteur
                type_item = QTableWidgetItem(sensor_type)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.sensors_table.setItem(row, 1, type_item)
                
                # Nom modifiable
                name_item = QTableWidgetItem(f"{sensor_type} {i+1}")
                self.sensors_table.setItem(row, 2, name_item)
                
                # Statut
                status_item = QTableWidgetItem("Non importé")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setBackground(QColor("#aa4444"))
                self.sensors_table.setItem(row, 3, status_item)
                
                # Bouton convention de signe
                sign_btn = QPushButton("Config")
                sign_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #e67e22;
                    }
                """)
                sign_btn.clicked.connect(lambda checked, sid=sensor_id, stype=sensor_type: 
                                       self.configure_sign_conventions(sid, stype))
                self.sensors_table.setCellWidget(row, 4, sign_btn)
                
                # Bouton d'import
                import_btn = QPushButton("Importer")
                import_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8e44ad;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #9b59b6;
                    }
                """)
                import_btn.clicked.connect(lambda checked, sid=sensor_id, stype=sensor_type: 
                                         self.import_sensor_data(sid, stype))
                self.sensors_table.setCellWidget(row, 5, import_btn)
                
                row += 1
        
        print(f"✓ Tableau des capteurs mis à jour: {total_sensors} capteurs configurés")
    
    def configure_sign_conventions(self, sensor_id, sensor_type):
        """Configure les conventions de signe pour un capteur"""
        print(f"Configuration conventions pour {sensor_id} ({sensor_type})")
        
        # Dialogue de configuration des conventions
        dialog = SignConventionDialog(sensor_id, sensor_type, self)
        if dialog.exec_() == dialog.Accepted:
            conventions = dialog.get_conventions()
            
            # Stocker dans le modèle de données
            if self.app_data:
                self.app_data.observation_data['sign_conventions'][sensor_id] = conventions
                print(f"✓ Conventions sauvegardées pour {sensor_id}: {conventions}")
    
    def import_sensor_data(self, sensor_id, sensor_type):
        """Importe les données d'un capteur"""
        print(f"Import de données pour {sensor_id} ({sensor_type})")
        
        try:
            # Ouvrir le dialogue d'import
            import_dialog = ObservationImportDialog(sensor_type, self)
            import_dialog.setWindowTitle(f"Importer {sensor_type} - {sensor_id}")
            
            if import_dialog.exec_() == import_dialog.Accepted:
                # Récupérer les données
                imported_data = import_dialog.get_imported_data()
                
                if imported_data is not None and not imported_data.empty:
                    # Stocker dans le modèle de données
                    if self.app_data:
                        self.app_data.observation_data['sensors'][sensor_id] = imported_data
                        self.app_data.observation_data['sensor_types'][sensor_id] = sensor_type
                        
                        # Mettre à jour le statut dans le tableau
                        self.update_sensor_status(sensor_id, f"Importé ({len(imported_data)} pts)", True)
                        
                        # Mettre à jour la liste des capteurs dans les sélecteurs
                        self.update_sensor_selectors()
                        
                        # Déclencher les calculs en arrière-plan
                        self.trigger_background_calculation()
                        
                        QMessageBox.information(
                            self, 
                            "Import réussi", 
                            f"Données importées pour {sensor_id}:\n"
                            f"- {len(imported_data)} points de données\n"
                            f"- Type: {sensor_type}"
                        )
                        
                        print(f"✓ Import réussi pour {sensor_id}: {len(imported_data)} lignes")
                    else:
                        QMessageBox.warning(self, "Erreur", "Modèle de données non disponible")
                else:
                    QMessageBox.warning(self, "Erreur", "Aucune donnée valide importée")
        
        except Exception as e:
            print(f"✗ Erreur lors de l'import: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur d'import", f"Erreur: {str(e)}")
    
    def update_sensor_status(self, sensor_id, status_text, success=False):
        """Met à jour le statut d'un capteur dans le tableau"""
        for row in range(self.sensors_table.rowCount()):
            id_item = self.sensors_table.item(row, 0)
            if id_item and id_item.text() == sensor_id:
                status_item = self.sensors_table.item(row, 3)
                if status_item:
                    status_item.setText(status_text)
                    color = QColor("#44aa44") if success else QColor("#aa4444")
                    status_item.setBackground(color)
                break
    
    def update_sensor_selectors(self):
        """Met à jour les listes de sélection des capteurs"""
        if not self.app_data:
            return
        
        # Obtenir la liste des capteurs avec données
        sensors_with_data = list(self.app_data.observation_data.get('sensors', {}).keys())
        
        # Mettre à jour le sélecteur de données brutes
        current_sensor = self.sensor_selector.currentText()
        self.sensor_selector.clear()
        self.sensor_selector.addItems(sensors_with_data)
        
        # Restaurer la sélection si possible
        if current_sensor in sensors_with_data:
            self.sensor_selector.setCurrentText(current_sensor)
    
    def trigger_background_calculation(self):
        """Déclenche les calculs en arrière-plan avec un délai"""
        # Arrêter le timer en cours s'il existe
        if self.calc_timer.isActive():
            self.calc_timer.stop()
        
        # Redémarrer le timer avec un délai de 500ms
        self.calc_timer.start(500)
        print("⏱ Calculs en arrière-plan programmés...")
    
    def perform_background_calculation(self):
        """Effectue les calculs en arrière-plan"""
        if not self.app_data:
            return
        
        try:
            print("🔄 Démarrage des calculs en arrière-plan...")
            
            # Effectuer les calculs via le calculator
            results = self.calculator.calculate_all_sensors()
            
            if results:
                # Stocker les résultats
                self.app_data.observation_data['calculations'] = results
                
                # Mettre à jour l'affichage
                self.update_all_displays()
                
                print(f"✓ Calculs terminés pour {len(results)} capteurs")
            else:
                print("ℹ Aucun calcul effectué (pas de données)")
        
        except Exception as e:
            print(f"✗ Erreur lors des calculs: {e}")
            import traceback
            traceback.print_exc()
    
    def perform_manual_calculation(self):
        """Force un recalcul manuel"""
        print("🔄 Recalcul manuel déclenché...")
        self.perform_background_calculation()
    
    def update_all_displays(self):
        """Met à jour tous les affichages"""
        self.update_raw_data_display()
        self.update_matrices_display()
        self.update_stats_display()
    
    def update_raw_data_display(self):
        """Met à jour l'affichage des données brutes"""
        current_sensor = self.sensor_selector.currentText()
        if not current_sensor or not self.app_data:
            self.raw_data_table.setRowCount(0)
            return
        
        sensor_data = self.app_data.observation_data.get('sensors', {}).get(current_sensor)
        if sensor_data is None:
            self.raw_data_table.setRowCount(0)
            return
        
        # Afficher les données dans le tableau
        display_rows = min(100, len(sensor_data))
        self.raw_data_table.setRowCount(display_rows)
        self.raw_data_table.setColumnCount(len(sensor_data.columns))
        self.raw_data_table.setHorizontalHeaderLabels(list(sensor_data.columns))
        
        for row in range(display_rows):
            for col, column_name in enumerate(sensor_data.columns):
                value = sensor_data.iloc[row, col]
                if isinstance(value, float):
                    value_str = f"{value:.6f}"
                else:
                    value_str = str(value)
                
                item = QTableWidgetItem(value_str)
                self.raw_data_table.setItem(row, col, item)
        
        # Ajuster les colonnes
        self.raw_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    
    def update_matrices_display(self):
        """Met à jour l'affichage des matrices de rotation"""
        if not self.app_data:
            return
        
        calculations = self.app_data.observation_data.get('calculations', {})
        if not calculations:
            self.matrices_text.setText("Aucune matrice calculée.")
            return
        
        # Formater l'affichage des matrices
        matrices_text = "=== MATRICES DE ROTATION ===\n\n"
        
        for sensor_id, calc_data in calculations.items():
            matrices_text += f"Capteur: {sensor_id}\n"
            matrices_text += "-" * 40 + "\n"
            
            if 'rotation_matrices' in calc_data:
                for matrix_name, matrix in calc_data['rotation_matrices'].items():
                    matrices_text += f"\n{matrix_name}:\n"
                    matrices_text += np.array2string(matrix, precision=6, suppress_small=True)
                    matrices_text += "\n"
            
            matrices_text += "\n" + "="*40 + "\n\n"
        
        self.matrices_text.setText(matrices_text)
    
    def update_stats_display(self):
        """Met à jour l'affichage des statistiques"""
        if not self.app_data:
            return
        
        calculations = self.app_data.observation_data.get('calculations', {})
        if not calculations:
            self.stats_table.setRowCount(0)
            return
        
        # Préparer les données statistiques
        stats_data = []
        for sensor_id, calc_data in calculations.items():
            if 'statistics' in calc_data:
                stats = calc_data['statistics']
                stats_data.append([
                    sensor_id,
                    f"{stats.get('data_points', 0)}",
                    f"{stats.get('pitch_std', 0):.4f}°",
                    f"{stats.get('roll_std', 0):.4f}°",
                    f"{stats.get('heading_std', 0):.4f}°",
                    f"{stats.get('quality_score', 0):.2f}"
                ])
        
        # Configurer le tableau
        self.stats_table.setRowCount(len(stats_data))
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels([
            "Capteur", "Points", "Pitch σ", "Roll σ", "Heading σ", "Qualité"
        ])
        
        # Remplir le tableau
        for row, data in enumerate(stats_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.stats_table.setItem(row, col, item)
        
        # Ajuster les colonnes
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    
    def export_results(self):
        """Exporte les résultats vers un fichier"""
        print("📄 Export des résultats...")
        # TODO: Implémenter l'export
        QMessageBox.information(self, "Export", "Fonctionnalité d'export à implémenter")
    
    def reset_all_data(self):
        """Réinitialise toutes les données"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Êtes-vous sûr de vouloir réinitialiser toutes les données d'observation ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.app_data:
                self.app_data.observation_data = {
                    'sensors': {},
                    'sensor_types': {},
                    'sign_conventions': {},
                    'calculations': {},
                    'active_sensors': []
                }
            
            # Reset de l'interface
            self.mru_count_spin.setValue(0)
            self.compass_count_spin.setValue(0)
            self.octans_count_spin.setValue(0)
            self.update_sensor_table()
            self.update_all_displays()
            
            print("✓ Toutes les données d'observation réinitialisées")
    
    def on_app_data_changed(self, section):
        """Réagit aux changements dans le modèle de données"""
        if section == "observation":
            self.sync_with_model()
    
    def sync_with_model(self):
        """Synchronise l'interface avec le modèle de données"""
        if not self.app_data:
            return
        
        # TODO: Implémenter la synchronisation si nécessaire
        print("🔄 Synchronisation avec le modèle...")
    
    # Méthodes de style
    def get_groupbox_style(self):
        return """
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px;
            }
        """
    
    def get_spinbox_style(self):
        return """
            QSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
        """
    
    def get_table_style(self):
        return """
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
        """
    
    def get_combobox_style(self):
        return """
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
        """
    
    def get_tabs_style(self):
        return """
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #8e44ad;
            }
        """


class SignConventionDialog(QtWidgets.QDialog):
    """Dialogue pour configurer les conventions de signe d'un capteur"""
    
    def __init__(self, sensor_id, sensor_type, parent=None):
        super().__init__(parent)
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.conventions = {}
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle(f"Conventions de signe - {self.sensor_id}")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Information
        info_label = QLabel(f"Configurez les conventions de signe pour {self.sensor_id} ({self.sensor_type})")
        info_label.setStyleSheet("color: white; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Conventions selon le type de capteur
        conv_group = QGroupBox("Conventions de signe")
        conv_group.setStyleSheet("""
            QGroupBox {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: white;
            }
        """)
        conv_layout = QFormLayout(conv_group)
        
        # Checkboxes pour inverser les signes
        if self.sensor_type in ["MRU", "Octans"]:
            self.pitch_invert = QCheckBox("Inverser Pitch")
            self.pitch_invert.setStyleSheet("color: white;")
            conv_layout.addRow("Pitch:", self.pitch_invert)
            
            self.roll_invert = QCheckBox("Inverser Roll")
            self.roll_invert.setStyleSheet("color: white;")
            conv_layout.addRow("Roll:", self.roll_invert)
        
        if self.sensor_type in ["Compas", "Octans"]:
            self.heading_invert = QCheckBox("Inverser Heading")
            self.heading_invert.setStyleSheet("color: white;")
            conv_layout.addRow("Heading:", self.heading_invert)
        
        layout.addWidget(conv_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 16px; border-radius: 4px;")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Style général
        self.setStyleSheet("QDialog { background-color: #2d2d30; }")
    
    def get_conventions(self):
        """Retourne les conventions configurées"""
        conventions = {}
        
        if self.sensor_type in ["MRU", "Octans"]:
            conventions['pitch_sign'] = -1 if self.pitch_invert.isChecked() else 1
            conventions['roll_sign'] = -1 if self.roll_invert.isChecked() else 1
        
        if self.sensor_type in ["Compas", "Octans"]:
            conventions['heading_sign'] = -1 if self.heading_invert.isChecked() else 1
        
        return conventions