#!/usr/bin/env python3
"""
Test simple pour vérifier le lancement des calculs GNSS
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer

from app.gui.page_GNSS import GnssWidget
from core.project_manager import ProjectManager
from core.app_data import ApplicationData

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("🧪 Test des Calculs GNSS")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #ECEFF4;")
        layout.addWidget(title)
        
        # Widget GNSS
        self.project_manager = ProjectManager.instance()
        self.app_data = ApplicationData()
        
        self.gnss_widget = GnssWidget(
            app_data=self.app_data,
            project_manager=self.project_manager,
            parent=self
        )
        layout.addWidget(self.gnss_widget)
        
        # Bouton de test
        self.test_btn = QPushButton("🧪 Tester le Lancement des Calculs")
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
        self.test_btn.clicked.connect(self.test_calculations)
        layout.addWidget(self.test_btn)
        
        # Label de statut
        self.status_label = QLabel("Prêt pour le test")
        self.status_label.setStyleSheet("color: #ECEFF4; font-size: 11pt;")
        layout.addWidget(self.status_label)
        
    def test_calculations(self):
        """Teste le lancement des calculs"""
        self.status_label.setText("🧪 Test en cours...")
        
        # Simuler la sélection de fichiers
        test_files = {
            "port_obs": Path("data/raw/port_test.txt"),
            "bow_obs": Path("data/raw/bow_test.txt"),
            "stbd_obs": Path("data/raw/stbd_test.txt")
        }
        
        # Créer des fichiers de test s'ils n'existent pas
        for file_type, file_path in test_files.items():
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(f"# Fichier de test {file_type}\n# Données simulées\n")
                print(f"✅ Fichier de test créé: {file_path}")
            
            # Sélectionner le fichier dans le widget
            self.gnss_widget.selected_files[file_type] = file_path
            print(f"✅ Fichier {file_type} sélectionné: {file_path}")
        
        # Essayer de lancer les calculs
        try:
            print("🚀 Tentative de lancement des calculs...")
            self.gnss_widget.start_calculation()
            self.status_label.setText("✅ Calculs lancés avec succès!")
            print("✅ Calculs lancés avec succès!")
        except Exception as e:
            self.status_label.setText(f"❌ Erreur: {e}")
            print(f"❌ Erreur lors du lancement: {e}")
            import traceback
            traceback.print_exc()

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
    
    window = TestWindow()
    window.setWindowTitle("🧪 Test Calculs GNSS")
    window.resize(800, 600)
    window.show()
    
    print("🧪 Application de test lancée")
    print("📝 Instructions:")
    print("   1. Cliquez sur 'Tester le Lancement des Calculs'")
    print("   2. Vérifiez que les calculs se lancent sans erreur")
    print("   3. Observez les logs dans la console")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

