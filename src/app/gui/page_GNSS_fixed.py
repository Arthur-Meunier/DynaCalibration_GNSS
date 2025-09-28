#!/usr/bin/env python3
"""
Page GNSS avec corrections pour les fichiers NAV/GNAV
"""

from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QComboBox, QTextEdit,
    QMessageBox, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush

# Import des modules internes
from core.app_data import ApplicationData
from core.project_manager import ProjectManager
from core.calculations.rtk_calculator import RTKCalculator, RTKConfig, RTKFileValidator

# Stylesheet pour la page
APP_STYLESHEET_TEST = """
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
"""

class SimpleDonutWidget(QWidget):
    """Widget donut simple pour afficher la qualité des données"""
    def __init__(self, baseline_name=""):
        super().__init__()
        self.baseline_name = baseline_name
        self.quality_data = {}
        self.setMinimumSize(80, 80)
        
        # Couleurs exactement comme dans test_RTKbat.py
        self.colors = {
            '1': QColor("#A3BE8C"), '2': QColor("#EBCB8B"), '5': QColor("#D08770"),
            '4': QColor("#B48EAD"), '3': QColor("#8FBCBB"), '6': QColor("#88C0D0"),
            '0': QColor("#BF616A"),
        }
        
    def update_data(self, quality_data):
        """Met à jour les données de qualité (signature simplifiée comme test_RTKbat.py)"""
        self.quality_data = quality_data.copy()
        self.update()
    
    def paintEvent(self, event):
        """Dessine le diagramme donut (exactement comme test_RTKbat.py)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect, side = self.rect(), min(self.rect().width(), self.rect().height())
        chart_rect = QRectF((rect.width()-side)/2+5, (rect.height()-side)/2+5, side-10, side-10)
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
        hole_rect = QRectF(25, 25, 30, 30)
        painter.setBrush(QBrush(QColor("#2E3440")))
        painter.drawEllipse(hole_rect)
        
        # Texte au centre
        painter.setPen(QColor("#ECEFF4"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(hole_rect, Qt.AlignCenter, f"{total}")


class GnssWidget(QWidget):
    """Widget GNSS avec gestion correcte des fichiers NAV/GNAV"""
    
    # Signaux requis par le menu vertical
    sp3_progress_updated = pyqtSignal(int, str)  # pourcentage, message
    baseline_progress_updated = pyqtSignal(str, int, str)  # baseline_name, pourcentage, status
    processing_completed = pyqtSignal(dict)  # résultats
    
    def __init__(self, app_data=None, project_manager: ProjectManager = None, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.project_manager = project_manager
        self.rtk_calculator = None
        self.rtk_config = RTKConfig()
        self.selected_files = {"port_obs": None, "bow_obs": None, "stbd_obs": None}
        
        # Appliquer le style du test
        self.setStyleSheet(APP_STYLESHEET_TEST)
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Titre
        title = QLabel("GNSS RTK")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #ECEFF4; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # SP3/CLK
        self.sp3_checkbox = QCheckBox("SP3/CLK")
        self.sp3_checkbox.setStyleSheet("color: #ECEFF4; padding: 5px;")
        self.sp3_checkbox.setChecked(True)  # Coché par défaut
        layout.addWidget(self.sp3_checkbox)
        
        # Fichiers
        files_layout = QHBoxLayout()
        
        # Port
        port_layout = QVBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_btn = QPushButton("Sélectionner")
        self.port_btn.clicked.connect(lambda: self.browse_file("port_obs"))
        port_layout.addWidget(self.port_btn)
        files_layout.addLayout(port_layout)
        
        # Bow
        bow_layout = QVBoxLayout()
        bow_layout.addWidget(QLabel("Bow:"))
        self.bow_btn = QPushButton("Sélectionner")
        self.bow_btn.clicked.connect(lambda: self.browse_file("bow_obs"))
        bow_layout.addWidget(self.bow_btn)
        files_layout.addLayout(bow_layout)
        
        # Stbd
        stbd_layout = QVBoxLayout()
        stbd_layout.addWidget(QLabel("Stbd:"))
        self.stbd_btn = QPushButton("Sélectionner")
        self.stbd_btn.clicked.connect(lambda: self.browse_file("stbd_obs"))
        stbd_layout.addWidget(self.stbd_btn)
        files_layout.addLayout(stbd_layout)
        
        layout.addLayout(files_layout)
        
        # Point fixe
        fixed_layout = QHBoxLayout()
        fixed_layout.addWidget(QLabel("Point fixe:"))
        self.fixed_combo = QComboBox()
        self.fixed_combo.addItems(["Port", "Bow", "Stbd"])
        self.fixed_combo.setStyleSheet("padding: 5px; border: 1px solid #4C566A; background-color: #3B4252;")
        fixed_layout.addWidget(self.fixed_combo)
        fixed_layout.addStretch()
        layout.addLayout(fixed_layout)
        
        # Monitoring avec barres séparées
        monitor_layout = QVBoxLayout()
        
        # Barres de progression individuelles avec diagrammes
        self.progress_bars = {}
        self.progress_labels = {}
        self.baseline_layouts = {}
        self.donut_widgets = {}
        
        # Créer un conteneur pour les barres dynamiques
        self.baselines_container = QVBoxLayout()
        monitor_layout.addLayout(self.baselines_container)
        
        layout.addLayout(monitor_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀 Calculer")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #A3BE8C;
                color: #2E3440;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #B5C99A; }
            QPushButton:disabled { background-color: #4C566A; color: #88C0D0; }
        """)
        self.start_btn.clicked.connect(self.start_calculation)
        
        self.stop_btn = QPushButton("⏹️ Arrêter")
        self.stop_btn.setStyleSheet("""
            QPushButton { 
                background-color: #BF616A;
                color: #ECEFF4;
                border: none; 
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #D08770; }
            QPushButton:disabled { background-color: #4C566A; color: #88C0D0; }
        """)
        self.stop_btn.clicked.connect(self.stop_calculation)
        self.stop_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Logs
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2E3440;
                border: 1px solid #4C566A;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 8pt;
                color: #ECEFF4;
            }
        """)
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
    
    def browse_file(self, file_type: str):
        """Sélection de fichier simplifiée"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner {file_type}", "", 
            "Fichiers RINEX (*.25o *.o *.obs);;Fichiers texte (*.txt);;Tous (*)"
        )
        
        if file_path:
            self.select_file(file_type, Path(file_path))
    
    def select_file(self, file_type: str, file_path: Path):
        """Sélection et validation de fichier avec gestion NAV/GNAV"""
        if file_type in ["port_obs", "bow_obs", "stbd_obs"]:
            # Vérifier si c'est un fichier RINEX ou un fichier texte
            if file_path.suffix.lower() in ['.obs', '.25o', '.o']:
                # Fichier RINEX - validation complète
                is_valid, files = RTKFileValidator.validate_rinex_files(file_path)
                
                if not is_valid:
                    QMessageBox.warning(self, "Erreur", f"Fichier RINEX {file_path.name} invalide (NAV/GNAV manquants)")
                    return
            else:
                # Fichier texte - validation simple
                if not file_path.exists():
                    QMessageBox.warning(self, "Erreur", f"Fichier {file_path.name} introuvable")
                    return
                
                # Créer un dictionnaire de fichiers simplifié pour les fichiers texte
                files = {"obs": file_path}
                is_valid = True
            
            self.selected_files[file_type] = files["obs"]
            
            # Stocker aussi les fichiers NAV/GNAV associés
            if "nav" in files:
                nav_key = file_type.replace("_obs", "_nav")
                self.selected_files[nav_key] = files["nav"]
                self.log_message(f"✅ {nav_key}: {files['nav'].name}")
            
            if "gnav" in files:
                gnav_key = file_type.replace("_obs", "_gnav")
                self.selected_files[gnav_key] = files["gnav"]
                self.log_message(f"✅ {gnav_key}: {files['gnav'].name}")
            
            # Mise à jour du bouton
            if file_type == "port_obs":
                self.port_btn.setText(f"✅ {file_path.name}")
            elif file_type == "bow_obs":
                self.bow_btn.setText(f"✅ {file_path.name}")
            elif file_type == "stbd_obs":
                self.stbd_btn.setText(f"✅ {file_path.name}")
            
            self.log_message(f"✅ Fichier {file_type} sélectionné: {file_path.name}")
    
    def start_calculation(self):
        """Démarre les calculs GNSS"""
        self.log_message("🚀 Démarrage des calculs GNSS...")
        
        # Déterminer le point fixe (base) depuis le combo
        fixed_point = self.fixed_combo.currentText()
        
        # Vérifier les fichiers disponibles
        available_files = {}
        for point in ["port", "bow", "stbd"]:
            if self.selected_files.get(f"{point}_obs"):
                available_files[point] = self.selected_files[f"{point}_obs"]
        
        if len(available_files) < 2:
            QMessageBox.warning(self, "Erreur", "Au moins 2 fichiers sont requis")
            return
        
        # Déterminer les baselines à calculer
        self.baselines_to_calculate = self._determine_baselines(fixed_point, available_files)
        
        # Créer les barres de progression dynamiques
        self._create_dynamic_progress_bars(self.baselines_to_calculate)
        
        # Démarrer les calculs parallèles
        self._start_parallel_calculations()
    
    def _determine_baselines(self, fixed_point: str, available_files: dict) -> list:
        """Détermine les 2 lignes de base à calculer"""
        baselines = []
        base_file = self.selected_files[f"{fixed_point.lower()}_obs"]
        rover_files = []
        
        for point in ["port", "bow", "stbd"]:
            if point != fixed_point.lower() and self.selected_files.get(f"{point}_obs"):
                rover_files.append({
                    "name": point.capitalize(),
                    "file": self.selected_files[f"{point}_obs"]
                })
        
        for rover in rover_files:
            baselines.append({
                "name": f"{fixed_point}→{rover['name']}",
                "base": fixed_point,
                "base_file": base_file,
                "rover": rover['name'],
                "rover_file": rover['file']
            })
        
        return baselines
    
    def _create_dynamic_progress_bars(self, baselines):
        """Crée dynamiquement les barres de progression selon les lignes de base"""
        # Nettoyer les anciennes barres
        for layout in self.baseline_layouts.values():
            # Supprimer tous les widgets du layout
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            # Supprimer le layout du conteneur
            self.baselines_container.removeItem(layout)
        
        self.progress_bars.clear()
        self.progress_labels.clear()
        self.baseline_layouts.clear()
        self.donut_widgets.clear()
        
        # Créer les nouvelles barres avec diagrammes
        for baseline in baselines:
            baseline_name = baseline['name']
            
            # Layout principal pour cette baseline
            main_layout = QVBoxLayout()
            main_layout.setSpacing(5)
            
            # Layout horizontal pour progression + diagramme
            progress_layout = QHBoxLayout()
            
            # Label de la ligne de base
            label = QLabel(f"{baseline_name}:")
            label.setStyleSheet("color: #ECEFF4; font-weight: bold; min-width: 80px;")
            progress_layout.addWidget(label)
            
            # Barre de progression
            progress_bar = QProgressBar()
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #4C566A;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #3B4252;
                    height: 25px;
                    font-size: 9pt;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(
                        x1: 0, y1: 0.5, x2: 1, y2: 0.5,
                        stop: 0 #81A1C1, stop: 1 #88C0D0
                    );
                    border-radius: 3px;
                }
            """)
            progress_bar.setValue(0)
            progress_bar.setFormat("En attente...")
            progress_layout.addWidget(progress_bar, 1)
            
            # Label de statut
            status_label = QLabel("⏸️")
            status_label.setStyleSheet("color: #ECEFF4; min-width: 30px; text-align: center;")
            progress_layout.addWidget(status_label)
            
            # Diagramme donut individuel
            donut_widget = SimpleDonutWidget(baseline_name)
            donut_widget.setFixedSize(80, 80)
            progress_layout.addWidget(donut_widget)
            
            main_layout.addLayout(progress_layout)
            
            # Stocker les références
            self.progress_bars[baseline_name] = progress_bar
            self.progress_labels[baseline_name] = status_label
            self.baseline_layouts[baseline_name] = main_layout
            self.donut_widgets[baseline_name] = donut_widget
            
            self.baselines_container.addLayout(main_layout)
    
    def _start_parallel_calculations(self):
        """Démarre les calculs parallèles avec gestion correcte des fichiers NAV/GNAV"""
        self.rtk_calculators = []
        self.baseline_results = {}
        
        for i, baseline in enumerate(self.baselines_to_calculate):
            config = RTKConfig()
            config.use_sp3_clk = self.sp3_checkbox.isChecked()
            config.fixed_point = baseline["base"]
            config.base_obs_file = baseline["base_file"]
            config.rover_obs_file = baseline["rover_file"]
            
            # Assigner les fichiers NAV/GNAV du rover
            rover_type = baseline["rover"].lower()
            if f"{rover_type}_nav" in self.selected_files and self.selected_files[f"{rover_type}_nav"]:
                config.rover_nav_file = self.selected_files[f"{rover_type}_nav"]
                self.log_message(f"✅ NAV {rover_type}: {config.rover_nav_file.name}")
            
            if f"{rover_type}_gnav" in self.selected_files and self.selected_files[f"{rover_type}_gnav"]:
                config.rover_gnav_file = self.selected_files[f"{rover_type}_gnav"]
                self.log_message(f"✅ GNAV {rover_type}: {config.rover_gnav_file.name}")
            
            # Assigner les fichiers NAV/GNAV de la base aussi
            base_type = baseline["base"].lower()
            if f"{base_type}_nav" in self.selected_files and self.selected_files[f"{base_type}_nav"]:
                config.base_nav_file = self.selected_files[f"{base_type}_nav"]
                self.log_message(f"✅ NAV {base_type}: {config.base_nav_file.name}")
            
            if f"{base_type}_gnav" in self.selected_files and self.selected_files[f"{base_type}_gnav"]:
                config.base_gnav_file = self.selected_files[f"{base_type}_gnav"]
                self.log_message(f"✅ GNAV {base_type}: {config.base_gnav_file.name}")
            
            # Recherche automatique des fichiers SP3/CLK si activés
            if config.use_sp3_clk:
                obs_dir = config.base_obs_file.parent
                sp3_file, clk_file = RTKFileValidator.find_sp3_clk_files(obs_dir)
                if sp3_file:
                    config.precise_eph_file = sp3_file
                    self.log_message(f"✅ SP3 trouvé pour {baseline['name']}: {sp3_file.name}")
                if clk_file:
                    config.precise_clk_file = clk_file
                    self.log_message(f"✅ CLK trouvé pour {baseline['name']}: {clk_file.name}")
            
            # Fichier de sortie pour cette ligne de base
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("export")
            output_dir.mkdir(exist_ok=True)
            config.output_file = output_dir / f"rtk_{baseline['name'].replace('→', '_to_')}_{timestamp}.pos"
            
            # Créer le calculateur
            calculator = RTKCalculator(config)
            calculator.baseline_name = baseline['name']
            calculator.baseline_index = i
            
            # Connecter les signaux
            calculator.progress_updated.connect(self.create_progress_handler(i))
            calculator.quality_updated.connect(self.create_quality_handler(i))
            calculator.process_finished.connect(self.create_finished_handler(i))
            calculator.log_message.connect(self.create_log_handler(baseline['name']))
            
            self.rtk_calculators.append(calculator)
            self.baseline_results[i] = {"status": "running", "progress": 0, "quality": {}}
        
        # Démarrer tous les calculateurs
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # Réinitialiser le flag de fin pour éviter les répétitions
        self._all_finished_called = False
        
        for calculator in self.rtk_calculators:
            calculator.start()
            self.log_message(f"🚀 Démarrage {calculator.baseline_name}")
    
    def create_progress_handler(self, baseline_index):
        """Crée un gestionnaire de progression pour une baseline"""
        def handler(message, percentage):
            self.update_parallel_progress(baseline_index, message, percentage)
        return handler
    
    def create_quality_handler(self, baseline_index):
        """Crée un gestionnaire de qualité pour une baseline"""
        def handler(quality_data):
            self.update_parallel_quality(baseline_index, quality_data)
        return handler
    
    def create_finished_handler(self, baseline_index):
        """Crée un gestionnaire de fin pour une baseline"""
        def handler(return_code):
            self.on_parallel_baseline_finished(baseline_index, return_code)
        return handler
    
    def create_log_handler(self, baseline_name):
        """Crée un gestionnaire de log pour une baseline"""
        def handler(message):
            self.log_message(f"[{baseline_name}] {message}")
        return handler
    
    def update_parallel_progress(self, baseline_index: int, message: str, percentage: int):
        """Met à jour la progression d'une ligne de base spécifique"""
        baseline_name = self.rtk_calculators[baseline_index].baseline_name
        self.baseline_results[baseline_index]["progress"] = percentage
        
        # Mettre à jour la barre de progression spécifique
        if baseline_name in self.progress_bars:
            self.progress_bars[baseline_name].setValue(percentage)
            self.progress_bars[baseline_name].setFormat(f"{message} ({percentage}%)")
            
            # Mettre à jour le statut
            if percentage == 0:
                self.progress_labels[baseline_name].setText("🚀")
            elif percentage < 100:
                self.progress_labels[baseline_name].setText("⏳")
            else:
                self.progress_labels[baseline_name].setText("✅")
        
        # Émettre le signal baseline
        self.baseline_progress_updated.emit(baseline_name, percentage, message)
    
    def update_parallel_quality(self, baseline_index: int, quality_data: dict):
        """Met à jour la qualité pour une ligne de base spécifique"""
        self.baseline_results[baseline_index]["quality"] = quality_data
        
        # Mettre à jour le diagramme individuel de cette baseline
        baseline_name = self.rtk_calculators[baseline_index].baseline_name
        if baseline_name in self.donut_widgets:
            self.donut_widgets[baseline_name].update_data(quality_data)
    
    def on_parallel_baseline_finished(self, baseline_index: int, return_code: int):
        """Une ligne de base terminée dans le calcul parallèle"""
        # Garde pour éviter les répétitions
        if baseline_index not in self.baseline_results:
            return
        
        current_status = self.baseline_results[baseline_index]["status"]
        if current_status in ["success", "error"]:
            # Déjà traité, éviter la répétition
            return
            
        baseline_name = self.rtk_calculators[baseline_index].baseline_name
        
        if return_code == 0:
            self.baseline_results[baseline_index]["status"] = "success"
            self.log_message(f"✅ {baseline_name} terminé avec succès")
            # Mettre à jour le statut visuel
            if baseline_name in self.progress_labels:
                self.progress_labels[baseline_name].setText("✅")
            self.baseline_progress_updated.emit(baseline_name, 100, "Terminé")
        else:
            self.baseline_results[baseline_index]["status"] = "error"
            self.log_message(f"❌ {baseline_name} échoué (code: {return_code})")
            # Mettre à jour le statut visuel
            if baseline_name in self.progress_labels:
                self.progress_labels[baseline_name].setText("❌")
            self.baseline_progress_updated.emit(baseline_name, 100, f"Erreur (code: {return_code})")
        
        # Vérifier si tous les calculs sont terminés
        all_finished = all(result["status"] in ["success", "error"] for result in self.baseline_results.values())
        
        if all_finished:
            self._on_all_parallel_baselines_finished()
    
    def _on_all_parallel_baselines_finished(self):
        """Toutes les lignes de base parallèles sont terminées"""
        # Garde pour éviter les appels multiples
        if not hasattr(self, '_all_finished_called'):
            self._all_finished_called = True
        else:
            return  # Déjà appelé, éviter la répétition
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Compter les succès et échecs
        successful_baselines = [name for i, result in self.baseline_results.items() 
                             if result["status"] == "success" 
                             for name in [self.rtk_calculators[i].baseline_name]]
        failed_baselines = [name for i, result in self.baseline_results.items() 
                           if result["status"] == "error" 
                           for name in [self.rtk_calculators[i].baseline_name]]
        
        # Préparer les résultats pour le signal
        results = {
            "total_baselines": len(self.baselines_to_calculate),
            "successful_baselines": successful_baselines,
            "failed_baselines": failed_baselines,
            "quality_data": {}  # Plus de donut global, chaque baseline a son propre diagramme
        }
        
        # Réinitialiser toutes les barres de progression
        for baseline_name in self.progress_bars:
            self.progress_bars[baseline_name].setValue(0)
            self.progress_bars[baseline_name].setFormat("En attente...")
            self.progress_labels[baseline_name].setText("⏸️")
            # Réinitialiser le diagramme individuel
            if baseline_name in self.donut_widgets:
                self.donut_widgets[baseline_name].update_data({})
        
        self.log_message(f"🎉 Calculs parallèles terminés: {len(successful_baselines)} succès, {len(failed_baselines)} échecs")
        
        # Émettre le signal de completion global
        self.processing_completed.emit(results)
    
    def stop_calculation(self):
        """Arrête tous les calculs"""
        if hasattr(self, 'rtk_calculators'):
            # Arrêter tous les calculateurs parallèles
            for calculator in self.rtk_calculators:
                if calculator.isRunning():
                    calculator.stop()
            self.log_message("⏹️ Arrêt de tous les calculs demandé")
            
            # Réinitialiser les barres de progression
            for baseline_name in self.progress_bars:
                self.progress_bars[baseline_name].setValue(0)
                self.progress_bars[baseline_name].setFormat("Arrêté")
                self.progress_labels[baseline_name].setText("⏹️")
                # Réinitialiser le diagramme individuel
                if baseline_name in self.donut_widgets:
                    self.donut_widgets[baseline_name].update_data({})
                
        elif self.rtk_calculator and self.rtk_calculator.isRunning():
            # Arrêter le calculateur unique (ancien mode)
            self.rtk_calculator.stop()
            self.log_message("⏹️ Arrêt demandé")
    
    def log_message(self, message: str):
        """Ajoute un log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

