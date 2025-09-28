# quick_actions_widget.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QPushButton, QSpacerItem, QSizePolicy, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

class QuickActionsWidget(QWidget):
    """
    Widget fournissant des boutons pour les actions courantes du projet.
    """
    
    # Définition des signaux pour chaque action
    statistics_requested = pyqtSignal()
    export_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    save_requested = pyqtSignal()
    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickActionsWidget")
        
        # Dictionnaire pour accéder facilement aux boutons
        self.buttons = {}
        
        try:
            self.setup_ui()
            self.apply_styles()
            self.set_project_loaded(False) # Désactiver les boutons au démarrage
            print("✅ QuickActionsWidget initialisé avec succès")
        except Exception as e:
            print(f"❌ Erreur initialisation QuickActionsWidget: {e}")
            import traceback
            traceback.print_exc()
            self.setup_fallback_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur du widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        try:
            group_box = QGroupBox("Actions Rapides")
            group_box.setObjectName("actionsGroupBox")
            
            grid_layout = QGridLayout(group_box)
            grid_layout.setSpacing(15)

            # Configuration des boutons (texte, icône, signal, tooltip)
            actions = [
                ("save", "💾 Sauvegarder", self.save_requested, "Sauvegarder les modifications du projet"),
                ("export", "📄 Exporter", self.export_requested, "Exporter un rapport ou des données"),
                ("stats", "📊 Statistiques", self.statistics_requested, "Afficher les statistiques détaillées"),
                ("refresh", "🔄 Rafraîchir", self.refresh_requested, "Actualiser toutes les données et affichages"),
            ]

            for i, (key, text, signal, tooltip) in enumerate(actions):
                try:
                    button = QPushButton(text)
                    button.setObjectName(f"{key}Button")
                    button.setToolTip(tooltip)
                    button.clicked.connect(signal.emit)
                    button.setMinimumHeight(50) # Rendre les boutons plus grands
                    
                    self.buttons[key] = button
                    
                    # Positionnement dans la grille (2 colonnes)
                    row, col = divmod(i, 2)
                    if i == len(actions) - 1 and col == 0: # Si le dernier est seul sur sa ligne
                        grid_layout.addWidget(button, row, 0, 1, 2) # L'étendre sur 2 colonnes
                    else:
                        grid_layout.addWidget(button, row, col)
                        
                    print(f"✅ Bouton {key} créé")
                    
                except Exception as e:
                    print(f"❌ Erreur création bouton {key}: {e}")
                    # Créer un bouton de secours
                    button = QPushButton(f"ERREUR {key}")
                    button.setEnabled(False)
                    self.buttons[key] = button
                    grid_layout.addWidget(button, i // 2, i % 2)

            main_layout.addWidget(group_box)
            main_layout.addStretch()
            
            print("✅ Interface QuickActionsWidget créée")
            
        except Exception as e:
            print(f"❌ Erreur setup_ui QuickActionsWidget: {e}")
            raise

    def setup_fallback_ui(self):
        """Interface de secours en cas d'erreur"""
        try:
            fallback_layout = QVBoxLayout(self)
            
            error_label = QLabel("❌ ERREUR QUICK ACTIONS\n\nMode de secours activé.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    background-color: #2d2d30;
                    border: 2px solid #ff6b6b;
                    border-radius: 8px;
                    padding: 20px;
                    color: #ffffff;
                    font-size: 12px;
                }
            """)
            
            # Créer des boutons de secours
            fallback_buttons = [
                ("save", "Sauv. (ERR)"),
                ("export", "Export (ERR)"),
                ("stats", "Stats (ERR)"),
                ("refresh", "Refresh (ERR)")
            ]
            
            self.buttons = {}
            for key, text in fallback_buttons:
                button = QPushButton(text)
                button.setEnabled(False)
                self.buttons[key] = button
                fallback_layout.addWidget(button)
            
            fallback_layout.addWidget(error_label)
            fallback_layout.addStretch()
            
            print("⚠️ Interface de secours QuickActionsWidget activée")
            
        except Exception as e:
            print(f"❌ Erreur critique setup_fallback_ui QuickActionsWidget: {e}")

    def apply_styles(self):
        """Applique le style visuel du widget."""
        try:
            self.setStyleSheet("""
                #quickActionsWidget {
                    background-color: transparent;
                }
                #actionsGroupBox {
                    background-color: #2d2d30;
                    border: 1px solid #555558;
                    border-radius: 8px;
                    padding: 15px;
                    font-weight: bold;
                    color: #ffffff;
                }
                #actionsGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 10px;
                    color: #0d7377;
                }
                QPushButton {
                    background-color: #3e3e42;
                    color: #ffffff;
                    border: 1px solid #555558;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #0d7377;
                    border-color: #14a085;
                }
                QPushButton:pressed {
                    background-color: #0a5d61;
                }
                QPushButton:disabled {
                    background-color: #4a4a50;
                    color: #888888;
                    border-color: #555558;
                }
            """)
            print("✅ Styles QuickActionsWidget appliqués")
        except Exception as e:
            print(f"❌ Erreur application styles QuickActionsWidget: {e}")

    def set_project_loaded(self, loaded: bool):
        """
        Active ou désactive les boutons en fonction de l'état du projet.
        """
        try:
            # Les autres boutons dépendent du chargement d'un projet
            button_states = {
                "save": loaded,
                "export": loaded,
                "stats": loaded,
                "refresh": loaded  # Le refresh peut être utile même sans projet
            }
            
            for button_key, enabled in button_states.items():
                if button_key in self.buttons and self.buttons[button_key]:
                    try:
                        self.buttons[button_key].setEnabled(enabled)
                    except Exception as e:
                        print(f"❌ Erreur activation bouton {button_key}: {e}")
            
            status = "activés" if loaded else "désactivés"
            print(f"📊 Boutons QuickActions {status}")
            
        except Exception as e:
            print(f"❌ Erreur set_project_loaded: {e}")
        
    def show_action_feedback(self, action_key: str, message: str, duration: int = 2000):
        """
        Fournit un retour visuel temporaire sur un bouton après une action.
        """
        try:
            if action_key not in self.buttons or not self.buttons[action_key]:
                print(f"❌ Bouton {action_key} non trouvé pour feedback")
                return
                
            button = self.buttons[action_key]
            original_text = button.text()
            
            button.setText(message)
            button.setEnabled(False) # Désactiver pendant le feedback
            
            # Revenir à l'état normal après une durée
            QTimer.singleShot(duration, lambda: self.reset_button_state(button, original_text))
            
            print(f"📊 Feedback affiché pour {action_key}: {message}")
            
        except Exception as e:
            print(f"❌ Erreur show_action_feedback: {e}")

    def reset_button_state(self, button: QPushButton, original_text: str):
        """Réinitialise le texte et l'état d'un bouton."""
        try:
            if button:
                button.setText(original_text)
                button.setEnabled(True)
        except Exception as e:
            print(f"❌ Erreur reset_button_state: {e}")
    
    def get_button(self, action_key: str):
        """Retourne un bouton spécifique (pour tests ou interactions externes)"""
        return self.buttons.get(action_key)
    
    def enable_button(self, action_key: str, enabled: bool = True):
        """Active/désactive un bouton spécifique"""
        try:
            if action_key in self.buttons and self.buttons[action_key]:
                self.buttons[action_key].setEnabled(enabled)
        except Exception as e:
            print(f"❌ Erreur enable_button {action_key}: {e}")
    
    def set_button_text(self, action_key: str, text: str):
        """Change le texte d'un bouton spécifique"""
        try:
            if action_key in self.buttons and self.buttons[action_key]:
                self.buttons[action_key].setText(text)
        except Exception as e:
            print(f"❌ Erreur set_button_text {action_key}: {e}")


# --- Test du widget si exécuté directement ---
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    widget = QuickActionsWidget()
    widget.setWindowTitle("Test QuickActionsWidget")
    
    # Simuler le chargement d'un projet pour activer les boutons
    widget.set_project_loaded(True)
    
    # Connecter les signaux pour vérifier leur fonctionnement
    widget.save_requested.connect(lambda: print("Signal 'save_requested' émis !"))
    widget.export_requested.connect(lambda: print("Signal 'export_requested' émis !"))
    widget.statistics_requested.connect(lambda: print("Signal 'statistics_requested' émis !"))
    widget.refresh_requested.connect(lambda: print("Signal 'refresh_requested' émis !"))
    
    # Tester le feedback visuel
    if "save" in widget.buttons:
        widget.buttons["save"].clicked.connect(lambda: widget.show_action_feedback("save", "✅ Sauvegardé !"))

    widget.resize(400, 200)
    widget.show()
    
    sys.exit(app.exec_())