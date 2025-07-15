# import_gnss.py - Version corrigée
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtWidgets, QtCore

class GNSSImportDialog(QtWidgets.QDialog):
    """Dialogue pour importer des données GNSS"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer des données GNSS mobiles")
        self.setMinimumSize(1000, 700)
        self.file_path = ""
        self.data_frame = None
        self.raw_data_lines = []
        self.setupUI()
        self.apply_styles()
    
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
            QTabWidget::tab-bar {
                left: 5px;
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
        """)
    
    def setupUI(self):
        """Configuration de l'interface utilisateur"""
        # Layout principal
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Sélection de fichier
        file_layout = QtWidgets.QHBoxLayout()
        self.file_path_input = QtWidgets.QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("Aucun fichier sélectionné...")
        self.select_file_btn = QtWidgets.QPushButton("Sélectionner un fichier")
        self.select_file_btn.clicked.connect(self.on_select_file)
        file_layout.addWidget(QtWidgets.QLabel("Fichier:"))
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.select_file_btn)
        main_layout.addLayout(file_layout)
        
        # Splitter pour diviser l'écran en deux
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Panneau gauche - données brutes
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.addWidget(QtWidgets.QLabel("Données brutes:"))
        self.raw_data_text = QtWidgets.QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setPlaceholderText("Sélectionnez un fichier pour voir son contenu...")
        left_layout.addWidget(self.raw_data_text)
        splitter.addWidget(left_panel)
        
        # Panneau droit - paramètres et résultats
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Options d'importation
        params_group = QtWidgets.QGroupBox("Paramètres d'importation")
        params_layout = QtWidgets.QFormLayout(params_group)
        
        # Détection automatique du séparateur
        self.separator_combo = QtWidgets.QComboBox()
        self.separator_combo.addItems(["Auto-détection", "Virgule (,)", "Point-virgule (;)", "Tabulation", "Espace"])
        params_layout.addRow("Séparateur:", self.separator_combo)
        
        # Nombre de lignes d'en-tête
        self.header_lines_spin = QtWidgets.QSpinBox()
        self.header_lines_spin.setMinimum(0)
        self.header_lines_spin.setMaximum(10)
        self.header_lines_spin.setValue(0)
        self.header_lines_spin.valueChanged.connect(self.update_preview)
        params_layout.addRow("Lignes d'en-tête:", self.header_lines_spin)
        
        # Colonnes à importer
        columns_group = QtWidgets.QGroupBox("Mapping des colonnes")
        columns_layout = QtWidgets.QFormLayout(columns_group)
        
        self.time_column = QtWidgets.QSpinBox()
        self.time_column.setMinimum(1)
        self.time_column.setMaximum(20)
        self.time_column.setValue(1)
        columns_layout.addRow("Colonne Time:", self.time_column)
        
        self.e_column = QtWidgets.QSpinBox()
        self.e_column.setMinimum(1)
        self.e_column.setMaximum(20)
        self.e_column.setValue(2)
        columns_layout.addRow("Colonne E:", self.e_column)
        
        self.n_column = QtWidgets.QSpinBox()
        self.n_column.setMinimum(1)
        self.n_column.setMaximum(20)
        self.n_column.setValue(3)
        columns_layout.addRow("Colonne N:", self.n_column)
        
        self.h_column = QtWidgets.QSpinBox()
        self.h_column.setMinimum(1)
        self.h_column.setMaximum(20)
        self.h_column.setValue(4)
        columns_layout.addRow("Colonne h:", self.h_column)
        
        right_layout.addWidget(params_group)
        right_layout.addWidget(columns_group)
        
        # Zone pour afficher les résultats
        self.result_table = QtWidgets.QTableWidget()
        right_layout.addWidget(QtWidgets.QLabel("Données traitées:"))
        right_layout.addWidget(self.result_table)
        
        splitter.addWidget(right_panel)
        main_layout.addWidget(splitter)
        
        # Graphiques
        self.figure_widget = QtWidgets.QWidget()
        self.figure_layout = QtWidgets.QVBoxLayout(self.figure_widget)
        self.figure_layout.addWidget(QtWidgets.QLabel("Graphiques:"))
        
        # Conteneur pour les graphiques
        self.tab_widget = QtWidgets.QTabWidget()
        self.figure_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.figure_widget)
        
        # Boutons d'action en bas
        buttons_layout = QtWidgets.QHBoxLayout()
        self.process_btn = QtWidgets.QPushButton("Traiter les données")
        self.process_btn.clicked.connect(self.process_data)
        self.reset_btn = QtWidgets.QPushButton("Réinitialiser")
        self.reset_btn.clicked.connect(self.reset_form)
        self.validate_btn = QtWidgets.QPushButton("Valider")
        self.validate_btn.clicked.connect(self.accept)
        self.cancel_btn = QtWidgets.QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        # Style spécial pour les boutons d'action
        self.process_btn.setStyleSheet("background-color: #3498db;")
        self.validate_btn.setStyleSheet("background-color: #27ae60;")
        self.cancel_btn.setStyleSheet("background-color: #e74c3c;")
        
        buttons_layout.addWidget(self.process_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.validate_btn)
        buttons_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(buttons_layout)
        
        # État initial des boutons
        self.process_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
    
    def detect_separator(self, file_path):
        """Détecte automatiquement le séparateur utilisé dans le fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()
            
            # Compter les occurrences de différents séparateurs
            separators = {',': 'comma', ';': 'semicolon', '\t': 'tab', ' ': 'space'}
            counts = {}
            
            for sep, name in separators.items():
                count1 = first_line.count(sep)
                count2 = second_line.count(sep)
                # Un bon séparateur devrait avoir le même nombre d'occurrences sur les deux lignes
                if count1 > 0 and count1 == count2:
                    counts[sep] = count1
            
            if counts:
                # Retourner le séparateur avec le plus d'occurrences
                best_sep = max(counts, key=counts.get)
                return best_sep
            else:
                return ','  # Par défaut
                
        except Exception as e:
            print(f"Erreur lors de la détection du séparateur: {e}")
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
        """Gère l'événement de sélection de fichier"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 
            "Sélectionner le fichier de données GNSS", 
            "", 
            "Fichiers texte (*.txt);;Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_input.setText(file_path)
            
            # Afficher les premières lignes du fichier
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.raw_data_lines = f.readlines()
                
                # Afficher les 30 premières lignes
                preview_lines = self.raw_data_lines[:30]
                self.raw_data_text.setText("".join(preview_lines))
                
                self.process_btn.setEnabled(True)
                
                # Auto-détection et configuration initiale
                separator = self.detect_separator(file_path)
                self.auto_detect_columns(separator)
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier: {str(e)}")
                print(f"Erreur détaillée: {e}")
    
    def auto_detect_columns(self, separator):
        """Détecte automatiquement la configuration des colonnes"""
        try:
            if not self.raw_data_lines:
                return
            
            # Analyser la première ligne de données (après les en-têtes)
            data_line_index = self.header_lines_spin.value()
            if data_line_index < len(self.raw_data_lines):
                data_line = self.raw_data_lines[data_line_index].strip()
                columns = data_line.split(separator)
                
                print(f"Ligne de données: {data_line}")
                print(f"Colonnes détectées: {columns}")
                print(f"Nombre de colonnes: {len(columns)}")
                
                # Mettre à jour les maximums des spin boxes
                max_cols = len(columns)
                self.time_column.setMaximum(max_cols)
                self.e_column.setMaximum(max_cols)
                self.n_column.setMaximum(max_cols)
                self.h_column.setMaximum(max_cols)
                
                # Configuration par défaut si on a au moins 4 colonnes
                if len(columns) >= 4:
                    self.time_column.setValue(1)
                    self.e_column.setValue(2)
                    self.n_column.setValue(3)
                    self.h_column.setValue(4)
                
        except Exception as e:
            print(f"Erreur lors de l'auto-détection des colonnes: {e}")
    
    def update_preview(self):
        """Met à jour l'aperçu quand les paramètres changent"""
        if self.file_path:
            self.auto_detect_columns(self.get_separator())
    
    def process_data(self):
        """Traite les données du fichier selon les paramètres spécifiés"""
        try:
            if not self.file_path:
                QtWidgets.QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un fichier.")
                return
            
            # Obtenir les paramètres
            separator = self.get_separator()
            skiprows = self.header_lines_spin.value()
            
            print(f"Traitement avec séparateur: '{separator}', skip_rows: {skiprows}")
            
            # Convertir les indices en base 0 pour pandas
            time_col = self.time_column.value() - 1
            e_col = self.e_column.value() - 1
            n_col = self.n_column.value() - 1
            h_col = self.h_column.value() - 1
            
            # Lire le fichier avec pandas
            try:
                df = pd.read_csv(
                    self.file_path, 
                    sep=separator, 
                    skiprows=skiprows, 
                    header=None,
                    encoding='utf-8',
                    on_bad_lines='skip'  # Ignorer les lignes mal formées
                )
                print(f"DataFrame lu: {df.shape}")
                print(f"Colonnes disponibles: {df.columns.tolist()}")
                print(f"Premières lignes:\n{df.head()}")
                
            except Exception as e:
                # Essayer avec un autre encodage
                try:
                    df = pd.read_csv(
                        self.file_path, 
                        sep=separator, 
                        skiprows=skiprows, 
                        header=None,
                        encoding='latin-1',
                        on_bad_lines='skip'
                    )
                    print("Fichier lu avec encodage latin-1")
                except Exception as e2:
                    raise Exception(f"Impossible de lire le fichier avec les encodages UTF-8 ou Latin-1: {e2}")
            
            # Vérifier si nous avons assez de colonnes
            max_col_needed = max(time_col, e_col, n_col, h_col)
            if df.shape[1] <= max_col_needed:
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Avertissement", 
                    f"Le fichier n'a que {df.shape[1]} colonnes, mais vous avez spécifié la colonne {max_col_needed + 1}."
                )
                return
            
            # Extraire les colonnes et les renommer
            self.data_frame = pd.DataFrame({
                'Time': df.iloc[:, time_col],
                'E': df.iloc[:, e_col],
                'N': df.iloc[:, n_col],
                'h': df.iloc[:, h_col]
            })
            
            print(f"DataFrame créé: {self.data_frame.shape}")
            print(f"Types de données:\n{self.data_frame.dtypes}")
            
            # Nettoyer et convertir les données
            self.clean_and_convert_data()
            
            # Afficher le résultat dans le tableau
            self.display_data_in_table()
            
            # Créer les graphiques
            self.create_plots()
            
            # Activer le bouton de validation
            self.validate_btn.setEnabled(True)
            
            QtWidgets.QMessageBox.information(
                self, 
                "Succès", 
                f"Données traitées avec succès: {len(self.data_frame)} lignes importées."
            )
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement des données: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def clean_and_convert_data(self):
        """Nettoie et convertit les données en types numériques appropriés"""
        try:
            # Supprimer les lignes vides
            self.data_frame = self.data_frame.dropna()
            
            # Convertir les colonnes E, N, h en numérique
            for col in ['E', 'N', 'h']:
                self.data_frame[col] = pd.to_numeric(self.data_frame[col], errors='coerce')
            
            # Gestion spéciale pour la colonne Time
            try:
                # Essayer de convertir directement en numérique
                self.data_frame['Time_num'] = pd.to_numeric(self.data_frame['Time'], errors='raise')
            except:
                try:
                    # Si ça échoue, vérifier si c'est du format HH:MM:SS
                    if ':' in str(self.data_frame['Time'].iloc[0]):
                        self.data_frame['Time_num'] = self.data_frame['Time'].apply(
                            self.convert_time_to_seconds
                        )
                    else:
                        # Sinon, utiliser l'index comme temps
                        self.data_frame['Time_num'] = self.data_frame.index.astype(float)
                except:
                    # En dernier recours, utiliser l'index
                    self.data_frame['Time_num'] = self.data_frame.index.astype(float)
            
            # Supprimer les lignes avec des valeurs NaN après conversion
            initial_count = len(self.data_frame)
            self.data_frame = self.data_frame.dropna()
            final_count = len(self.data_frame)
            
            if initial_count != final_count:
                print(f"Suppression de {initial_count - final_count} lignes avec des valeurs invalides")
            
            print(f"Données nettoyées: {len(self.data_frame)} lignes valides")
            
        except Exception as e:
            print(f"Erreur lors du nettoyage des données: {e}")
            raise
    
    def convert_time_to_seconds(self, time_str):
        """Convertit une chaîne de temps HH:MM:SS en secondes depuis minuit"""
        try:
            time_parts = str(time_str).split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(float, time_parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:
                minutes, seconds = map(float, time_parts)
                return minutes * 60 + seconds
            else:
                return float(time_str)  # Essayer de convertir directement
        except:
            return 0  # Valeur par défaut
    
    def display_data_in_table(self):
        """Affiche les données dans le tableau de résultats"""
        if self.data_frame is None:
            return
        
        # Configurer le tableau
        display_rows = min(100, len(self.data_frame))
        self.result_table.setRowCount(display_rows)
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['Time', 'E', 'N', 'h', 'Time_num'])
        
        # Remplir le tableau avec les données
        for row in range(display_rows):
            for col, colname in enumerate(['Time', 'E', 'N', 'h', 'Time_num']):
                value = self.data_frame[colname].iloc[row]
                if isinstance(value, float):
                    value_str = f"{value:.6f}"
                else:
                    value_str = str(value)
                self.result_table.setItem(row, col, QtWidgets.QTableWidgetItem(value_str))
        
        # Ajuster les colonnes
        self.result_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        if len(self.data_frame) > 100:
            self.result_table.setToolTip(f"Affichage des 100 premières lignes sur {len(self.data_frame)} total")
    
    def create_plots(self):
        """Crée les graphiques pour les données E, N, h en fonction du temps"""
        if self.data_frame is None:
            return
        
        # Effacer les onglets existants
        self.tab_widget.clear()
        
        try:
            # Créer les graphiques E, N, h
            for coord in ['E', 'N', 'h']:
                # Créer un widget pour contenir le graphique
                plot_widget = QtWidgets.QWidget()
                plot_layout = QtWidgets.QVBoxLayout(plot_widget)
                
                # Créer la figure et le canvas
                figure = plt.figure(figsize=(8, 5))
                figure.patch.set_facecolor('#353535')
                ax = figure.add_subplot(111)
                ax.set_facecolor('#353535')
                
                # Tracer les données
                ax.plot(self.data_frame['Time_num'], self.data_frame[coord], '-', color='cyan', linewidth=1)
                ax.set_xlabel('Temps', color='white')
                ax.set_ylabel(coord, color='white')
                ax.set_title(f'{coord} en fonction du temps', color='white')
                ax.grid(True, alpha=0.3)
                
                # Style sombre pour les axes
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
                
                figure.tight_layout()
                
                # Convertir la figure en QWidget
                from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
                canvas = FigureCanvas(figure)
                canvas.setStyleSheet("background-color: #353535;")
                plot_layout.addWidget(canvas)
                
                # Ajouter au tabWidget
                self.tab_widget.addTab(plot_widget, coord)
                
        except Exception as e:
            print(f"Erreur lors de la création des graphiques: {e}")
            # Ajouter un onglet d'erreur
            error_widget = QtWidgets.QWidget()
            error_layout = QtWidgets.QVBoxLayout(error_widget)
            error_label = QtWidgets.QLabel(f"Erreur lors de la création des graphiques:\n{str(e)}")
            error_label.setStyleSheet("color: red;")
            error_layout.addWidget(error_label)
            self.tab_widget.addTab(error_widget, "Erreur")
    
    def reset_form(self):
        """Réinitialise le formulaire"""
        self.file_path = ""
        self.file_path_input.setText("")
        self.raw_data_text.setText("")
        self.raw_data_lines = []
        self.separator_combo.setCurrentIndex(0)
        self.header_lines_spin.setValue(0)
        self.time_column.setValue(1)
        self.e_column.setValue(2)
        self.n_column.setValue(3)
        self.h_column.setValue(4)
        self.result_table.setRowCount(0)
        self.tab_widget.clear()
        self.data_frame = None
        self.process_btn.setEnabled(False)
        self.validate_btn.setEnabled(False)
    
    def get_imported_data(self):
        """Retourne les données importées"""
        return self.data_frame