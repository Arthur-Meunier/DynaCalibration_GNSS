#!/usr/bin/env python3
"""
Test de la navigation automatique après calculs
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer

from app.gui.page_GNSS import GnssWidget
from app.gui.page_GNSSpostcalc import GNSSPostCalcWidget
from core.project_manager import ProjectManager
from core.app_data import ApplicationData

class TestNavigationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("🧪 Test Navigation Automatique")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #ECEFF4;")
        layout.addWidget(title)
        
        # Widgets
        self.project_manager = ProjectManager.instance()
        self.app_data = ApplicationData()
        
        # Widget GNSS
        self.gnss_widget = GnssWidget(
            app_data=self.app_data,
            project_manager=self.project_manager,
            parent=self
        )
        layout.addWidget(self.gnss_widget)
        
        # Widget Post-Calcul
        self.postcalc_widget = GNSSPostCalcWidget(
            app_data=self.app_data,
            project_manager=self.project_manager,
            parent=self
        )
        layout.addWidget(self.postcalc_widget)
        self.postcalc_widget.hide()  # Caché au début
        
        # Boutons de test
        self.test_btn = QPushButton("🧪 Tester Calculs + Navigation")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #A3BE8C;
                color: #2E3440;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover { background-color: #B5C99A; }
        """)
        self.test_btn.clicked.connect(self.test_navigation)
        layout.addWidget(self.test_btn)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #3B4252;
                color: #ECEFF4;
                border: 1px solid #4C566A;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Connecter les signaux
        self.gnss_widget.processing_completed.connect(self.on_processing_completed)
        
    def log(self, message):
        """Ajoute un message au log"""
        self.log_text.append(f"[{QTimer().remainingTime()}] {message}")
        print(message)
        
    def test_navigation(self):
        """Teste les calculs et la navigation"""
        self.log("🧪 Début du test de navigation...")
        
        # Créer des fichiers de test
        test_files = {
            "port_obs": Path("data/raw/port_test.txt"),
            "bow_obs": Path("data/raw/bow_test.txt"),
            "stbd_obs": Path("data/raw/stbd_test.txt")
        }
        
        for file_type, file_path in test_files.items():
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(f"# Fichier de test {file_type}\n# Données simulées\n")
                self.log(f"✅ Fichier de test créé: {file_path}")
            
            # Sélectionner le fichier
            self.gnss_widget.select_file(file_type, file_path)
            self.log(f"✅ Fichier {file_type} sélectionné")
        
        # Lancer les calculs
        try:
            self.log("🚀 Lancement des calculs...")
            self.gnss_widget.start_calculation()
            self.log("✅ Calculs lancés!")
            
            # Programmer la vérification de navigation après 5 secondes
            QTimer.singleShot(5000, self.check_navigation)
            
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def on_processing_completed(self, results):
        """Appelé quand les calculs sont terminés"""
        self.log(f"🎉 Calculs terminés! Résultats: {results}")
        
        # Simuler la navigation automatique
        self.log("📊 Navigation vers la page post-calcul...")
        QTimer.singleShot(2000, self.show_postcalc)
    
    def show_postcalc(self):
        """Affiche la page post-calcul"""
        self.log("📊 Affichage de la page post-calcul")
        self.gnss_widget.hide()
        self.postcalc_widget.show()
        self.postcalc_widget.load_project_stats()
    
    def check_navigation(self):
        """Vérifie si la navigation s'est produite"""
        if self.postcalc_widget.isVisible():
            self.log("✅ Navigation automatique réussie!")
        else:
            self.log("❌ Navigation automatique échouée")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Style sombre
    dark_stylesheet = """
        QWidget {
            background-color: #2E3440;
            color: #ECEFF4;
        }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = TestNavigationWindow()
    window.setWindowTitle("🧪 Test Navigation Automatique")
    window.resize(1000, 800)
    window.show()
    
    print("🧪 Application de test de navigation lancée")
    print("📝 Instructions:")
    print("   1. Cliquez sur 'Tester Calculs + Navigation'")
    print("   2. Observez les logs dans la fenêtre")
    print("   3. Vérifiez que la navigation automatique fonctionne")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

