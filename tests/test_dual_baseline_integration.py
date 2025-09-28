#!/usr/bin/env python3
"""
Script de test pour l'intégration du traitement des deux lignes de base
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Import des modules du projet
from src.core.project_manager import ProjectManager
from src.core.progress_manager import ProgressManager
from src.app.gui.dual_baseline_integration import DualBaselineIntegrationWidget


class TestMainWindow(QMainWindow):
    """Fenêtre principale de test"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Intégration Deux Lignes de Base")
        self.setGeometry(100, 100, 1200, 800)
        
        # Créer les gestionnaires
        self.project_manager = ProjectManager.instance()
        self.progress_manager = ProgressManager()
        
        # Créer le widget d'intégration
        self.integration_widget = DualBaselineIntegrationWidget(
            self.project_manager, 
            self.progress_manager
        )
        
        # Configurer la fenêtre
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.integration_widget)
        
        # Connecter les signaux
        self.integration_widget.processing_completed.connect(self.on_processing_completed)
        self.integration_widget.step_completed.connect(self.on_step_completed)
        
        # Charger un projet de test si disponible
        self.load_test_project()
    
    def load_test_project(self):
        """Charge un projet de test"""
        try:
            # Chercher un projet existant
            projects_dir = Path("projets")
            if projects_dir.exists():
                project_files = list(projects_dir.glob("**/*.json"))
                if project_files:
                    # Charger le premier projet trouvé
                    project_file = project_files[0]
                    success, message = self.project_manager.load_project(str(project_file))
                    if success:
                        print(f"✅ Projet de test chargé: {project_file.name}")
                    else:
                        print(f"❌ Erreur chargement projet: {message}")
                else:
                    print("⚠️ Aucun projet de test trouvé")
            else:
                print("⚠️ Répertoire projets non trouvé")
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement du projet de test: {e}")
    
    def on_processing_completed(self, results):
        """Gère la fin du traitement complet"""
        print("🎉 Traitement complet terminé!")
        print(f"Résultats: {results}")
    
    def on_step_completed(self, step_name, result):
        """Gère la fin d'une étape"""
        print(f"✓ Étape {step_name} terminée: {result.get('status', 'unknown')}")


def main():
    """Fonction principale"""
    print("🚀 Démarrage du test d'intégration")
    
    # Créer l'application
    app = QApplication(sys.argv)
    app.setApplicationName("Test Dual Baseline Integration")
    
    # Créer la fenêtre principale
    window = TestMainWindow()
    window.show()
    
    print("✅ Interface de test lancée")
    print("📋 Instructions:")
    print("   1. Vérifiez qu'un projet est chargé")
    print("   2. Cliquez sur 'Démarrer RTKLIB' pour tester le traitement")
    print("   3. Une fois RTKLIB terminé, cliquez sur 'Démarrer Préparation'")
    print("   4. Consultez les onglets pour voir les résultats")
    
    # Lancer l'application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
