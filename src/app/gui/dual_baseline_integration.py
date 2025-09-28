"""
Widget d'intégration pour le traitement des deux lignes de base
Intègre le processeur RTKLIB, la préparation des données et la gestion de projet
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, 
    QLabel, QGroupBox, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

# Import des modules existants
from core.project_manager import ProjectManager
from core.calculations.dual_baseline_processor import (
    DualBaselineConfig, DualBaselineProcessor, DualBaselineMonitorWidget
)
from core.calculations.data_preparation import DataPreparationWidget
from core.progress_manager import ProgressManager


class DualBaselineIntegrationWidget(QWidget):
    """
    Widget principal d'intégration pour le traitement complet des deux lignes de base
    """
    
    # Signaux
    processing_completed = pyqtSignal(dict)  # Résultats finaux
    step_completed = pyqtSignal(str, dict)   # Étape terminée
    
    def __init__(self, project_manager: ProjectManager = None, progress_manager: ProgressManager = None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.progress_manager = progress_manager
        
        # Composants
        self.rtk_monitor = None
        self.data_preparation = None
        self.current_step = "rtk_processing"
        
        self.init_ui()
        self.setup_connections()
        self.check_existing_results()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle('Traitement GNSS - Deux Lignes de Base')
        self.setGeometry(100, 100, 1000, 700)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title_label = QLabel("🚢 Traitement GNSS - Deux Lignes de Base")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Barre de progression globale
        self.global_progress_bar = QProgressBar()
        self.global_progress_bar.setTextVisible(True)
        self.global_progress_bar.setFormat("Initialisation...")
        main_layout.addWidget(self.global_progress_bar)
        
        # Onglets pour les différentes étapes
        self.tab_widget = QTabWidget()
        
        # Onglet 1: Traitement RTKLIB
        self.rtk_tab = QWidget()
        self.rtk_tab_layout = QVBoxLayout(self.rtk_tab)
        self.rtk_tab_layout.addWidget(QLabel("Traitement RTKLIB - Deux Lignes de Base"))
        self.tab_widget.addTab(self.rtk_tab, "1. RTKLIB")
        
        # Onglet 2: Préparation des données
        self.preparation_tab = QWidget()
        self.preparation_tab_layout = QVBoxLayout(self.preparation_tab)
        self.preparation_tab_layout.addWidget(QLabel("Préparation des Données"))
        self.tab_widget.addTab(self.preparation_tab, "2. Préparation")
        
        # Onglet 3: Résultats
        self.results_tab = QWidget()
        self.results_tab_layout = QVBoxLayout(self.results_tab)
        self.results_tab_layout.addWidget(QLabel("Résultats et Analyse"))
        self.tab_widget.addTab(self.results_tab, "3. Résultats")
        
        main_layout.addWidget(self.tab_widget)
        
        # Boutons de contrôle
        control_layout = QHBoxLayout()
        
        self.start_rtk_button = QPushButton("Démarrer RTKLIB")
        self.start_rtk_button.clicked.connect(self.start_rtk_processing)
        control_layout.addWidget(self.start_rtk_button)
        
        self.start_preparation_button = QPushButton("Démarrer Préparation")
        self.start_preparation_button.clicked.connect(self.start_data_preparation)
        self.start_preparation_button.setEnabled(False)
        control_layout.addWidget(self.start_preparation_button)
        
        self.clear_cache_button = QPushButton("Effacer Cache")
        self.clear_cache_button.clicked.connect(self.clear_processing_cache)
        control_layout.addWidget(self.clear_cache_button)
        
        main_layout.addLayout(control_layout)
        
        # Zone de log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        main_layout.addWidget(self.log_text)
        
        # Initialiser les composants
        self.init_rtk_monitor()
        self.init_data_preparation()
        self.init_results_display()
    
    def init_rtk_monitor(self):
        """Initialise le moniteur RTKLIB"""
        self.rtk_monitor = DualBaselineMonitorWidget(self.project_manager)
        self.rtk_tab_layout.addWidget(self.rtk_monitor)
    
    def init_data_preparation(self):
        """Initialise le widget de préparation des données"""
        self.data_preparation = DataPreparationWidget(self.project_manager)
        self.preparation_tab_layout.addWidget(self.data_preparation)
    
    def init_results_display(self):
        """Initialise l'affichage des résultats"""
        # Groupe pour les résultats RTKLIB
        rtk_results_group = QGroupBox("Résultats RTKLIB")
        rtk_results_layout = QVBoxLayout(rtk_results_group)
        
        self.rtk_results_text = QTextEdit()
        self.rtk_results_text.setReadOnly(True)
        self.rtk_results_text.setMaximumHeight(100)
        rtk_results_layout.addWidget(self.rtk_results_text)
        
        # Groupe pour les résultats de préparation
        prep_results_group = QGroupBox("Résultats de Préparation")
        prep_results_layout = QVBoxLayout(prep_results_group)
        
        self.prep_results_text = QTextEdit()
        self.prep_results_text.setReadOnly(True)
        self.prep_results_text.setMaximumHeight(100)
        prep_results_layout.addWidget(self.prep_results_text)
        
        # Groupe pour les statistiques globales
        stats_group = QGroupBox("Statistiques Globales")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        # Ajouter les groupes au layout
        self.results_tab_layout.addWidget(rtk_results_group)
        self.results_tab_layout.addWidget(prep_results_group)
        self.results_tab_layout.addWidget(stats_group)
    
    def setup_connections(self):
        """Configure les connexions entre les composants"""
        # Les connexions seront établies dynamiquement lors du démarrage des traitements
        pass
    
    def check_existing_results(self):
        """Vérifie s'il existe déjà des résultats dans le projet"""
        if not self.project_manager:
            return
        
        # Vérifier le cache RTKLIB
        if self.project_manager.is_rtk_processing_completed():
            self.log_message("✅ Traitement RTKLIB déjà terminé")
            self.start_preparation_button.setEnabled(True)
            self.update_rtk_results_display()
        
        # Vérifier le cache de préparation
        if self.project_manager.is_data_preparation_completed():
            self.log_message("✅ Préparation des données déjà terminée")
            self.update_preparation_results_display()
            self.update_global_stats()
    
    def start_rtk_processing(self):
        """Démarre le traitement RTKLIB"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "Erreur", "Aucun projet chargé")
            return
        
        self.current_step = "rtk_processing"
        self.global_progress_bar.setFormat("Traitement RTKLIB en cours...")
        self.start_rtk_button.setEnabled(False)
        
        # Démarrer le moniteur RTKLIB
        if self.rtk_monitor:
            # Connecter les signaux avant de démarrer
            if hasattr(self.rtk_monitor, 'processor') and self.rtk_monitor.processor:
                self.rtk_monitor.processor.process_finished.connect(self.on_rtk_finished)
                self.rtk_monitor.processor.log_message.connect(self.on_log_message)
            self.rtk_monitor.start_processing()
    
    def start_data_preparation(self):
        """Démarre la préparation des données"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "Erreur", "Aucun projet chargé")
            return
        
        self.current_step = "data_preparation"
        self.global_progress_bar.setFormat("Préparation des données en cours...")
        self.start_preparation_button.setEnabled(False)
        
        # Démarrer la préparation
        if self.data_preparation:
            # Connecter les signaux avant de démarrer
            if hasattr(self.data_preparation, 'worker') and self.data_preparation.worker:
                self.data_preparation.worker.preparation_completed.connect(self.on_preparation_finished)
                self.data_preparation.worker.log_message.connect(self.on_log_message)
            self.data_preparation.start_preparation()
    
    def clear_processing_cache(self):
        """Efface le cache de traitement"""
        if not self.project_manager:
            return
        
        reply = QMessageBox.question(
            self, "Confirmation", 
            "Êtes-vous sûr de vouloir effacer le cache de traitement ?\n"
            "Cela forcera un recalcul complet.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.project_manager.clear_processing_cache():
                self.log_message("✅ Cache de traitement effacé")
                self.start_rtk_button.setEnabled(True)
                self.start_preparation_button.setEnabled(False)
                self.clear_results_display()
            else:
                self.log_message("❌ Erreur lors de l'effacement du cache")
    
    def on_rtk_finished(self, results: Dict[str, Any]):
        """Gère la fin du traitement RTKLIB"""
        self.start_rtk_button.setEnabled(True)
        
        if results.get("status") == "success":
            self.log_message("✅ Traitement RTKLIB terminé avec succès")
            self.start_preparation_button.setEnabled(True)
            self.update_rtk_results_display()
            
            # Mettre à jour le cache
            if self.project_manager:
                self.project_manager.update_rtk_processing_cache(
                    results.get("baselines", {}),
                    results.get("global_quality", {})
                )
            
            # Mettre à jour la progression
            self.global_progress_bar.setValue(50)
            self.global_progress_bar.setFormat("RTKLIB terminé - Prêt pour la préparation")
            
        else:
            self.log_message(f"❌ Erreur RTKLIB: {results.get('message', 'Inconnue')}")
            self.global_progress_bar.setFormat("Erreur RTKLIB")
    
    def on_preparation_finished(self, results: Dict[str, Any]):
        """Gère la fin de la préparation des données"""
        self.start_preparation_button.setEnabled(True)
        
        if results.get("status") == "success":
            self.log_message("✅ Préparation des données terminée avec succès")
            self.update_preparation_results_display()
            self.update_global_stats()
            
            # Mettre à jour le cache
            if self.project_manager:
                self.project_manager.update_data_preparation_cache(results)
            
            # Mettre à jour la progression
            self.global_progress_bar.setValue(100)
            self.global_progress_bar.setFormat("Traitement complet terminé")
            
            # Émettre le signal de completion
            self.processing_completed.emit(results)
            
        else:
            self.log_message(f"❌ Erreur préparation: {results.get('error', 'Inconnue')}")
            self.global_progress_bar.setFormat("Erreur préparation")
    
    def update_rtk_results_display(self):
        """Met à jour l'affichage des résultats RTKLIB"""
        if not self.project_manager:
            return
        
        results = self.project_manager.get_rtk_processing_results()
        if not results:
            return
        
        text = "Résultats RTKLIB:\n"
        for baseline_name, result in results.items():
            if result.get("status") == "success":
                text += f"✓ {baseline_name}: {result.get('output_file', 'N/A')}\n"
            else:
                text += f"✗ {baseline_name}: Erreur\n"
        
        self.rtk_results_text.setText(text)
    
    def update_preparation_results_display(self):
        """Met à jour l'affichage des résultats de préparation"""
        if not self.project_manager:
            return
        
        results = self.project_manager.get_data_preparation_results()
        if not results:
            return
        
        text = "Résultats de Préparation:\n"
        text += f"Points d'attitude: {results.get('attitudes_count', 0)}\n"
        text += f"Seuil de qualité: {results.get('quality_threshold', 0.1)}m\n"
        
        biases = results.get('geometric_biases', {})
        if biases:
            text += f"Biais Pitch: {biases.get('pitch_bias', 0):+.3f}°\n"
            text += f"Biais Roll: {biases.get('roll_bias', 0):+.3f}°\n"
        
        self.prep_results_text.setText(text)
    
    def update_global_stats(self):
        """Met à jour les statistiques globales"""
        if not self.project_manager:
            return
        
        rtk_results = self.project_manager.get_rtk_processing_results()
        prep_results = self.project_manager.get_data_preparation_results()
        
        text = "Statistiques Globales:\n"
        text += f"Lignes de base traitées: {len(rtk_results)}\n"
        text += f"Points d'attitude calculés: {prep_results.get('attitudes_count', 0)}\n"
        
        # Ajouter les statistiques de qualité si disponibles
        gnss_config = self.project_manager.current_project.get("gnss_config", {})
        processing_cache = gnss_config.get("processing_cache", {})
        rtk_cache = processing_cache.get("rtk_processing", {})
        quality_stats = rtk_cache.get("quality_stats", {})
        
        if quality_stats:
            text += "\nStatistiques de qualité:\n"
            for quality, count in quality_stats.items():
                text += f"Qualité {quality}: {count} points\n"
        
        self.stats_text.setText(text)
    
    def clear_results_display(self):
        """Efface l'affichage des résultats"""
        self.rtk_results_text.clear()
        self.prep_results_text.clear()
        self.stats_text.clear()
    
    def on_log_message(self, message: str):
        """Affiche un message de log"""
        self.log_text.append(f"[{self.current_step}] {message}")
    
    def log_message(self, message: str):
        """Affiche un message de log"""
        self.log_text.append(message)


# Style pour l'interface
STYLE_SHEET = """
QWidget {
    background-color: #2E3440;
    color: #ECEFF4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #4C566A;
    border-radius: 6px;
    background-color: #3B4252;
}
QTabBar::tab {
    background-color: #4C566A;
    color: #ECEFF4;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #5E81AC;
}
QTabBar::tab:hover {
    background-color: #5E81AC;
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
QPushButton {
    background-color: #4C566A;
    border: 1px solid #5E81AC;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5E81AC;
}
QPushButton:pressed {
    background-color: #3B4252;
}
QPushButton:disabled {
    background-color: #3B4252;
    color: #4C566A;
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
QTextEdit {
    background-color: #3B4252;
    border: 1px solid #4C566A;
    border-radius: 6px;
    padding: 8px;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 9pt;
}
"""


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)
    
    # Créer les gestionnaires
    project_manager = ProjectManager.instance()
    progress_manager = ProgressManager()
    
    # Créer le widget d'intégration
    widget = DualBaselineIntegrationWidget(project_manager, progress_manager)
    widget.show()
    
    sys.exit(app.exec_())
