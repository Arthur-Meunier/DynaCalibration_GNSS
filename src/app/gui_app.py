# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 01:46:46 2025

@author: a.meunier
"""

# src/app/gui_app.py
"""
Application principale GUI pour la calibration des capteurs de navigation.

Cette application fournit une interface graphique complète pour :
- Configuration des points DIMCON
- Import et traitement des données GNSS  
- Import et analyse des données d'observation (MRU, Compas, Octans)
- Calcul des transformations et matrices de rotation
- Affichage des résultats et export des rapports
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QHBoxLayout, 
    QWidget, QMessageBox, QSplashScreen, QLabel
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter

# Imports des modules de l'application
from .gui.menu_vertical import VerticalMenu
from .gui.page_accueil import HomePageWidget
from .gui.page_dimcon import DimconWidget
from .gui.page_gnss import GnssWidget
from .gui.page_observation import ObservationWidget
from .gui.app_data import ApplicationData

class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application de calibration.
    
    Intègre tous les modules dans une interface unifiée avec navigation
    par menu vertical et gestion centralisée des données.
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.setWindowTitle("Calibration Navigation - Capteurs GNSS/IMU v1.0")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)
        
        # Modèle de données central - CRITIQUE pour le fonctionnement
        print("🔧 Initialisation du modèle de données central...")
        self.app_data = ApplicationData()
        
        # Interface utilisateur
        self.setup_ui()
        
        # Thème et styles
        self.apply_application_theme()
        
        # Connexions de signaux
        self.setup_connections()
        
        print("✅ Application principale initialisée")
    
    def setup_ui(self):
        """Configure l'interface utilisateur principale."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Menu vertical de navigation
        print("🔧 Création du menu de navigation...")
        self.menu = VerticalMenu(self)
        self.menu.setFixedWidth(280)
        main_layout.addWidget(self.menu)
        
        # Zone de contenu principal avec pages empilées
        print("🔧 Configuration de la zone de contenu...")
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)
        
        # Créer et configurer toutes les pages
        self.setup_all_pages()
    
    def setup_all_pages(self):
        """
        Crée et configure toutes les pages de l'application.
        
        IMPORTANT: L'ordre d'ajout doit correspondre aux indices
        utilisés dans le menu vertical.
        """
        
        # Page 0: Accueil
        print("🔧 Configuration page Accueil...")
        home_page = HomePageWidget()
        self.content_area.addWidget(home_page)
        
        # Page 1: Dimcon (Points de référence du navire)
        print("🔧 Configuration page Dimcon...")
        try:
            dimcon_page = DimconWidget()
            dimcon_page.set_data_model(self.app_data)
            self.content_area.addWidget(dimcon_page)
            print("✅ Page Dimcon configurée")
        except Exception as e:
            print(f"❌ Erreur page Dimcon: {e}")
            # Page de fallback
            fallback_page = QWidget()
            fallback_label = QLabel(f"Erreur chargement Dimcon: {e}")
            fallback_label.setStyleSheet("color: red; padding: 20px;")
            fallback_layout = QHBoxLayout(fallback_page)
            fallback_layout.addWidget(fallback_label)
            self.content_area.addWidget(fallback_page)
        
        # Page 2: GNSS (Configuration et données GNSS)
        print("🔧 Configuration page GNSS...")
        try:
            gnss_page = GnssWidget()
            gnss_page.set_data_model(self.app_data)
            self.content_area.addWidget(gnss_page)
            print("✅ Page GNSS configurée")
        except Exception as e:
            print(f"❌ Erreur page GNSS: {e}")
            # Page de fallback
            fallback_page = QWidget()
            fallback_label = QLabel(f"Erreur chargement GNSS: {e}")
            fallback_label.setStyleSheet("color: red; padding: 20px;")
            fallback_layout = QHBoxLayout(fallback_page)
            fallback_layout.addWidget(fallback_label)
            self.content_area.addWidget(fallback_page)
        
        # Page 3: Observation (Capteurs MRU, Compas, Octans)
        print("🔧 Configuration page Observation...")
        try:
            observation_page = ObservationWidget()
            observation_page.set_data_model(self.app_data)
            self.content_area.addWidget(observation_page)
            print("✅ Page Observation configurée")
        except Exception as e:
            print(f"❌ Erreur page Observation: {e}")
            import traceback
            traceback.print_exc()
            # Page de fallback
            fallback_page = QWidget()
            fallback_label = QLabel(f"Erreur chargement Observation:\n{e}\n\nVérifiez les imports des modules de calcul.")
            fallback_label.setStyleSheet("color: red; padding: 20px;")
            fallback_label.setWordWrap(True)
            fallback_layout = QHBoxLayout(fallback_page)
            fallback_layout.addWidget(fallback_label)
            self.content_area.addWidget(fallback_page)
        
        # Page 4: Résultats (Analyse et export)
        print("🔧 Configuration page Résultats...")
        results_page = self.create_results_page()
        self.content_area.addWidget(results_page)
        
        print(f"✅ {self.content_area.count()} pages configurées")
    
    def create_results_page(self):
        """
        Crée la page des résultats (placeholder pour l'instant).
        
        Returns:
            QWidget: Page des résultats
        """
        results_page = QWidget()
        results_layout = QHBoxLayout(results_page)
        
        results_label = QLabel("""
        📊 PAGE RÉSULTATS
        
        Cette page affichera :
        • Synthèse des données importées
        • Matrices de transformation calculées  
        • Métriques de qualité
        • Export des rapports
        
        🚧 En cours de développement...
        """)
        
        results_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            padding: 20px;
            background-color: #353535;
            border-radius: 5px;
            margin: 20px;
        """)
        results_label.setAlignment(Qt.AlignCenter)
        
        results_layout.addWidget(results_label)
        return results_page
    
    def setup_connections(self):
        """Configure les connexions de signaux entre composants."""
        
        # Connexion des signaux de changement de données
        if hasattr(self.app_data, 'data_changed'):
            self.app_data.data_changed.connect(self.on_data_changed)
            print("✅ Signaux de données connectés")
        
        # Autres connexions peuvent être ajoutées ici
    
    def on_data_changed(self, section):
        """
        Gestionnaire pour les changements de données.
        
        Args:
            section (str): Section des données qui a changé
        """
        print(f"📊 Données mises à jour: {section}")
        
        # Ici on peut ajouter la logique pour :
        # - Sauvegarder automatiquement
        # - Mettre à jour d'autres vues
        # - Recalculer des résultats
        # - etc.
    
    def apply_application_theme(self):
        """Applique le thème sombre cohérent à toute l'application."""
        
        app_style = """
        QMainWindow {
            background-color: #2d2d30;
            color: white;
        }
        
        QWidget {
            background-color: #2d2d30;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
        }
        
        QStackedWidget {
            background-color: #3a3a3d;
            border: none;
        }
        
        /* Barres de défilement */
        QScrollBar:vertical {
            background-color: #404040;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #8e44ad;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #9b59b6;
        }
        
        /* Messages d'erreur et info */
        QMessageBox {
            background-color: #2d2d30;
            color: white;
        }
        
        QMessageBox QLabel {
            color: white;
        }
        
        QMessageBox QPushButton {
            background-color: #8e44ad;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #9b59b6;
        }
        """
        
        self.setStyleSheet(app_style)
        print("✅ Thème appliqué")
    
    def closeEvent(self, event):
        """
        Gestionnaire de fermeture de l'application.
        
        Propose de sauvegarder les données avant fermeture.
        """
        reply = QMessageBox.question(
            self,
            "Fermeture de l'application",
            "Voulez-vous sauvegarder les données avant de quitter ?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            # TODO: Implémenter la sauvegarde
            print("💾 Sauvegarde des données...")
            event.accept()
        elif reply == QMessageBox.Discard:
            print("🚪 Fermeture sans sauvegarde")
            event.accept()
        else:
            event.ignore()

class SplashScreen(QSplashScreen):
    """Écran de démarrage pour l'application."""
    
    def __init__(self):
        # Créer un pixmap simple pour le splash screen
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.black)
        
        super().__init__(pixmap)
        
        # Ajouter du texte
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, 
                        "Calibration Navigation\n\nChargement...")
        painter.end()
        
        self.setPixmap(pixmap)

def main():
    """
    Point d'entrée principal de l'application GUI.
    
    Configure l'application Qt, affiche l'écran de démarrage,
    puis lance la fenêtre principale.
    """
    
    # Création de l'application Qt
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("Calibration Navigation")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Navigation Systems")
    app.setOrganizationDomain("navigation-systems.com")
    
    # Écran de démarrage
    splash = SplashScreen()
    splash.show()
    splash.showMessage("Initialisation des modules...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    # Traitement des événements pendant le chargement
    app.processEvents()
    
    try:
        # Création de la fenêtre principale
        splash.showMessage("Création de l'interface...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        app.processEvents()
        
        window = MainWindow()
        
        # Fermer le splash et afficher la fenêtre
        splash.finish(window)
        window.show()
        
        print("🚀 Application démarrée avec succès")
        
        # Lancement de la boucle événementielle
        sys.exit(app.exec_())
        
    except Exception as e:
        splash.close()
        
        # Afficher l'erreur
        error_msg = f"Erreur critique lors du démarrage:\n\n{str(e)}"
        print(f"❌ {error_msg}")
        
        # Boîte de dialogue d'erreur
        error_app = QApplication(sys.argv) if not app else app
        QMessageBox.critical(None, "Erreur de démarrage", error_msg)
        
        import traceback
        traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main()


# =============================================================================
# FICHIER DE LANCEMENT PRINCIPAL : src/main.py
# =============================================================================

# src/main.py
#!/usr/bin/env python3
"""
Point d'entrée principal de l'application de calibration des capteurs.

Ce script configure l'environnement Python et lance l'application GUI.
Il peut être exécuté directement ou utilisé comme module.

Usage:
    python src/main.py
    ou
    python -m src.main
"""

import sys
import os
from pathlib import Path

def setup_python_path():
    """
    Configure le PYTHONPATH pour permettre les imports relatifs.
    
    Ajoute le répertoire racine du projet au sys.path pour que
    les imports depuis src/ fonctionnent correctement.
    """
    # Répertoire du script actuel
    current_file = Path(__file__).resolve()
    
    # Répertoire racine du projet (parent de src/)
    project_root = current_file.parent.parent
    
    # Répertoire src/
    src_dir = current_file.parent
    
    # Ajouter au PYTHONPATH
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    print(f"📁 Répertoire projet: {project_root}")
    print(f"📁 Répertoire src: {src_dir}")
    
    return project_root, src_dir

def check_dependencies():
    """
    Vérifie que toutes les dépendances sont installées.
    
    Returns:
        bool: True si toutes les dépendances sont disponibles
    """
    required_packages = [
        'PyQt5',
        'numpy', 
        'pandas',
        'scipy',
        'matplotlib',
        'pyqtgraph'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Packages manquants: {', '.join(missing_packages)}")
        print(f"💡 Installez avec: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Toutes les dépendances sont disponibles")
    return True

def main():
    """Fonction principale."""
    
    print("=" * 60)
    print("🛰️ CALIBRATION NAVIGATION - DÉMARRAGE")
    print("=" * 60)
    
    # Configuration des chemins
    print("\n🔧 Configuration de l'environnement...")
    project_root, src_dir = setup_python_path()
    
    # Vérification des dépendances
    print("\n🔍 Vérification des dépendances...")
    if not check_dependencies():
        print("\n❌ Impossible de démarrer - dépendances manquantes")
        sys.exit(1)
    
    # Test des imports critiques
    print("\n🔍 Test des imports critiques...")
    try:
        # Test import du module GUI principal
        from app.gui_app import main as gui_main
        print("✅ Module GUI principal")
        
        # Test import des modules de base
        from app.gui.app_data import ApplicationData
        print("✅ Modèle de données")
        
        # Test import des calculateurs
        from app.core.calculations.calculs_observation import ObservationCalculator
        print("✅ Calculateur d'observations")
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez que tous les fichiers __init__.py sont présents")
        print("   2. Vérifiez la structure des répertoires")
        print("   3. Exécutez le script check_imports.py")
        sys.exit(1)
    
    # Lancement de l'application
    print("\n🚀 Lancement de l'application...")
    print("=" * 60)
    
    try:
        gui_main()
    except KeyboardInterrupt:
        print("\n👋 Arrêt par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()