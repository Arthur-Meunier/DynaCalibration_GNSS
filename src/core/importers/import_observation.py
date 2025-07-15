# import_observation.py
import os
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QFormLayout, QSpinBox,
    QTableWidget, QTableWidgetItem, QTabWidget, 
    QTextEdit, QSplitter, QFileDialog, QMessageBox,
    QComboBox, QHeaderView, QWidget, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ObservationImportDialog(QDialog):
    """Dialogue pour importer des données d'observation selon le type de capteur"""
    
    def __init__(self, sensor_type, parent=None):
        super().__init__(parent)
        self.sensor_type = sensor_type
        self.file_path = ""
        self.data_frame = None
        self.raw_data_lines = []
        
        # Définir les colonnes attendues selon le type de capteur
        self.expected_columns = self.get_expected_columns()
        
        self.setupUI()
        self.apply_styles()
        
        print(f"✓ Dialogue d'import initialisé pour {sensor_type}")
    
    def get_expected_columns(self):
        """Retourne les colonnes attendues selon le type de capteur"""
        if self.sensor_type == "MRU":
            return ["Time", "Pitch", "Roll"]
        elif self.sensor_type == "Compas":
            return ["Time", "Heading"]
        elif self.sensor_type == "Octans":
            return ["Time", "Pitch", "Roll", "Heading"]
        else:
            return ["Time"]  # Par défaut
    
    def apply_styles(self):
        """Applique les styles sombres à l'interface"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d30;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QGroupBox {
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QTableWidget {
                background-color: #353535;
                color: white;
                gridline-color: #555555;
                border: 1px solid #555555;
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
            QTextEdit {
                background-color: #353535;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-bottom-color: #555555;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background-color: #8e44ad;
            }
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QCheckBox {
                color: white;
            }
        """)
    
    def setupUI(self):
        """Configuration de l'interface utilisateur"""
        self.setWindowTitle(f"Importer données {self.sensor_type}")
        self.setMinimumSize(1000, 700)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Information sur le type de capteur
        info_label = QLabel(f"Import de données pour capteur {self.sensor_type}")
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_label.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(info_label)
        
        # Colonnes attendues
        expected_text = f"Colonnes attendues: {', '.join(self.expected_columns)}"
        expected_label = QLabel(expected_text)
        expected_label.setStyleSheet("color: #cccccc; font-style: italic; margin-bottom: 10px;")
        main_layout.addWidget(expected_label)
        
        # Sélection de fichier
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("Aucun fichier sélectionné...")
        self.select_file_btn = QPushButton("Sélectionner un fichier")
        self.select_file_btn.clicked.connect(self.on_select_file)
        file_layout.addWidget(QLabel("Fichier:"))
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.select_file_btn)
        main_layout.addLayout(file_layout)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau gauche - données brutes et paramètres
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit - données traitées et résultats
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)
        
        # Boutons d'action
        buttons_layout = self.create_buttons()
        main_layout.addLayout(buttons_layout)
        
        # État initial
        self.process_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
    
    def create_left_panel(self):
        """Crée le panneau gauche avec données brutes et paramètres"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Données brutes
        raw_group = QGroupBox("Données brutes")
        raw_layout = QVBoxLayout(raw_group)
        
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setPlaceholderText("Sélectionnez un fichier pour voir son contenu...")
        self.raw_data_text.setMaximumHeight(200)
        raw_layout.addWidget(self.raw_data_text)
        
        left_layout.addWidget(raw_group)
        
        # Paramètres d'importation
        params_group = QGroupBox("Paramètres d'importation")
        params_layout = QFormLayout(params_group)
        
        # Séparateur
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(["Auto-détection", "Virgule (,)", "Point-virgule (;)", "Tabulation", "Espace"])
        params_layout.addRow("Séparateur:", self.separator_combo)
        
        # Lignes d'en-tête
        self.header_lines_spin = QSpinBox()
        self.header_lines_spin.setRange(0, 10)
        self.header_lines_spin.setValue(0)
        self.header_lines_spin.valueChanged.connect(self.update_preview)
        params_layout.addRow("Lignes d'en-tête:", self.header_lines_spin)
        
        left_layout.addWidget(params_group)
        
        # Mapping des colonnes
        mapping_group = QGroupBox("Mapping des colonnes")
        mapping_layout = QFormLayout(mapping_group)
        
        self.column_spinboxes = {}
        for i, col_name in enumerate(self.expected_columns):
            spinbox = QSpinBox()
            spinbox.setRange(1, 20)
            spinbox.setValue(i + 1)
            self.column_spinboxes[col_name] = spinbox
            mapping_layout.addRow(f"Colonne {col_name}:", spinbox)
        
        left_layout.addWidget(mapping_group)
        
        # Conventions de données
        if self.sensor_type != "Compas":  # Compas n'a que heading
            conventions_group = QGroupBox("Conventions d'angles")
            conventions_layout = QFormLayout(conventions_group)
            
            # Format des angles
            self.angle_format_combo = QComboBox()
            self.angle_format_combo.addItems(["Degrés", "Radians"])
            conventions_layout.addRow("Format:", self.angle_format_combo)
            
            # Plage des angles
            if "Pitch" in self.expected_columns:
                self.pitch_range_combo = QComboBox()
                self.pitch_range_combo.addItems(["±90°", "±180°", "0-360°"])
                conventions_layout.addRow("Plage Pitch:", self.pitch_range_combo)
            
            if "Roll" in self.expected_columns:
                self.roll_range_combo = QComboBox()
                self.roll_range_combo.addItems(["±90°", "±180°", "0-360°"])
                conventions_layout.addRow("Plage Roll:", self.roll_range_combo)
            
            if "Heading" in self.expected_columns:
                self.heading_range_combo = QComboBox()
                self.heading_range_combo.addItems(["0-360°", "±180°"])
                conventions_layout.addRow("Plage Heading:", self.heading_range_combo)
            
            left_layout.addWidget(conventions_group)
        
        left_layout.addStretch()
        return left_widget
    
    def create_right_panel(self):
        """Crée le panneau droit avec résultats"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Onglets pour les résultats
        self.result_tabs = QTabWidget()
        
        # Onglet tableau
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        table_layout.addWidget(QLabel("Données traitées:"))
        self.result_table = QTableWidget()
        table_layout.addWidget(self.result_table)
        
        self.result_tabs.addTab(table_tab, "Tableau")
        
        # Onglet graphiques (placeholder)
        plot_tab = QWidget()
        plot_layout = QVBoxLayout(plot_tab)
        
        self.plot_text = QTextEdit()
        self.plot_text.setReadOnly(True)
        self.plot_text.setText("Graphiques des séries temporelles\n(Affichage après traitement)")
        plot_layout.addWidget(self.plot_text)
        
        self.result_tabs.addTab(plot_tab, "Graphiques")
        
        # Onglet statistiques
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        self.result_tabs.addTab(stats_tab, "Statistiques")
        
        right_layout.addWidget(self.result_tabs)
        
        return right_widget
    
    def create_buttons(self):
        """Crée les boutons d'action"""
        buttons_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("Traiter les données")
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setStyleSheet("background-color: #3498db;")
        
        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_form)
        
        self.validate_btn = QPushButton("Valider")
        self.validate_btn.clicked.connect(self.accept)
        self.validate_btn.setStyleSheet("background-color: #27ae60;")
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("background-color: #e74c3c;")
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.validate_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        return buttons_layout
    
    def detect_separator(self, file_path):
        """Détecte automatiquement le séparateur du fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()
            
            separators = {',': 'comma', ';': 'semicolon', '\t': 'tab', ' ': 'space'}
            counts = {}
            
            for sep, name in separators.items():
                count1 = first_line.count(sep)
                count2 = second_line.count(sep)
                if count1 > 0 and count1 == count2:
                    counts[sep] = count1
            
            if counts:
                best_sep = max(counts, key=counts.get)
                return best_sep
            else:
                return ','
                
        except Exception as e:
            print(f"Erreur détection séparateur: {e}")
            return ','
    
    def get_separator(self):
        """Retourne le séparateur sélectionné"""
        separator_text = self.separator_combo.currentText()
        if separator_text == "Auto-détection":
            return self.detect_separator(self.file_path) if self.file_path else ','
        elif separator_text == "Virgule (,)":
            return ','
        elif separator_text == "Point-virgule (;)":
            return ';'
        elif separator_text == "Tabulation":
            return '\t'
        elif separator_text == "Espace":
            return ' '
        else:
            return ','
    
    def on_select_file(self):
        """Gère la sélection de fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Sélectionner le fichier de données {self.sensor_type}", 
            "", 
            "Fichiers texte (*.txt);;Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_input.setText(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.raw_data_lines = f.readlines()
                
                # Afficher aperçu
                preview_lines = self.raw_data_lines[:20]
                self.raw_data_text.setText("".join(preview_lines))
                
                self.process_btn.setEnabled(True)
                
                # Auto-détection
                separator = self.detect_separator(file_path)
                self.auto_detect_columns(separator)
                
                print(f"✓ Fichier sélectionné: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier: {str(e)}")
                print(f"Erreur lecture fichier: {e}")
    
    def auto_detect_columns(self, separator):
        """Détecte automatiquement les colonnes"""
        try:
            if not self.raw_data_lines:
                return
            
            data_line_index = self.header_lines_spin.value()
            if data_line_index < len(self.raw_data_lines):
                data_line = self.raw_data_lines[data_line_index].strip()
                columns = data_line.split(separator)
                
                print(f"Colonnes détectées: {len(columns)} colonnes")
                
                # Mettre à jour les maximums
                max_cols = len(columns)
                for spinbox in self.column_spinboxes.values():
                    spinbox.setMaximum(max_cols)
                
                # Configuration automatique si nombre de colonnes correspond
                if len(columns) >= len(self.expected_columns):
                    for i, col_name in enumerate(self.expected_columns):
                        self.column_spinboxes[col_name].setValue(i + 1)
                
        except Exception as e:
            print(f"Erreur auto-détection: {e}")
    
    def update_preview(self):
        """Met à jour l'aperçu"""
        if self.file_path:
            self.auto_detect_columns(self.get_separator())
    
    def process_data(self):
        """Traite les données du fichier"""
        try:
            if not self.file_path:
                QMessageBox.warning(self, "Erreur", "Sélectionnez d'abord un fichier")
                return
            
            print(f"🔄 Traitement des données {self.sensor_type}...")
            
            # Paramètres d'importation
            separator = self.get_separator()
            skiprows = self.header_lines_spin.value()
            
            # Colonnes à extraire
            column_indices = {}
            for col_name, spinbox in self.column_spinboxes.items():
                column_indices[col_name] = spinbox.value() - 1  # Base 0
            
            # Lecture du fichier
            try:
                df = pd.read_csv(
                    self.file_path, 
                    sep=separator, 
                    skiprows=skiprows, 
                    header=None,
                    encoding='utf-8',
                    on_bad_lines='skip'
                )
            except:
                df = pd.read_csv(
                    self.file_path, 
                    sep=separator, 
                    skiprows=skiprows, 
                    header=None,
                    encoding='latin-1',
                    on_bad_lines='skip'
                )
            
            print(f"DataFrame lu: {df.shape}")
            
            # Vérifier les colonnes
            max_col_needed = max(column_indices.values())
            if df.shape[1] <= max_col_needed:
                QMessageBox.warning(
                    self, 
                    "Erreur", 
                    f"Le fichier n'a que {df.shape[1]} colonnes, colonne {max_col_needed + 1} demandée"
                )
                return
            
            # Extraire et renommer les colonnes
            extracted_data = {}
            for col_name, col_index in column_indices.items():
                extracted_data[col_name] = df.iloc[:, col_index]
            
            self.data_frame = pd.DataFrame(extracted_data)
            
            # Nettoyer et convertir
            self.clean_and_convert_data()
            
            # Afficher résultats
            self.display_results()
            
            # Calculer statistiques
            self.calculate_statistics()
            
            self.validate_btn.setEnabled(True)
            
            QMessageBox.information(
                self, 
                "Succès", 
                f"Données {self.sensor_type} traitées: {len(self.data_frame)} points"
            )
            
            print(f"✓ Traitement terminé: {len(self.data_frame)} points valides")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de traitement: {str(e)}")
            print(f"Erreur traitement: {e}")
            import traceback
            traceback.print_exc()
    
    def clean_and_convert_data(self):
        """Nettoie et convertit les données"""
        try:
            # Supprimer lignes vides
            self.data_frame = self.data_frame.dropna()
            
            # Traitement de la colonne Time
            self.convert_time_column()
            
            # Traitement des colonnes d'angles
            self.convert_angle_columns()
            
            # Supprimer les valeurs NaN après conversion
            initial_count = len(self.data_frame)
            self.data_frame = self.data_frame.dropna()
            final_count = len(self.data_frame)
            
            if initial_count != final_count:
                print(f"Suppression de {initial_count - final_count} lignes invalides")
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            raise
    
    def convert_time_column(self):
        """Convertit la colonne Time"""
        try:
            # Essayer conversion directe
            self.data_frame['Time_num'] = pd.to_numeric(self.data_frame['Time'], errors='raise')
        except:
            try:
                # Format HH:MM:SS
                if ':' in str(self.data_frame['Time'].iloc[0]):
                    self.data_frame['Time_num'] = self.data_frame['Time'].apply(
                        self.convert_time_to_seconds
                    )
                else:
                    self.data_frame['Time_num'] = self.data_frame.index.astype(float)
            except:
                self.data_frame['Time_num'] = self.data_frame.index.astype(float)
    
    def convert_time_to_seconds(self, time_str):
        """Convertit HH:MM:SS en secondes"""
        try:
            time_parts = str(time_str).split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(float, time_parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:
                minutes, seconds = map(float, time_parts)
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return 0
    
    def convert_angle_columns(self):
        """Convertit les colonnes d'angles selon les conventions"""
        # Format (degrés/radians)
        is_radians = False
        if hasattr(self, 'angle_format_combo'):
            is_radians = self.angle_format_combo.currentText() == "Radians"
        
        # Convertir chaque angle
        angle_columns = [col for col in self.expected_columns if col != "Time"]
        
        for col in angle_columns:
            if col in self.data_frame.columns:
                # Conversion vers numérique
                self.data_frame[col] = pd.to_numeric(self.data_frame[col], errors='coerce')
                
                # Conversion radians -> degrés si nécessaire
                if is_radians:
                    self.data_frame[col] = np.degrees(self.data_frame[col])
                
                # Normalisation des plages d'angles
                if col == "Pitch" and hasattr(self, 'pitch_range_combo'):
                    self.normalize_angle_range(col, self.pitch_range_combo.currentText())
                elif col == "Roll" and hasattr(self, 'roll_range_combo'):
                    self.normalize_angle_range(col, self.roll_range_combo.currentText())
                elif col == "Heading" and hasattr(self, 'heading_range_combo'):
                    self.normalize_angle_range(col, self.heading_range_combo.currentText())
    
    def normalize_angle_range(self, column, range_type):
        """Normalise la plage d'un angle"""
        if range_type == "±90°":
            # Limiter à ±90°
            self.data_frame[column] = np.clip(self.data_frame[column], -90, 90)
        elif range_type == "±180°":
            # Convertir vers ±180°
            self.data_frame[column] = ((self.data_frame[column] + 180) % 360) - 180
        elif range_type == "0-360°":
            # Convertir vers 0-360°
            self.data_frame[column] = self.data_frame[column] % 360
    
    def display_results(self):
        """Affiche les résultats dans le tableau"""
        if self.data_frame is None:
            return
        
        # Configuration du tableau
        display_rows = min(100, len(self.data_frame))
        self.result_table.setRowCount(display_rows)
        self.result_table.setColumnCount(len(self.data_frame.columns))
        self.result_table.setHorizontalHeaderLabels(list(self.data_frame.columns))
        
        # Remplir le tableau
        for row in range(display_rows):
            for col, column_name in enumerate(self.data_frame.columns):
                value = self.data_frame.iloc[row, col]
                if isinstance(value, float):
                    value_str = f"{value:.6f}"
                else:
                    value_str = str(value)
                
                item = QTableWidgetItem(value_str)
                self.result_table.setItem(row, col, item)
        
        # Ajuster colonnes
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        if len(self.data_frame) > 100:
            self.result_table.setToolTip(f"Affichage de 100 lignes sur {len(self.data_frame)}")
    
    def calculate_statistics(self):
        """Calcule et affiche les statistiques"""
        if self.data_frame is None:
            return
        
        stats_text = f"=== STATISTIQUES {self.sensor_type} ===\n\n"
        stats_text += f"Nombre total de points: {len(self.data_frame)}\n\n"
        
        # Statistiques par colonne
        for col in self.data_frame.columns:
            if col in ['Time', 'Time_num']:
                continue
            
            if col in self.data_frame.columns:
                data = self.data_frame[col].dropna()
                if len(data) > 0:
                    stats_text += f"{col}:\n"
                    stats_text += f"  Moyenne: {data.mean():.4f}°\n"
                    stats_text += f"  Écart-type: {data.std():.4f}°\n"
                    stats_text += f"  Minimum: {data.min():.4f}°\n"
                    stats_text += f"  Maximum: {data.max():.4f}°\n"
                    stats_text += f"  Étendue: {data.max() - data.min():.4f}°\n\n"
        
        # Période d'échantillonnage
        if 'Time_num' in self.data_frame.columns and len(self.data_frame) > 1:
            time_diff = np.diff(self.data_frame['Time_num'].values)
            mean_dt = np.mean(time_diff)
            std_dt = np.std(time_diff)
            stats_text += f"Échantillonnage:\n"
            stats_text += f"  Période moyenne: {mean_dt:.3f}s\n"
            stats_text += f"  Écart-type période: {std_dt:.3f}s\n"
            stats_text += f"  Fréquence moyenne: {1/mean_dt:.2f}Hz\n"
        
        self.stats_text.setText(stats_text)
    
    def reset_form(self):
        """Réinitialise le formulaire"""
        self.file_path = ""
        self.file_path_input.setText("")
        self.raw_data_text.setText("")
        self.raw_data_lines = []
        
        # Reset paramètres
        self.separator_combo.setCurrentIndex(0)
        self.header_lines_spin.setValue(0)
        
        # Reset colonnes
        for i, spinbox in enumerate(self.column_spinboxes.values()):
            spinbox.setValue(i + 1)
        
        # Reset résultats
        self.result_table.setRowCount(0)
        self.stats_text.setText("")
        
        self.data_frame = None
        self.process_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
        
        print("✓ Formulaire réinitialisé")
    
    def get_imported_data(self):
        """Retourne les données importées"""
        return self.data_frame