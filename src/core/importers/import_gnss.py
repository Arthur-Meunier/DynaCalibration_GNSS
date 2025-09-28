# core/importers/import_gnss_fixed.py - Importeur GNSS robuste et corrigé

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QFormLayout, QSpinBox, QComboBox,
    QProgressBar, QTextEdit, QFileDialog, QMessageBox, QCheckBox,
    QFrame, QHeaderView, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

class GNSSDataProcessor(QThread):
    """Thread de traitement des données GNSS de façon robuste"""
    
    # Signaux pour communication avec l'interface
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    data_processed = pyqtSignal(object)  # DataFrame traité
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_path, config):
        super().__init__()
        self.file_path = file_path
        self.config = config
        self.is_cancelled = False
    
    def cancel_processing(self):
        """Annule le traitement en cours"""
        self.is_cancelled = True
    
    def run(self):
        """Traite les données GNSS de façon robuste"""
        try:
            self.status_updated.emit("🔍 Analyse du fichier...")
            self.progress_updated.emit(10)
            
            # Vérification de l'annulation
            if self.is_cancelled:
                return
            
            # === LECTURE SÉCURISÉE DU FICHIER ===
            df = self.safe_read_file()
            if df is None:
                return
            
            self.progress_updated.emit(30)
            self.status_updated.emit("🔧 Validation des données...")
            
            # === VALIDATION ET NETTOYAGE ===
            df_cleaned = self.validate_and_clean_data(df)
            if df_cleaned is None:
                return
            
            self.progress_updated.emit(60)
            self.status_updated.emit("📊 Traitement des coordonnées...")
            
            # === TRAITEMENT DES COORDONNÉES ===
            df_processed = self.process_coordinates(df_cleaned)
            if df_processed is None:
                return
            
            self.progress_updated.emit(80)
            self.status_updated.emit("✅ Finalisation...")
            
            # === FINALISATION ===
            df_final = self.finalize_data(df_processed)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("✅ Traitement terminé avec succès")
            
            # Émettre les données traitées
            self.data_processed.emit(df_final)
            
        except Exception as e:
            error_msg = f"Erreur lors du traitement: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def safe_read_file(self):
        """Lecture sécurisée du fichier avec différents encodages"""
        try:
            separator = self.config.get('separator', ',')
            skiprows = self.config.get('skiprows', 0)
            
            # Essayer différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    if self.is_cancelled:
                        return None
                    
                    self.status_updated.emit(f"📖 Lecture avec encodage {encoding}...")
                    
                    df = pd.read_csv(
                        self.file_path,
                        sep=separator,
                        skiprows=skiprows,
                        header=None,
                        encoding=encoding,
                        on_bad_lines='skip',
                        low_memory=False
                    )
                    
                    if not df.empty:
                        print(f"✓ Fichier lu avec succès (encodage: {encoding})")
                        print(f"✓ Dimensions: {df.shape}")
                        return df
                        
                except Exception as e:
                    print(f"⚠ Échec encodage {encoding}: {e}")
                    continue
            
            # Si tous les encodages échouent
            raise Exception("Impossible de lire le fichier avec les encodages disponibles")
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur lecture fichier: {str(e)}")
            return None
    
    def validate_and_clean_data(self, df):
        """Valide et nettoie les données"""
        try:
            if self.is_cancelled:
                return None
            
            # Vérifier les colonnes requises
            required_cols = [
                self.config.get('time_col', 0),
                self.config.get('e_col', 1),
                self.config.get('n_col', 2),
                self.config.get('h_col', 3)
            ]
            
            max_col = max(required_cols)
            if df.shape[1] <= max_col:
                raise Exception(f"Le fichier n'a que {df.shape[1]} colonnes, colonne {max_col + 1} requise")
            
            # Extraire les colonnes d'intérêt
            df_selected = df.iloc[:, required_cols].copy()
            df_selected.columns = ['Time', 'E', 'N', 'h']
            
            # Supprimer les lignes vides ou avec des valeurs manquantes
            original_rows = len(df_selected)
            df_selected = df_selected.dropna()
            
            if len(df_selected) == 0:
                raise Exception("Aucune donnée valide après nettoyage")
            
            removed_rows = original_rows - len(df_selected)
            if removed_rows > 0:
                print(f"⚠ {removed_rows} lignes supprimées (valeurs manquantes)")
            
            return df_selected
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur validation: {str(e)}")
            return None
    
    def process_coordinates(self, df):
        """Traite et valide les coordonnées"""
        try:
            if self.is_cancelled:
                return None
            
            # Conversion des coordonnées en numérique
            coord_columns = ['E', 'N', 'h']
            
            for col in coord_columns:
                try:
                    # Essayer conversion directe
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    # Si échec, essayer de nettoyer d'abord
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Supprimer les lignes avec des coordonnées invalides
            original_rows = len(df)
            df = df.dropna(subset=coord_columns)
            
            if len(df) == 0:
                raise Exception("Aucune coordonnée valide trouvée")
            
            removed_rows = original_rows - len(df)
            if removed_rows > 0:
                print(f"⚠ {removed_rows} lignes supprimées (coordonnées invalides)")
            
            # Validation des plages de coordonnées (exemple pour coordonnées UTM)
            coord_ranges = {
                'E': (100000, 900000),  # Plage UTM Est approximative
                'N': (1000000, 9000000),  # Plage UTM Nord approximative  
                'h': (-1000, 10000)  # Plage altitude raisonnable
            }
            
            for col, (min_val, max_val) in coord_ranges.items():
                outliers = (df[col] < min_val) | (df[col] > max_val)
                outlier_count = outliers.sum()
                
                if outlier_count > 0:
                    print(f"⚠ {outlier_count} valeurs aberrantes détectées pour {col}")
                    # Optionnel: supprimer les valeurs aberrantes
                    # df = df[~outliers]
            
            return df
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur traitement coordonnées: {str(e)}")
            return None
    
    def finalize_data(self, df):
        """Finalise les données et calcule les statistiques"""
        try:
            if self.is_cancelled:
                return None
            
            # Traitement du temps
            time_format = self.config.get('time_format', 'auto')
            
            if time_format == 'auto':
                # Tentative de détection automatique du format de temps
                df['Time'] = self.auto_parse_time(df['Time'])
            else:
                # Format spécifique
                try:
                    df['Time'] = pd.to_datetime(df['Time'], format=time_format)
                except:
                    # Fallback vers parsing automatique
                    df['Time'] = pd.to_datetime(df['Time'], infer_datetime_format=True)
            
            # Tri par temps
            df = df.sort_values('Time').reset_index(drop=True)
            
            # Calcul des statistiques
            stats = {
                'total_points': len(df),
                'time_span': (df['Time'].max() - df['Time'].min()).total_seconds() / 3600,  # heures
                'e_mean': df['E'].mean(),
                'e_std': df['E'].std(),
                'n_mean': df['N'].mean(), 
                'n_std': df['N'].std(),
                'h_mean': df['h'].mean(),
                'h_std': df['h'].std()
            }
            
            # Ajouter les statistiques comme attribut
            df.attrs['statistics'] = stats
            
            print(f"✓ Données finalisées: {len(df)} points")
            print(f"✓ Période: {stats['time_span']:.2f} heures")
            print(f"✓ Position moyenne: E={stats['e_mean']:.3f}, N={stats['n_mean']:.3f}")
            
            return df
            
        except Exception as e:
            self.error_occurred.emit(f"Erreur finalisation: {str(e)}")
            return None
    
    def auto_parse_time(self, time_series):
        """Parse automatique des timestamps"""
        try:
            # Essayer différents formats courants
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y%m%d %H%M%S'
            ]
            
            for fmt in formats_to_try:
                try:
                    return pd.to_datetime(time_series, format=fmt)
                except:
                    continue
            
            # Si tous échouent, utiliser l'inférence automatique
            return pd.to_datetime(time_series, infer_datetime_format=True)
            
        except Exception as e:
            print(f"⚠ Erreur parsing temps: {e}")
            # Créer un index temporel artificiel
            start_time = datetime.now()
            return pd.date_range(start=start_time, periods=len(time_series), freq='1S')


class GNSSImportDialog(QDialog):
    """Dialogue d'importation GNSS robuste et moderne"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📡 Importation Données GNSS")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Variables de contrôle
        self.file_path = None
        self.imported_data = None
        self.preview_data = None
        self.processor = None
        
        # Configuration d'import
        self.import_config = {
            'separator': ',',
            'skiprows': 0,
            'time_col': 0,
            'e_col': 1,
            'n_col': 2,
            'h_col': 3,
            'time_format': 'auto'
        }
        
        self.setup_ui()
        self.apply_modern_style()
        
        print("✓ Dialogue import GNSS initialisé")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # === ONGLETS PRINCIPAUX ===
        self.tabs = QTabWidget()
        
        # Onglet 1: Sélection de fichier
        self.file_tab = self.create_file_selection_tab()
        self.tabs.addTab(self.file_tab, "📁 Fichier")
        
        # Onglet 2: Configuration
        self.config_tab = self.create_configuration_tab()
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        
        # Onglet 3: Aperçu
        self.preview_tab = self.create_preview_tab()
        self.tabs.addTab(self.preview_tab, "👁️ Aperçu")
        
        # Onglet 4: Traitement
        self.process_tab = self.create_processing_tab()
        self.tabs.addTab(self.process_tab, "🔧 Traitement")
        
        main_layout.addWidget(self.tabs)
        
        # === BOUTONS DE CONTRÔLE ===
        self.create_control_buttons(main_layout)
        
        # Désactiver les onglets initialement
        for i in range(1, 4):
            self.tabs.setTabEnabled(i, False)
    
    def create_file_selection_tab(self):
        """Crée l'onglet de sélection de fichier"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Instructions
        instructions = QLabel("""
        <h3>📡 Importation de données GNSS</h3>
        <p>Sélectionnez un fichier contenant des données de positionnement GNSS.</p>
        <p><b>Formats supportés :</b></p>
        <ul>
        <li>CSV avec séparateurs: virgule, point-virgule, tabulation</li>
        <li>Colonnes typiques: Time, E (Est), N (Nord), h (altitude)</li>
        <li>Encodages: UTF-8, Latin-1, CP1252</li>
        </ul>
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                color: #495057;
            }
        """)
        layout.addWidget(instructions)
        
        # Sélection de fichier
        file_group = QGroupBox("📁 Sélection du fichier")
        file_layout = QVBoxLayout(file_group)
        
        # Ligne de sélection
        file_select_layout = QHBoxLayout()
        
        self.file_path_edit = QtWidgets.QLineEdit()
        self.file_path_edit.setPlaceholderText("Aucun fichier sélectionné...")
        self.file_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("📂 Parcourir")
        browse_btn.clicked.connect(self.select_file)
        browse_btn.setFixedWidth(120)
        
        file_select_layout.addWidget(self.file_path_edit)
        file_select_layout.addWidget(browse_btn)
        file_layout.addLayout(file_select_layout)
        
        # Informations sur le fichier
        self.file_info_label = QLabel("Aucun fichier sélectionné")
        self.file_info_label.setStyleSheet("color: #6c757d; font-style: italic;")
        file_layout.addWidget(self.file_info_label)
        
        layout.addWidget(file_group)
        layout.addStretch()
        
        return tab
    
    def create_configuration_tab(self):
        """Crée l'onglet de configuration"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuration du parsing
        parse_group = QGroupBox("🔧 Configuration du parsing")
        parse_layout = QFormLayout(parse_group)
        
        # Séparateur
        self.separator_combo = QComboBox()
        self.separator_combo.addItems([
            "Virgule (,)", "Point-virgule (;)", "Tabulation", "Espace", "Autre"
        ])
        self.separator_combo.currentTextChanged.connect(self.update_separator)
        parse_layout.addRow("Séparateur:", self.separator_combo)
        
        # Lignes à ignorer
        self.skiprows_spin = QSpinBox()
        self.skiprows_spin.setRange(0, 100)
        self.skiprows_spin.setValue(0)
        self.skiprows_spin.valueChanged.connect(self.update_skiprows)
        parse_layout.addRow("Lignes d'en-tête à ignorer:", self.skiprows_spin)
        
        layout.addWidget(parse_group)
        
        # Configuration des colonnes
        cols_group = QGroupBox("📊 Configuration des colonnes")
        cols_layout = QFormLayout(cols_group)
        
        # Colonnes de données
        self.time_col_spin = QSpinBox()
        self.time_col_spin.setRange(1, 50)
        self.time_col_spin.setValue(1)
        self.time_col_spin.valueChanged.connect(self.update_columns)
        cols_layout.addRow("Colonne Temps:", self.time_col_spin)
        
        self.e_col_spin = QSpinBox()
        self.e_col_spin.setRange(1, 50)
        self.e_col_spin.setValue(2)
        self.e_col_spin.valueChanged.connect(self.update_columns)
        cols_layout.addRow("Colonne E (Est):", self.e_col_spin)
        
        self.n_col_spin = QSpinBox()
        self.n_col_spin.setRange(1, 50)
        self.n_col_spin.setValue(3)
        self.n_col_spin.valueChanged.connect(self.update_columns)
        cols_layout.addRow("Colonne N (Nord):", self.n_col_spin)
        
        self.h_col_spin = QSpinBox()
        self.h_col_spin.setRange(1, 50)
        self.h_col_spin.setValue(4)
        self.h_col_spin.valueChanged.connect(self.update_columns)
        cols_layout.addRow("Colonne h (altitude):", self.h_col_spin)
        
        layout.addWidget(cols_group)
        
        # Test de configuration
        test_btn = QPushButton("🔍 Tester la configuration")
        test_btn.clicked.connect(self.test_configuration)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        
        return tab
    
    def create_preview_tab(self):
        """Crée l'onglet d'aperçu"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Titre et informations
        info_layout = QHBoxLayout()
        
        self.preview_info = QLabel("Aperçu des données")
        self.preview_info.setFont(QFont("", 12, QFont.Bold))
        
        refresh_preview_btn = QPushButton("🔄 Actualiser")
        refresh_preview_btn.clicked.connect(self.update_preview)
        refresh_preview_btn.setFixedWidth(100)
        
        info_layout.addWidget(self.preview_info)
        info_layout.addStretch()
        info_layout.addWidget(refresh_preview_btn)
        
        layout.addLayout(info_layout)
        
        # Tableau d'aperçu
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.preview_table)
        
        # Statistiques de base
        self.preview_stats = QLabel("Aucune donnée")
        self.preview_stats.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.preview_stats)
        
        return tab
    
    def create_processing_tab(self):
        """Crée l'onglet de traitement"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Status et progression
        status_group = QGroupBox("📊 État du traitement")
        status_layout = QVBoxLayout(status_group)
        
        self.process_status = QLabel("En attente...")
        self.process_status.setFont(QFont("", 11, QFont.Bold))
        status_layout.addWidget(self.process_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # Log du traitement
        log_group = QGroupBox("📝 Journal du traitement")
        log_layout = QVBoxLayout(log_group)
        
        self.process_log = QTextEdit()
        self.process_log.setReadOnly(True)
        self.process_log.setMaximumHeight(200)
        self.process_log.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.process_log)
        
        layout.addWidget(log_group)
        
        # Contrôles de traitement
        controls_layout = QHBoxLayout()
        
        self.start_process_btn = QPushButton("🚀 Démarrer le traitement")
        self.start_process_btn.clicked.connect(self.start_processing)
        
        self.cancel_process_btn = QPushButton("❌ Annuler")
        self.cancel_process_btn.clicked.connect(self.cancel_processing)
        self.cancel_process_btn.setEnabled(False)
        
        controls_layout.addWidget(self.start_process_btn)
        controls_layout.addWidget(self.cancel_process_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        layout.addStretch()
        
        return tab
    
    def create_control_buttons(self, layout):
        """Crée les boutons de contrôle"""
        buttons_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⬅️ Précédent")
        self.prev_btn.clicked.connect(self.previous_tab)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("➡️ Suivant")
        self.next_btn.clicked.connect(self.next_tab)
        self.next_btn.setEnabled(False)
        
        self.import_btn = QPushButton("✅ Importer")
        self.import_btn.clicked.connect(self.accept)
        self.import_btn.setEnabled(False)
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.prev_btn)
        buttons_layout.addWidget(self.next_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def apply_modern_style(self):
        """Applique le style moderne"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: #007bff;
                color: white;
                border-radius: 4px;
                margin-left: 10px;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 30px;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
            }
            
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                gridline-color: #e9ecef;
            }
            
            QTableWidget::item {
                padding: 8px;
            }
            
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #e9ecef;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            
            QTabBar::tab:hover {
                background-color: #f8f9fa;
            }
        """)
    
    # === MÉTHODES DE CONTRÔLE ===
    
    def select_file(self):
        """Sélectionne un fichier GNSS"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Sélectionner un fichier GNSS",
                "",
                "Fichiers CSV (*.csv);;Fichiers texte (*.txt);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                self.file_path = file_path
                self.file_path_edit.setText(file_path)
                
                # Analyser le fichier
                self.analyze_file()
                
                # Activer l'onglet suivant
                self.tabs.setTabEnabled(1, True)
                self.next_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sélection: {str(e)}")
    
    def analyze_file(self):
        """Analyse le fichier sélectionné"""
        try:
            if not self.file_path:
                return
            
            file_info = Path(self.file_path)
            size_mb = file_info.stat().st_size / (1024 * 1024)
            
            # Lire les premières lignes pour détection automatique
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
            
            # Détecter le séparateur le plus probable
            separators = {',': 0, ';': 0, '\t': 0, ' ': 0}
            for line in first_lines:
                for sep in separators:
                    separators[sep] += line.count(sep)
            
            best_sep = max(separators, key=separators.get)
            
            # Mettre à jour la configuration automatiquement
            sep_map = {',': 0, ';': 1, '\t': 2, ' ': 3}
            if best_sep in sep_map:
                self.separator_combo.setCurrentIndex(sep_map[best_sep])
                self.update_separator()
            
            # Afficher les informations
            info_text = f"""
            📁 Fichier: {file_info.name}
            📊 Taille: {size_mb:.2f} MB
            🔍 Séparateur détecté: '{best_sep}'
            📝 Premières lignes:
            """
            
            for i, line in enumerate(first_lines[:3], 1):
                info_text += f"\n{i}: {line[:100]}{'...' if len(line) > 100 else ''}"
            
            self.file_info_label.setText(info_text)
            
        except Exception as e:
            self.file_info_label.setText(f"Erreur analyse: {str(e)}")
    
    def update_separator(self):
        """Met à jour le séparateur"""
        sep_map = {
            "Virgule (,)": ',',
            "Point-virgule (;)": ';',
            "Tabulation": '\t',
            "Espace": ' '
        }
        
        text = self.separator_combo.currentText()
        if text in sep_map:
            self.import_config['separator'] = sep_map[text]
    
    def update_skiprows(self):
        """Met à jour le nombre de lignes à ignorer"""
        self.import_config['skiprows'] = self.skiprows_spin.value()
    
    def update_columns(self):
        """Met à jour la configuration des colonnes"""
        self.import_config.update({
            'time_col': self.time_col_spin.value() - 1,  # Convertir en index 0
            'e_col': self.e_col_spin.value() - 1,
            'n_col': self.n_col_spin.value() - 1,
            'h_col': self.h_col_spin.value() - 1
        })
    
    def test_configuration(self):
        """Teste la configuration actuelle"""
        try:
            if not self.file_path:
                QMessageBox.warning(self, "Attention", "Aucun fichier sélectionné")
                return
            
            # Lire quelques lignes avec la configuration actuelle
            separator = self.import_config['separator']
            skiprows = self.import_config['skiprows']
            
            df_test = pd.read_csv(
                self.file_path,
                sep=separator,
                skiprows=skiprows,
                header=None,
                nrows=5,  # Seulement 5 lignes pour le test
                encoding='utf-8',
                on_bad_lines='skip'
            )
            
            if df_test.empty:
                QMessageBox.warning(self, "Attention", "Aucune donnée lue avec cette configuration")
                return
            
            # Vérifier que les colonnes existent
            required_cols = [
                self.import_config['time_col'],
                self.import_config['e_col'],
                self.import_config['n_col'],
                self.import_config['h_col']
            ]
            
            max_col = max(required_cols)
            if df_test.shape[1] <= max_col:
                QMessageBox.warning(
                    self, "Attention", 
                    f"Le fichier n'a que {df_test.shape[1]} colonnes, "
                    f"mais la colonne {max_col + 1} est requise"
                )
                return
            
            # Test réussi
            QMessageBox.information(
                self, "Test réussi", 
                f"Configuration valide!\n"
                f"Colonnes détectées: {df_test.shape[1]}\n"
                f"Lignes d'exemple: {df_test.shape[0]}"
            )
            
            # Activer l'onglet aperçu
            self.tabs.setTabEnabled(2, True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Test échoué: {str(e)}")
    
    def update_preview(self):
        """Met à jour l'aperçu des données"""
        try:
            if not self.file_path:
                return
            
            # Lire un échantillon plus grand pour l'aperçu
            separator = self.import_config['separator']
            skiprows = self.import_config['skiprows']
            
            df_preview = pd.read_csv(
                self.file_path,
                sep=separator,
                skiprows=skiprows,
                header=None,
                nrows=100,  # 100 lignes pour l'aperçu
                encoding='utf-8',
                on_bad_lines='skip'
            )
            
            if df_preview.empty:
                self.preview_info.setText("Aucune donnée à afficher")
                return
            
            # Extraire les colonnes d'intérêt
            cols = [
                self.import_config['time_col'],
                self.import_config['e_col'],
                self.import_config['n_col'],
                self.import_config['h_col']
            ]
            
            if max(cols) >= df_preview.shape[1]:
                self.preview_info.setText("Configuration des colonnes invalide")
                return
            
            df_selected = df_preview.iloc[:, cols]
            df_selected.columns = ['Time', 'E', 'N', 'h']
            
            # Remplir le tableau
            self.preview_table.setRowCount(min(50, len(df_selected)))  # Max 50 lignes
            self.preview_table.setColumnCount(4)
            self.preview_table.setHorizontalHeaderLabels(['Time', 'E', 'N', 'h'])
            
            for row in range(min(50, len(df_selected))):
                for col in range(4):
                    value = str(df_selected.iloc[row, col])
                    item = QTableWidgetItem(value)
                    self.preview_table.setItem(row, col, item)
            
            # Ajuster les colonnes
            self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Statistiques
            stats_text = f"""
            📊 Aperçu: {len(df_selected)} lignes × {len(df_selected.columns)} colonnes
            🎯 Échantillon: {min(50, len(df_selected))} lignes affichées
            """
            
            self.preview_stats.setText(stats_text)
            self.preview_info.setText("Aperçu des données GNSS")
            
            # Stocker pour le traitement
            self.preview_data = df_selected
            
            # Activer l'onglet traitement
            self.tabs.setTabEnabled(3, True)
            
        except Exception as e:
            self.preview_info.setText(f"Erreur aperçu: {str(e)}")
    
    def start_processing(self):
        """Démarre le traitement des données"""
        try:
            if not self.file_path:
                QMessageBox.warning(self, "Attention", "Aucun fichier sélectionné")
                return
            
            # Préparer l'interface
            self.start_process_btn.setEnabled(False)
            self.cancel_process_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.process_log.clear()
            
            # Créer et démarrer le processeur
            self.processor = GNSSDataProcessor(self.file_path, self.import_config)
            
            # Connecter les signaux
            self.processor.progress_updated.connect(self.progress_bar.setValue)
            self.processor.status_updated.connect(self.update_process_status)
            self.processor.data_processed.connect(self.on_data_processed)
            self.processor.error_occurred.connect(self.on_processing_error)
            
            # Démarrer le traitement
            self.processor.start()
            
            self.log_message("🚀 Démarrage du traitement...")
            
        except Exception as e:
            self.on_processing_error(f"Erreur démarrage: {str(e)}")
    
    def cancel_processing(self):
        """Annule le traitement en cours"""
        if self.processor:
            self.processor.cancel_processing()
            self.processor.wait(3000)  # Attendre max 3 secondes
            
        self.start_process_btn.setEnabled(True)
        self.cancel_process_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.log_message("❌ Traitement annulé")
    
    def update_process_status(self, status):
        """Met à jour le statut du traitement"""
        self.process_status.setText(status)
        self.log_message(status)
    
    def on_data_processed(self, df):
        """Traitement terminé avec succès"""
        self.imported_data = df
        
        self.start_process_btn.setEnabled(True)
        self.cancel_process_btn.setEnabled(False)
        self.import_btn.setEnabled(True)
        
        # Afficher les résultats finaux
        if hasattr(df, 'attrs') and 'statistics' in df.attrs:
            stats = df.attrs['statistics']
            self.log_message(f"✅ Traitement terminé: {stats['total_points']} points")
            self.log_message(f"📊 Durée: {stats['time_span']:.2f} heures")
            self.log_message(f"📍 Position moyenne: E={stats['e_mean']:.3f}, N={stats['n_mean']:.3f}")
    
    def on_processing_error(self, error_msg):
        """Gestion des erreurs de traitement"""
        self.start_process_btn.setEnabled(True)
        self.cancel_process_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.log_message(f"❌ {error_msg}")
        QMessageBox.critical(self, "Erreur de traitement", error_msg)
    
    def log_message(self, message):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.process_log.append(f"[{timestamp}] {message}")
    
    # === NAVIGATION ENTRE ONGLETS ===
    
    def next_tab(self):
        """Passe à l'onglet suivant"""
        current = self.tabs.currentIndex()
        if current < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current + 1)
            self.update_navigation_buttons()
    
    def previous_tab(self):
        """Passe à l'onglet précédent"""
        current = self.tabs.currentIndex()
        if current > 0:
            self.tabs.setCurrentIndex(current - 1)
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Met à jour l'état des boutons de navigation"""
        current = self.tabs.currentIndex()
        
        self.prev_btn.setEnabled(current > 0)
        self.next_btn.setEnabled(current < self.tabs.count() - 1 and self.tabs.isTabEnabled(current + 1))
    
    # === MÉTHODES PUBLIQUES ===
    
    def get_imported_data(self):
        """Retourne les données importées"""
        return self.imported_data
    
    def get_file_path(self):
        """Retourne le chemin du fichier"""
        return self.file_path