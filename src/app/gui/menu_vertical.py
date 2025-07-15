from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSlot

class VerticalMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("verticalMenu")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initialisation des variables
        self.buttons = []
        self.current_index = 0
        self.parent_window = parent
        
        # Titre du menu
        self.title_label = QLabel("CALIBRATION")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: white;
            background-color: #2d2d30;
            padding: 15px 5px;
            border-bottom: 1px solid #3a3a3d;
        """)
        self.layout.addWidget(self.title_label)
        
        # Définition des menus - MISE À JOUR avec la nouvelle page
        self.menus = [
            {
                "title": "Accueil", 
                "description": "Écran d'accueil. Bienvenue dans le logiciel de calibration des capteurs de navigation."
            },
            {
                "title": "Dimcon", 
                "description": "Configuration des points de référence du navire dans le système de navigation. Définition des coordonnées relatives des points clés."
            },
            {
                "title": "GNSS", 
                "description": "Configuration et import des données GNSS. Gestion des points fixes et mobiles pour la géoréférence."
            },
            {
                "title": "Observation", 
                "description": "Import et traitement des données de capteurs (MRU, Compas, Octans). Calculs de transformation avec matrices de rotation et méthode de Cholesky."
            },
            {
                "title": "Résultats", 
                "description": "Visualisation des résultats de calibration, matrices de transformation et métriques de qualité. Export des rapports finaux."
            }
        ]
        
        # Créer le widget pour la description
        self.description_container = QWidget()
        self.description_layout = QVBoxLayout(self.description_container)
        self.description_layout.setContentsMargins(10, 10, 10, 10)
        
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.description_label.setStyleSheet("font-size: 12px; color: #cccccc; padding: 5px;")
        self.description_label.setText(self.menus[0]["description"])
        
        self.description_layout.addWidget(self.description_label)
        self.layout.addWidget(self.description_container)
        
        # Ajouter un espaceur pour pousser les boutons vers le bas
        self.layout.addStretch(1)
        
        # Boutons de menu
        for i, menu in enumerate(self.menus):
            btn = QPushButton(menu["title"])
            btn.setCheckable(True)
            btn.setProperty("index", i)
            btn.clicked.connect(self.on_button_clicked)
            self.layout.addWidget(btn)
            self.buttons.append(btn)
        
        # Sélectionner le premier bouton par défaut
        self.buttons[0].setChecked(True)
        self.update_styles()
    
    @pyqtSlot()
    def on_button_clicked(self):
        sender = self.sender()
        index = sender.property("index")
        
        # Définir l'index actuel
        self.current_index = index
        
        # Mettre à jour le contenu de la description
        self.description_label.setText(self.menus[index]["description"])
        
        # Mettre à jour les styles des boutons
        self.update_styles()
        
        # Changer le widget affiché dans la zone de contenu
        if self.parent_window:
            self.parent_window.content_area.setCurrentIndex(index)
            
            # Message de debug pour suivre la navigation
            page_names = ["Accueil", "Dimcon", "GNSS", "Observation", "Résultats"]
            if index < len(page_names):
                print(f"🔄 Navigation vers: {page_names[index]}")
    
    def update_styles(self):
        # Mettre à jour les styles de tous les boutons
        for i, btn in enumerate(self.buttons):
            if i == self.current_index:
                # Style pour le bouton actif
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8e44ad;
                        color: white;
                        font-weight: bold;
                        font-size: 14px;
                        text-align: left;
                        padding: 12px 15px;
                        border: none;
                        border-left: 4px solid #9b59b6;
                    }
                """)
            else:
                # Style pour les boutons inactifs
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: white;
                        font-size: 14px;
                        text-align: left;
                        padding: 12px 15px;
                        border: none;
                        border-top: 1px solid #3a3a3d;
                    }
                    QPushButton:hover {
                        background-color: #333333;
                        border-left: 3px solid #8e44ad;
                    }
                """)
    
    def set_active_page(self, page_index):
        """Permet de définir la page active programmatiquement"""
        if 0 <= page_index < len(self.buttons):
            self.current_index = page_index
            self.description_label.setText(self.menus[page_index]["description"])
            self.update_styles()
            
            # Déclencher le changement de page
            if self.parent_window:
                self.parent_window.content_area.setCurrentIndex(page_index)