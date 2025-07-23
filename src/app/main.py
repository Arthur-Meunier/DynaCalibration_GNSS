import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Ajouter le répertoire src au Python path
# Cette partie est correcte et ne doit pas être changée.
# Elle garantit que 'src' est la racine de notre projet pour les imports.
current_dir = Path(__file__).parent.resolve() # Utiliser .resolve() pour un chemin absolu propre
src_dir = current_dir.parent.parent # On remonte de app -> src
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Imports de l'application
# Les imports sont maintenant "absolus" depuis le dossier 'src'
try:
    from app.gui.menu_vertical import VerticalMenu
    from app.gui.page_accueil import HomePageWidget
    from app.gui.page_Dimcon import DimconWidget  # CORRIGÉ: La casse correspond au nom de fichier
    from app.gui.page_GNSS import GnssWidget      # CORRIGÉ: La casse correspond au nom de fichier
    from app.gui.page_observation import ObservationWidget
    from app.gui.app_data import ApplicationData
    print("Tous les modules ont été importés avec succès.")
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print(f"Le chemin de recherche est: {sys.path}")
    print("Vérifiez que tous les fichiers sont présents et que la structure est correcte")
    sys.exit(1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configuration générale de la fenêtre
        self.setWindowTitle("Analyse de Données Moderne")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow, QStackedWidget, QWidget { 
                background-color: #2d2d30; 
                color: white; 
            }
            QLabel { 
                color: white; 
            }
        """)
        
        # Création du widget principal pour contenir la mise en page
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Création de la barre latérale personnalisée (1/5 de la largeur)
        self.sidebar_container = QWidget()
        self.sidebar_container.setMaximumWidth(self.width() // 5)
        self.sidebar_container.setStyleSheet("""
            background-color: #1e1e1e;
            border-right: 1px solid #333;
        """)
        
        # Création du menu vertical
        self.menu = VerticalMenu(self)
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(self.menu)
        
        # Création de la zone de contenu principal
        self.content_area = QStackedWidget()
        
        # Ajout des widgets au layout principal
        self.main_layout.addWidget(self.sidebar_container)
        self.main_layout.addWidget(self.content_area)
        self.main_layout.setStretch(0, 1)  # Sidebar prend 1 part
        self.main_layout.setStretch(1, 4)  # Content prend 4 parts (donc 1/5 vs 4/5)
        
        # Création et ajout des pages
        self.page_home = HomePageWidget()
        self.page_Dimcon = DimconWidget()
        self.page_gnss = GnssWidget()  # Nouvelle instance de la page GNSS
        #self.page_stats = StatsPageWidget()
        #self.page_settings = SettingsPageWidget()
        
        # Ajout des pages au widget empilé
        self.content_area.addWidget(self.page_home)
        self.content_area.addWidget(self.page_Dimcon)
        self.content_area.addWidget(self.page_gnss)  # Ajouter la page GNSS
        #self.content_area.addWidget(self.page_stats)
        #self.content_area.addWidget(self.page_settings)
        
        # Définir le widget principal
        self.setCentralWidget(self.central_widget)
        
        # Initialiser les connexions entre les pages et les données
        self.initialize_data_connections()
        
    def initialize_data_connections(self):
        """Initialise les connexions entre le modèle de données et les widgets"""
        # Connecter la page Dimcon aux données
        # self.page_Dimcon.set_data_model(app_data)
        
        # Connecter la page GNSS aux données
        # self.page_gnss.set_data_model(app_data)
        pass # Remplacer par la logique de connexion
    
    def resizeEvent(self, event):
        # Maintenir la barre latérale à 1/5 de la largeur lors du redimensionnement
        self.sidebar_container.setMaximumWidth(self.width() // 5)
        super().resizeEvent(event)
    
    def set_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QStackedWidget, QWidget { 
                background-color: #2d2d30; 
                color: white; 
            }
            QLabel { 
                color: white; 
            }
        """)
        self.sidebar_container.setStyleSheet("""
            background-color: #1e1e1e;
            border-right: 1px solid #333;
        """)
        # Propager le thème aux pages
        #self.page_graph.apply_theme("dark")
        #self.page_stats.apply_theme("dark")
        #self.page_settings.apply_theme("dark")
        
    def set_light_theme(self):
        self.setStyleSheet("""
            QMainWindow, QStackedWidget, QWidget { 
                background-color: #f5f5f5; 
                color: #333; 
            }
            QLabel { 
                color: #333; 
            }
        """)
        self.sidebar_container.setStyleSheet("""
            background-color: #e1e1e1;
            border-right: 1px solid #dcdcdc;
        """)
        # Propager le thème aux pages
        #self.page_graph.apply_theme("light")
        #self.page_stats.apply_theme("light")
        #self.page_settings.apply_theme("light")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
