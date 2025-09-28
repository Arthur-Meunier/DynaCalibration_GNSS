
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 23:45:00 2025

@author: a.meunier
"""

# settings_dialog.py
# Dialogue de paramètres pour l'application de calibration

import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QPushButton, QFileDialog, QLabel,
    QTextEdit, QSlider, QButtonGroup, QRadioButton, QDialogButtonBox,
    QMessageBox, QColorDialog, QFontComboBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette


class SettingsDialog(QDialog):
    """Dialogue de configuration des paramètres de l'application"""
    
    # Signal émis quand les paramètres sont modifiés
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration du dialogue
        self.setWindowTitle("⚙️ Paramètres de l'Application")
        self.setModal(True)
        self.resize(700, 600)
        
        # Gestionnaire de paramètres Qt
        self.settings = QSettings("CalibrationGNSS", "MainApp")
        
        # Paramètres par défaut
        self.default_settings = {
            # Général
            'auto_save': True,
            'auto_save_interval': 30,
            'backup_enabled': True,
            'backup_count': 5,
            'theme': 'dark',
            'language': 'fr',
            
            # Interface
            'font_family': 'Segoe UI',
            'font_size': 10,
            'animation_enabled': True,
            'show_tooltips': True,
            'compact_mode': False,
            
            # Projet
            'default_project_path': os.path.expanduser("~/CalibrationGNSS"),
            'recent_projects_count': 10,
            'auto_load_last_project': False,
            
            # GNSS
            'default_meridian_convergence': 0.0,
            'default_scale_factor': 1.0,
            'sp3_auto_download': True,
            'sp3_cache_days': 30,
            'gnss_timeout': 30,
            
            # Capteurs
            'sensor_data_validation': True,
            'outlier_detection': True,
            'outlier_threshold': 3.0,
            'data_smoothing': False,
            
            # Export
            'default_export_format': 'json',
            'include_metadata': True,
            'compress_exports': False,
            'auto_open_exports': True,
            
            # Développement
            'debug_mode': False,
            'log_level': 'INFO',
            'performance_monitoring': False
        }
        
        # Paramètres actuels
        self.current_settings = self.load_settings()
        
        self.setup_ui()
        self.load_current_values()
        self.connect_signals()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Onglets de paramètres
        self.tabs = QTabWidget()
        
        # Créer les onglets
        self.create_general_tab()
        self.create_interface_tab()
        self.create_project_tab()
        self.create_gnss_tab()
        self.create_sensors_tab()
        self.create_export_tab()
        self.create_advanced_tab()
        
        layout.addWidget(self.tabs)
        
        # Boutons de dialogue
        self.create_dialog_buttons(layout)
        
        # Appliquer le style
        self.apply_styles()
    
    def create_general_tab(self):
        """Crée l'onglet des paramètres généraux"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Sauvegarde
        save_group = QGroupBox("💾 Sauvegarde Automatique")
        save_layout = QFormLayout(save_group)
        
        self.auto_save_check = QCheckBox("Activer la sauvegarde automatique")
        save_layout.addRow(self.auto_save_check)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(5, 300)
        self.auto_save_interval.setSuffix(" secondes")
        save_layout.addRow("Intervalle:", self.auto_save_interval)
        
        self.backup_enabled_check = QCheckBox("Créer des sauvegardes")
        save_layout.addRow(self.backup_enabled_check)
        
        self.backup_count = QSpinBox()
        self.backup_count.setRange(1, 20)
        save_layout.addRow("Nombre de sauvegardes:", self.backup_count)
        
        layout.addWidget(save_group)
        
        # Groupe Apparence
        appearance_group = QGroupBox("🎨 Apparence")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "auto"])
        appearance_layout.addRow("Thème:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["fr", "en", "es"])
        appearance_layout.addRow("Langue:", self.language_combo)
        
        layout.addWidget(appearance_group)
        
        # Espace flexible
        layout.addStretch()
        
        self.tabs.addTab(tab, "⚙️ Général")
    
    def create_interface_tab(self):
        """Crée l'onglet des paramètres d'interface"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Police
        font_group = QGroupBox("🔤 Police et Taille")
        font_layout = QFormLayout(font_group)
        
        self.font_combo = QFontComboBox()
        font_layout.addRow("Police:", self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        font_layout.addRow("Taille:", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # Groupe Comportement
        behavior_group = QGroupBox("🖱️ Comportement Interface")
        behavior_layout = QFormLayout(behavior_group)
        
        self.animation_check = QCheckBox("Activer les animations")
        behavior_layout.addRow(self.animation_check)
        
        self.tooltips_check = QCheckBox("Afficher les info-bulles")
        behavior_layout.addRow(self.tooltips_check)
        
        self.compact_mode_check = QCheckBox("Mode compact")
        behavior_layout.addRow(self.compact_mode_check)
        
        layout.addWidget(behavior_group)
        
        # Aperçu de la police
        preview_group = QGroupBox("👁️ Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.font_preview = QLabel("Exemple de texte avec cette police")
        self.font_preview.setStyleSheet("""
            QLabel {
                border: 1px solid #555;
                padding: 10px;
                background-color: #2d2d30;
                border-radius: 4px;
            }
        """)
        preview_layout.addWidget(self.font_preview)
        
        layout.addWidget(preview_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "🖥️ Interface")
    
    def create_project_tab(self):
        """Crée l'onglet des paramètres de projet"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Répertoires
        paths_group = QGroupBox("📁 Répertoires")
        paths_layout = QFormLayout(paths_group)
        
        path_layout = QHBoxLayout()
        self.default_path_edit = QLineEdit()
        browse_btn = QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.browse_default_path)
        path_layout.addWidget(self.default_path_edit)
        path_layout.addWidget(browse_btn)
        
        paths_layout.addRow("Répertoire par défaut:", path_layout)
        
        layout.addWidget(paths_group)
        
        # Groupe Projets Récents
        recent_group = QGroupBox("📋 Projets Récents")
        recent_layout = QFormLayout(recent_group)
        
        self.recent_count_spin = QSpinBox()
        self.recent_count_spin.setRange(5, 50)
        recent_layout.addRow("Nombre de projets récents:", self.recent_count_spin)
        
        self.auto_load_check = QCheckBox("Charger automatiquement le dernier projet")
        recent_layout.addRow(self.auto_load_check)
        
        layout.addWidget(recent_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "📂 Projets")
    
    def create_gnss_tab(self):
        """Crée l'onglet des paramètres GNSS"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Paramètres par défaut
        defaults_group = QGroupBox("🛰️ Paramètres par Défaut")
        defaults_layout = QFormLayout(defaults_group)
        
        self.meridian_conv_spin = QDoubleSpinBox()
        self.meridian_conv_spin.setRange(-180, 180)
        self.meridian_conv_spin.setDecimals(6)
        self.meridian_conv_spin.setSuffix("°")
        defaults_layout.addRow("Convergence méridienne:", self.meridian_conv_spin)
        
        self.scale_factor_spin = QDoubleSpinBox()
        self.scale_factor_spin.setRange(0.9, 1.1)
        self.scale_factor_spin.setDecimals(8)
        defaults_layout.addRow("Facteur d'échelle:", self.scale_factor_spin)
        
        self.gnss_timeout_spin = QSpinBox()
        self.gnss_timeout_spin.setRange(10, 300)
        self.gnss_timeout_spin.setSuffix(" secondes")
        defaults_layout.addRow("Timeout GNSS:", self.gnss_timeout_spin)
        
        layout.addWidget(defaults_group)
        
        # Groupe SP3
        sp3_group = QGroupBox("📡 Orbites Précises (SP3)")
        sp3_layout = QFormLayout(sp3_group)
        
        self.sp3_auto_check = QCheckBox("Téléchargement automatique SP3")
        sp3_layout.addRow(self.sp3_auto_check)
        
        self.sp3_cache_spin = QSpinBox()
        self.sp3_cache_spin.setRange(1, 365)
        self.sp3_cache_spin.setSuffix(" jours")
        sp3_layout.addRow("Durée de cache SP3:", self.sp3_cache_spin)
        
        layout.addWidget(sp3_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "🛰️ GNSS")
    
    def create_sensors_tab(self):
        """Crée l'onglet des paramètres de capteurs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Validation
        validation_group = QGroupBox("✅ Validation des Données")
        validation_layout = QFormLayout(validation_group)
        
        self.validation_check = QCheckBox("Validation automatique des données")
        validation_layout.addRow(self.validation_check)
        
        self.outlier_check = QCheckBox("Détection des valeurs aberrantes")
        validation_layout.addRow(self.outlier_check)
        
        self.outlier_threshold_spin = QDoubleSpinBox()
        self.outlier_threshold_spin.setRange(1.0, 10.0)
        self.outlier_threshold_spin.setDecimals(1)
        self.outlier_threshold_spin.setSuffix(" σ")
        validation_layout.addRow("Seuil de détection:", self.outlier_threshold_spin)
        
        layout.addWidget(validation_group)
        
        # Groupe Traitement
        processing_group = QGroupBox("📊 Traitement des Données")
        processing_layout = QFormLayout(processing_group)
        
        self.smoothing_check = QCheckBox("Lissage des données")
        processing_layout.addRow(self.smoothing_check)
        
        layout.addWidget(processing_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "📊 Capteurs")
    
    def create_export_tab(self):
        """Crée l'onglet des paramètres d'export"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Format par défaut
        format_group = QGroupBox("📄 Format d'Export")
        format_layout = QFormLayout(format_group)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["json", "html", "pdf", "csv"])
        format_layout.addRow("Format par défaut:", self.export_format_combo)
        
        layout.addWidget(format_group)
        
        # Groupe Options
        options_group = QGroupBox("⚙️ Options d'Export")
        options_layout = QFormLayout(options_group)
        
        self.include_metadata_check = QCheckBox("Inclure les métadonnées")
        options_layout.addRow(self.include_metadata_check)
        
        self.compress_check = QCheckBox("Compresser les exports")
        options_layout.addRow(self.compress_check)
        
        self.auto_open_check = QCheckBox("Ouvrir automatiquement après export")
        options_layout.addRow(self.auto_open_check)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "📤 Export")
    
    def create_advanced_tab(self):
        """Crée l'onglet des paramètres avancés"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Debug
        debug_group = QGroupBox("🐛 Développement")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_check = QCheckBox("Mode debug")
        debug_layout.addRow(self.debug_check)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        debug_layout.addRow("Niveau de log:", self.log_level_combo)
        
        self.performance_check = QCheckBox("Monitoring des performances")
        debug_layout.addRow(self.performance_check)
        
        layout.addWidget(debug_group)
        
        # Groupe Actions
        actions_group = QGroupBox("🔧 Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        reset_btn = QPushButton("🔄 Restaurer les Paramètres par Défaut")
        reset_btn.clicked.connect(self.reset_to_defaults)
        
        export_btn = QPushButton("📤 Exporter la Configuration")
        export_btn.clicked.connect(self.export_settings)
        
        import_btn = QPushButton("📥 Importer une Configuration")
        import_btn.clicked.connect(self.import_settings)
        
        actions_layout.addWidget(reset_btn)
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(import_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "🔧 Avancé")
    
    def create_dialog_buttons(self, layout):
        """Crée les boutons du dialogue"""
        buttons_layout = QHBoxLayout()
        
        # Bouton Aperçu en direct
        self.live_preview_check = QCheckBox("Aperçu en direct")
        self.live_preview_check.setChecked(True)
        buttons_layout.addWidget(self.live_preview_check)
        
        buttons_layout.addStretch()
        
        # Boutons standard
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        
        self.button_box.accepted.connect(self.accept_settings)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        
        buttons_layout.addWidget(self.button_box)
        
        layout.addLayout(buttons_layout)
    
    def connect_signals(self):
        """Connecte les signaux pour l'aperçu en direct"""
        # Connexions pour l'aperçu de police
        self.font_combo.currentTextChanged.connect(self.update_font_preview)
        self.font_size_spin.valueChanged.connect(self.update_font_preview)
        
        # Connexions pour l'aperçu en direct
        if hasattr(self, 'live_preview_check'):
            widgets_to_connect = [
                self.auto_save_check, self.theme_combo, self.animation_check,
                self.font_combo, self.font_size_spin
            ]
            
            for widget in widgets_to_connect:
                if hasattr(widget, 'stateChanged'):
                    widget.stateChanged.connect(self.on_setting_changed)
                elif hasattr(widget, 'currentTextChanged'):
                    widget.currentTextChanged.connect(self.on_setting_changed)
                elif hasattr(widget, 'valueChanged'):
                    widget.valueChanged.connect(self.on_setting_changed)
    
    def on_setting_changed(self):
        """Appelé quand un paramètre change (aperçu en direct)"""
        if self.live_preview_check.isChecked():
            # Appliquer immédiatement certains changements
            self.update_font_preview()
    
    def update_font_preview(self):
        """Met à jour l'aperçu de police"""
        if hasattr(self, 'font_preview'):
            font = QFont(self.font_combo.currentText(), self.font_size_spin.value())
            self.font_preview.setFont(font)
    
    def browse_default_path(self):
        """Ouvre un dialogue pour choisir le répertoire par défaut"""
        current_path = self.default_path_edit.text()
        if not current_path:
            current_path = os.path.expanduser("~")
        
        new_path = QFileDialog.getExistingDirectory(
            self, "Choisir le répertoire par défaut", current_path
        )
        
        if new_path:
            self.default_path_edit.setText(new_path)
    
    def load_settings(self):
        """Charge les paramètres depuis QSettings"""
        settings = {}
        
        for key, default_value in self.default_settings.items():
            # Utiliser la valeur par défaut si le paramètre n'existe pas
            settings[key] = self.settings.value(key, default_value)
            
            # Conversion de type si nécessaire
            if isinstance(default_value, bool):
                settings[key] = str(settings[key]).lower() == 'true'
            elif isinstance(default_value, int):
                settings[key] = int(settings[key])
            elif isinstance(default_value, float):
                settings[key] = float(settings[key])
        
        return settings
    
    def save_settings(self, settings):
        """Sauvegarde les paramètres vers QSettings"""
        for key, value in settings.items():
            self.settings.setValue(key, value)
        
        self.settings.sync()
    
    def load_current_values(self):
        """Charge les valeurs actuelles dans l'interface"""
        # Général
        self.auto_save_check.setChecked(self.current_settings['auto_save'])
        self.auto_save_interval.setValue(self.current_settings['auto_save_interval'])
        self.backup_enabled_check.setChecked(self.current_settings['backup_enabled'])
        self.backup_count.setValue(self.current_settings['backup_count'])
        self.theme_combo.setCurrentText(self.current_settings['theme'])
        self.language_combo.setCurrentText(self.current_settings['language'])
        
        # Interface
        self.font_combo.setCurrentText(self.current_settings['font_family'])
        self.font_size_spin.setValue(self.current_settings['font_size'])
        self.animation_check.setChecked(self.current_settings['animation_enabled'])
        self.tooltips_check.setChecked(self.current_settings['show_tooltips'])
        self.compact_mode_check.setChecked(self.current_settings['compact_mode'])
        
        # Projet
        self.default_path_edit.setText(self.current_settings['default_project_path'])
        self.recent_count_spin.setValue(self.current_settings['recent_projects_count'])
        self.auto_load_check.setChecked(self.current_settings['auto_load_last_project'])
        
        # GNSS
        self.meridian_conv_spin.setValue(self.current_settings['default_meridian_convergence'])
        self.scale_factor_spin.setValue(self.current_settings['default_scale_factor'])
        self.sp3_auto_check.setChecked(self.current_settings['sp3_auto_download'])
        self.sp3_cache_spin.setValue(self.current_settings['sp3_cache_days'])
        self.gnss_timeout_spin.setValue(self.current_settings['gnss_timeout'])
        
        # Capteurs
        self.validation_check.setChecked(self.current_settings['sensor_data_validation'])
        self.outlier_check.setChecked(self.current_settings['outlier_detection'])
        self.outlier_threshold_spin.setValue(self.current_settings['outlier_threshold'])
        self.smoothing_check.setChecked(self.current_settings['data_smoothing'])
        
        # Export
        self.export_format_combo.setCurrentText(self.current_settings['default_export_format'])
        self.include_metadata_check.setChecked(self.current_settings['include_metadata'])
        self.compress_check.setChecked(self.current_settings['compress_exports'])
        self.auto_open_check.setChecked(self.current_settings['auto_open_exports'])
        
        # Avancé
        self.debug_check.setChecked(self.current_settings['debug_mode'])
        self.log_level_combo.setCurrentText(self.current_settings['log_level'])
        self.performance_check.setChecked(self.current_settings['performance_monitoring'])
        
        # Mettre à jour l'aperçu
        self.update_font_preview()
    
    def collect_current_values(self):
        """Collecte les valeurs actuelles de l'interface"""
        settings = {}
        
        # Général
        settings['auto_save'] = self.auto_save_check.isChecked()
        settings['auto_save_interval'] = self.auto_save_interval.value()
        settings['backup_enabled'] = self.backup_enabled_check.isChecked()
        settings['backup_count'] = self.backup_count.value()
        settings['theme'] = self.theme_combo.currentText()
        settings['language'] = self.language_combo.currentText()
        
        # Interface
        settings['font_family'] = self.font_combo.currentText()
        settings['font_size'] = self.font_size_spin.value()
        settings['animation_enabled'] = self.animation_check.isChecked()
        settings['show_tooltips'] = self.tooltips_check.isChecked()
        settings['compact_mode'] = self.compact_mode_check.isChecked()
        
        # Projet
        settings['default_project_path'] = self.default_path_edit.text()
        settings['recent_projects_count'] = self.recent_count_spin.value()
        settings['auto_load_last_project'] = self.auto_load_check.isChecked()
        
        # GNSS
        settings['default_meridian_convergence'] = self.meridian_conv_spin.value()
        settings['default_scale_factor'] = self.scale_factor_spin.value()
        settings['sp3_auto_download'] = self.sp3_auto_check.isChecked()
        settings['sp3_cache_days'] = self.sp3_cache_spin.value()
        settings['gnss_timeout'] = self.gnss_timeout_spin.value()
        
        # Capteurs
        settings['sensor_data_validation'] = self.validation_check.isChecked()
        settings['outlier_detection'] = self.outlier_check.isChecked()
        settings['outlier_threshold'] = self.outlier_threshold_spin.value()
        settings['data_smoothing'] = self.smoothing_check.isChecked()
        
        # Export
        settings['default_export_format'] = self.export_format_combo.currentText()
        settings['include_metadata'] = self.include_metadata_check.isChecked()
        settings['compress_exports'] = self.compress_check.isChecked()
        settings['auto_open_exports'] = self.auto_open_check.isChecked()
        
        # Avancé
        settings['debug_mode'] = self.debug_check.isChecked()
        settings['log_level'] = self.log_level_combo.currentText()
        settings['performance_monitoring'] = self.performance_check.isChecked()
        
        return settings
    
    def apply_settings(self):
        """Applique les paramètres sans fermer le dialogue"""
        new_settings = self.collect_current_values()
        self.save_settings(new_settings)
        self.current_settings = new_settings
        self.settings_changed.emit(new_settings)
        
        QMessageBox.information(self, "Paramètres", "Paramètres appliqués avec succès!")
    
    def accept_settings(self):
        """Accepte et applique les paramètres"""
        self.apply_settings()
        self.accept()
    
    def reset_to_defaults(self):
        """Restaure les paramètres par défaut"""
        reply = QMessageBox.question(
            self,
            "Restaurer les Paramètres",
            "Êtes-vous sûr de vouloir restaurer tous les paramètres par défaut ?\n"
            "Cette action ne peut pas être annulée.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_settings = self.default_settings.copy()
            self.load_current_values()
            
            QMessageBox.information(self, "Restauration", 
                                  "Paramètres restaurés aux valeurs par défaut.")
    
    def export_settings(self):
        """Exporte la configuration vers un fichier"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la Configuration",
            "configuration_calibration.json",
            "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            try:
                current_settings = self.collect_current_values()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_settings, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Export Réussi", 
                                      f"Configuration exportée vers:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'Export", 
                                   f"Impossible d'exporter la configuration:\n{str(e)}")
    
    def import_settings(self):
        """Importe une configuration depuis un fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer une Configuration",
            "",
            "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)
                
                # Valider et fusionner avec les paramètres par défaut
                for key in self.default_settings:
                    if key in imported_settings:
                        self.current_settings[key] = imported_settings[key]
                
                self.load_current_values()
                
                QMessageBox.information(self, "Import Réussi", 
                                      f"Configuration importée depuis:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'Import", 
                                   f"Impossible d'importer la configuration:\n{str(e)}")
    
    def apply_styles(self):
        """Applique les styles au dialogue"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #555558;
                background-color: #2d2d30;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #3e3e42;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #007acc;
            }
            
            QTabBar::tab:hover {
                background-color: #4a4a4e;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555558;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #2d2d30;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: #2d2d30;
                color: #ffffff;
            }
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: #3e3e42;
                border: 1px solid #555558;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #007acc;
            }
            
            QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #004578;
            }
            
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555558;
                border-radius: 3px;
                background-color: #3e3e42;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
            
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #555558;
                height: 6px;
                background: #3e3e42;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #007acc;
                border: 1px solid #005a9e;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)
    
    def get_settings(self):
        """Retourne les paramètres actuels"""
        return self.current_settings.copy()


# Test du dialogue si exécuté directement
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Test du dialogue
    dialog = SettingsDialog()
    
    # Connexion de test
    dialog.settings_changed.connect(lambda settings: print(f"Paramètres modifiés: {len(settings)} éléments"))
    
    # Affichage
    dialog.show()
    
    sys.exit(app.exec_())