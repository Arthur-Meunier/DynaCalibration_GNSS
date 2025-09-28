# status_bar_widget.py

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime

class StatusBarWidget(QWidget):
    """
    Barre d'état affichant le statut de la sauvegarde, l'heure de mise à jour
    et l'état d'avancement des modules principaux.
    """
    
    # Signaux pour la navigation et les actions
    save_requested = pyqtSignal()
    module_indicator_clicked = pyqtSignal(str) # Émet le nom du module cliqué

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBarWidget")
        self.setFixedHeight(40)
        
        # Dictionnaire pour les indicateurs de module
        self.module_indicators = {}
        
        # Attributs pour éviter les erreurs
        self.save_status_label = None
        self.timestamp_label = None
        
        try:
            self.setup_ui()
            self.apply_styles()
            self.set_project_loaded(False)
            print("✅ StatusBarWidget initialisé avec succès")
        except Exception as e:
            print(f"❌ Erreur initialisation StatusBarWidget: {e}")
            import traceback
            traceback.print_exc()
            self.setup_fallback_ui()

    def setup_ui(self):
        """Configure l'interface de la barre d'état."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 5, 15, 5)
        main_layout.setSpacing(20)

        try:
            # Indicateur de sauvegarde à gauche
            self.save_status_label = QLabel("💾 Aucun projet")
            self.save_status_label.setObjectName("saveStatusLabel")
            main_layout.addWidget(self.save_status_label)

            main_layout.addStretch()

            # Indicateurs de progression des modules au centre
            modules = [
                ("DIMCON", "📐 DIMCON"),
                ("GNSS", "🛰️ GNSS"),
                ("OBSERVATION", "📊 Observation"),
                ("QC", "✅ Qualité")
            ]
            
            for key, tooltip in modules:
                try:
                    indicator = QPushButton(key)
                    indicator.setObjectName("moduleIndicator")
                    indicator.setToolTip(tooltip)
                    indicator.setCheckable(True)
                    indicator.clicked.connect(lambda checked, k=key: self.module_indicator_clicked.emit(k))
                    self.module_indicators[key] = indicator
                    main_layout.addWidget(indicator)
                except Exception as e:
                    print(f"❌ Erreur création indicateur {key}: {e}")
                    # Créer un indicateur de secours
                    indicator = QPushButton(f"ERR")
                    indicator.setEnabled(False)
                    self.module_indicators[key] = indicator
                    main_layout.addWidget(indicator)

            main_layout.addStretch()

            # Horodatage à droite
            self.timestamp_label = QLabel(f"Actualisé: --:--:--")
            self.timestamp_label.setObjectName("timestampLabel")
            main_layout.addWidget(self.timestamp_label)
            
            print("✅ Interface StatusBarWidget créée")
            
        except Exception as e:
            print(f"❌ Erreur setup_ui StatusBarWidget: {e}")
            # Créer des widgets de secours
            if not self.save_status_label:
                self.save_status_label = QLabel("Erreur sauvegarde")
                main_layout.addWidget(self.save_status_label)
            if not self.timestamp_label:
                self.timestamp_label = QLabel("Erreur timestamp")
                main_layout.addWidget(self.timestamp_label)

    def setup_fallback_ui(self):
        """Interface de secours en cas d'erreur"""
        try:
            fallback_layout = QHBoxLayout(self)
            
            error_label = QLabel("❌ ERREUR STATUS BAR - Mode de secours")
            error_label.setStyleSheet("color: red; background-color: #2d2d30; padding: 5px;")
            
            # Créer les attributs de base
            self.save_status_label = QLabel("Erreur")
            self.timestamp_label = QLabel("--:--:--")
            
            fallback_layout.addWidget(error_label)
            fallback_layout.addStretch()
            fallback_layout.addWidget(self.save_status_label)
            fallback_layout.addWidget(self.timestamp_label)
            
            print("⚠️ Interface de secours StatusBarWidget activée")
            
        except Exception as e:
            print(f"❌ Erreur critique setup_fallback_ui StatusBarWidget: {e}")

    def apply_styles(self):
        """Applique le style visuel."""
        try:
            self.setStyleSheet("""
                #statusBarWidget {
                    background-color: #2d2d30;
                    border-top: 2px solid #0d7377;
                }
                QLabel {
                    color: #d4d4d4;
                    font-size: 10px;
                    font-weight: bold;
                }
                #saveStatusLabel {
                    color: #888888;
                }
                #moduleIndicator {
                    background-color: #555558; /* Gris par défaut */
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 8px;
                    padding: 5px 15px;
                    font-weight: bold;
                    font-size: 10px;
                    min-width: 80px;
                }
                #moduleIndicator:hover {
                    border: 1px solid #14a085;
                }
                /* Style pour un module en cours */
                #moduleIndicator[in_progress="true"] {
                    background-color: #f39c12; /* Orange */
                }
                /* Style pour un module terminé */
                #moduleIndicator[completed="true"] {
                    background-color: #27ae60; /* Vert */
                }
            """)
            print("✅ Styles StatusBarWidget appliqués")
        except Exception as e:
            print(f"❌ Erreur application styles StatusBarWidget: {e}")

    def update_timestamp(self):
        """Met à jour l'heure de la dernière actualisation."""
        try:
            if self.timestamp_label:
                now = datetime.now().strftime("%H:%M:%S")
                self.timestamp_label.setText(f"Actualisé: {now}")
        except Exception as e:
            print(f"❌ Erreur update_timestamp: {e}")

    def show_save_feedback(self, success: bool):
        """Affiche un retour visuel après une tentative de sauvegarde."""
        try:
            if not self.save_status_label:
                return
                
            if success:
                self.save_status_label.setText("💾 Projet sauvegardé !")
                self.save_status_label.setStyleSheet("color: #27ae60;")
            else:
                self.save_status_label.setText("❌ Échec sauvegarde")
                self.save_status_label.setStyleSheet("color: #e74c3c;")
            
            # Revenir à l'état normal après 3 secondes
            QTimer.singleShot(3000, lambda: self.save_status_label.setText("💾 Prêt"))
            if success:
                QTimer.singleShot(3000, lambda: self.save_status_label.setStyleSheet("color: #d4d4d4;"))
                
        except Exception as e:
            print(f"❌ Erreur show_save_feedback: {e}")

    def update_module_progress(self, progress_data: dict):
        """
        Met à jour l'apparence des indicateurs de module.
        """
        try:
            for key, indicator in self.module_indicators.items():
                if not indicator:
                    continue
                    
                progress = progress_data.get(key, 0)
                
                is_completed = (progress >= 100)
                is_in_progress = (0 < progress < 100)
                
                # Utiliser des propriétés dynamiques pour le style
                indicator.setProperty("completed", is_completed)
                indicator.setProperty("in_progress", is_in_progress)
                
                # Rafraîchir le style pour appliquer les changements
                try:
                    indicator.style().unpolish(indicator)
                    indicator.style().polish(indicator)
                except Exception as style_error:
                    print(f"❌ Erreur mise à jour style indicateur {key}: {style_error}")
                    
        except Exception as e:
            print(f"❌ Erreur update_module_progress: {e}")

    def set_project_loaded(self, loaded: bool):
        """Met à jour l'état de la barre lorsque le projet est chargé/déchargé."""
        try:
            if not self.save_status_label:
                return
                
            if loaded:
                self.save_status_label.setText("💾 Prêt")
                self.save_status_label.setStyleSheet("color: #d4d4d4;")
            else:
                self.save_status_label.setText("💾 Aucun projet")
                self.save_status_label.setStyleSheet("color: #888888;")
                self.update_module_progress({}) # Réinitialiser les indicateurs
                
        except Exception as e:
            print(f"❌ Erreur set_project_loaded: {e}")

    def animate_module(self, module_key: str):
        """Anime un indicateur de module pour attirer l'attention."""
        try:
            if module_key not in self.module_indicators:
                return
                
            button = self.module_indicators.get(module_key)
            if not button:
                return
            
            # Créer une animation de couleur (nécessite une approche plus complexe)
            # ou une animation de taille simple.
            try:
                anim = QPropertyAnimation(button, b"geometry")
                current_geom = button.geometry()
                
                anim.setDuration(150)
                anim.setLoopCount(2) # L'animation se jouera 2 fois (aller-retour)
                
                # Animation : rétrécir puis revenir à la normale
                start_rect = current_geom
                end_rect = QRect(current_geom.x() + 5, current_geom.y() + 5, 
                                 current_geom.width() - 10, current_geom.height() - 10)
                
                anim.setStartValue(start_rect)
                anim.setEndValue(end_rect)
                anim.setEasingCurve(QEasingCurve.InOutCubic)
                anim.setDirection(QPropertyAnimation.Forward)
                
                # Animation de retour
                anim_return = QPropertyAnimation(button, b"geometry")
                anim_return.setDuration(150)
                anim_return.setStartValue(end_rect)
                anim_return.setEndValue(start_rect)
                anim_return.setEasingCurve(QEasingCurve.InOutCubic)

                # Enchaîner les animations
                anim.finished.connect(anim_return.start)
                anim.start()
                
            except Exception as anim_error:
                print(f"❌ Erreur animation {module_key}: {anim_error}")
                
        except Exception as e:
            print(f"❌ Erreur animate_module: {e}")
    
    def show_module_completed(self, module_name):
        """Affiche une notification visuelle pour un module terminé"""
        try:
            self.animate_module(module_name)
            # log désactivé pour réduire le bruit
        except Exception as e:
            print(f"❌ Erreur show_module_completed: {e}")


# --- Test du widget si exécuté directement ---
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    widget = StatusBarWidget()
    widget.setWindowTitle("Test StatusBarWidget")
    
    # Simuler le chargement d'un projet
    widget.set_project_loaded(True)
    
    # Simuler une mise à jour de progression
    test_progress = {"DIMCON": 100, "GNSS": 50, "OBSERVATION": 0, "QC": 75}
    widget.update_module_progress(test_progress)
    
    # Simuler une sauvegarde réussie
    widget.show_save_feedback(True)
    
    # Tester l'animation
    if "GNSS" in widget.module_indicators:
        widget.module_indicators["GNSS"].clicked.connect(lambda: widget.animate_module("GNSS"))
    
    widget.show()
    
    sys.exit(app.exec_())