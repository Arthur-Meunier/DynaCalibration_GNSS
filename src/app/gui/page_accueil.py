from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class HomePageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Configuration de la mise en page
        self.layout = QVBoxLayout(self)
        
        self.welcome_label = QLabel("Bienvenue dans l'Application d'Analyse de Données")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        
        self.home_description = QLabel(
            "Cette application vous permet d'explorer et d'analyser vos données de manière interactive. "
            "Utilisez le menu de gauche pour naviguer entre les différentes fonctionnalités."
        )
        self.home_description.setWordWrap(True)
        self.home_description.setAlignment(Qt.AlignCenter)
        self.home_description.setStyleSheet("font-size: 16px; margin: 20px; color: #cccccc;")
        
        # Widget décoratif pour l'accueil
        self.home_decorative = QWidget()
        self.home_decorative.setStyleSheet("""
            background-color: #8e44ad;
            border-radius: 10px;
        """)
        self.home_decorative.setFixedHeight(5)
        self.home_decorative.setMaximumWidth(100)
        
        self.layout.addStretch(2)
        self.layout.addWidget(self.welcome_label, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.home_decorative, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.home_description, alignment=Qt.AlignCenter)
        self.layout.addStretch(3)
    
    def apply_theme(self, theme):
        if theme == "dark":
            self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px; color: white;")
            self.home_description.setStyleSheet("font-size: 16px; margin: 20px; color: #cccccc;")
        else:
            self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px; color: #333;")
            self.home_description.setStyleSheet("font-size: 16px; margin: 20px; color: #555555;")
