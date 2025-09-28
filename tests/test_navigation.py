#!/usr/bin/env python3
"""
Test simple pour vérifier la navigation automatique après calculs GNSS
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import QTimer, pyqtSignal

# Ajouter le répertoire src au path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

class MockGnssWidget(QWidget):
    """Mock du GnssWidget pour tester la navigation"""
    processing_completed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.label = QLabel("Mock GNSS Widget")
        layout.addWidget(self.label)
        
        self.test_button = QPushButton("Simuler fin de calcul")
        self.test_button.clicked.connect(self.simulate_completion)
        layout.addWidget(self.test_button)
        
        self.setLayout(layout)
    
    def simulate_completion(self):
        """Simule la fin d'un calcul GNSS"""
        print("🔍 DEBUG: Simulation de la fin de calcul")
        results = {
            "total_baselines": 2,
            "successful_baselines": ["Port→Bow", "Port→Stbd"],
            "failed_baselines": [],
            "quality_data": {}
        }
        print("🔍 DEBUG: Émission du signal processing_completed")
        self.processing_completed.emit(results)
        print("🔍 DEBUG: Signal émis")

class MockMainWindow(QMainWindow):
    """Mock de la fenêtre principale pour tester la navigation"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Navigation GNSS")
        self.setGeometry(100, 100, 600, 400)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Label de statut
        self.status_label = QLabel("En attente...")
        layout.addWidget(self.status_label)
        
        # Mock du GnssWidget
        self.gnss_widget = MockGnssWidget()
        layout.addWidget(self.gnss_widget)
        
        # Connexion du signal
        self.gnss_widget.processing_completed.connect(self.on_gnss_workflow_completed)
        
        central_widget.setLayout(layout)
    
    def on_gnss_workflow_completed(self, results):
        """Gère la fin du workflow GNSS"""
        print("🔍 DEBUG: on_gnss_workflow_completed appelé")
        print(f"🔍 DEBUG: Résultats reçus: {results}")
        
        self.status_label.setText("Calculs terminés - Navigation dans 3 secondes...")
        
        # Navigation automatique après 3 secondes
        print("🔍 DEBUG: Programmation de la navigation dans 3 secondes")
        QTimer.singleShot(3000, self.navigate_to_postcalc)
    
    def navigate_to_postcalc(self):
        """Simule la navigation vers la page post-calcul"""
        print("🔍 DEBUG: Navigation vers la page post-calcul")
        self.status_label.setText("✅ Navigation vers la page post-calcul effectuée!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MockMainWindow()
    window.show()
    
    print("🔍 DEBUG: Application démarrée")
    print("🔍 DEBUG: Cliquez sur 'Simuler fin de calcul' pour tester la navigation")
    
    sys.exit(app.exec_())

