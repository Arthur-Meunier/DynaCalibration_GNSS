# app/gui/menu_vertical.py - Menu vertical avec barres de progression GNSS intégrées

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QSizePolicy, QSpacerItem, QProgressBar, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QIcon, QPainter, QLinearGradient, QColor, QBrush

class ModernMenuButton(QPushButton):
    """Bouton de menu moderne avec animations et effets visuels"""
    
    def __init__(self, text, icon, page_index, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.icon_text = icon
        self.is_active = False
        
        # Configuration du bouton
        self.setFixedHeight(60)
        self.setCheckable(True)
        self.setText(f"  {icon}  {text}")
        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        
        # Style et comportement
        self.setup_style()
        self.setup_animations()
        
    def setup_style(self):
        """Configure le style moderne du bouton"""
        self.setStyleSheet("""
            ModernMenuButton {
                text-align: left;
                padding-left: 20px;
                border: none;
                border-radius: 8px;
                background-color: transparent;
                color: #b0b0b0;
                font-weight: bold;
                margin: 2px 8px;
            }
            
            ModernMenuButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border-left: 4px solid #007acc;
            }
            
            ModernMenuButton:checked {
                background-color: #007acc;
                color: #ffffff;
                border-left: 4px solid #005a9e;
            }
            
            ModernMenuButton:pressed {
                background-color: #005a9e;
            }
        """)
    
    def setup_animations(self):
        """Configure les animations du bouton"""
        try:
            # Animation de géométrie pour l'effet hover
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(150)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
        except Exception as e:
            print(f"[WARNING] Animation non disponible: {e}")
            self.animation = None
    
    def set_active(self, active):
        """Active ou désactive le bouton"""
        self.is_active = active
        self.setChecked(active)
        
        if active:
            # Effet visuel pour le bouton actif
            self.setStyleSheet(self.styleSheet() + """
                ModernMenuButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #007acc, stop:1 #005a9e);
                    color: #ffffff;
                    border-left: 4px solid #00ff88;
                }
            """)
    
    def enterEvent(self, event):
        """Effet au survol"""
        super().enterEvent(event)
        if self.animation and not self.is_active:
            # Petit effet de décalage
            current_rect = self.geometry()
            target_rect = QRect(current_rect.x() + 5, current_rect.y(), 
                                current_rect.width() - 5, current_rect.height())
            
            self.animation.setStartValue(current_rect)
            self.animation.setEndValue(target_rect)
            self.animation.start()
    
    def leaveEvent(self, event):
        """Effet à la sortie du survol"""
        super().leaveEvent(event)
        if self.animation and not self.is_active:
            # Retour à la position normale
            current_rect = self.geometry()
            original_rect = QRect(current_rect.x() - 5, current_rect.y(), 
                                    current_rect.width() + 5, current_rect.height())
            
            self.animation.setStartValue(current_rect)
            self.animation.setEndValue(original_rect)
            self.animation.start()


class GNSSProgressWidget(QWidget):
    """Widget de progression GNSS intégré au menu vertical"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("gnssProgressWidget")
        
        # État interne
        self.is_processing = False
        self.current_phase = None
        
        self.setup_ui()
        self.apply_styles()
        
        # Masquer par défaut
        self.setVisible(False)
        
        print("✅ GNSSProgressWidget initialisé")
    
    def setup_ui(self):
        """Configure l'interface du widget de progression"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # === TITRE SECTION ===
        self.title_label = QLabel("🛰️ TRAITEMENT GNSS")
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #007acc; margin-bottom: 5px;")
        layout.addWidget(self.title_label)
        
        # === BARRE SP3/CLK ===
        self.create_sp3_progress_section(layout)
        
        # === BARRE BASELINE 1 ===
        self.create_baseline_progress_section(layout, "baseline1", "📊 Baseline 1", "#e67e22")
        
        # === BARRE BASELINE 2 ===
        self.create_baseline_progress_section(layout, "baseline2", "📊 Baseline 2", "#9b59b6")
        
        # === STATUT GLOBAL ===
        self.global_status_label = QLabel("En attente...")
        self.global_status_label.setFont(QFont("Segoe UI", 8))
        self.global_status_label.setAlignment(Qt.AlignCenter)
        self.global_status_label.setStyleSheet("color: #888; margin-top: 5px;")
        layout.addWidget(self.global_status_label)
    
    def create_sp3_progress_section(self, layout):
        """Crée la section de progression SP3/CLK"""
        # Conteneur SP3
        self.sp3_container = QFrame()
        self.sp3_container.setObjectName("sp3Container")
        self.sp3_container.setVisible(False)
        
        sp3_layout = QVBoxLayout(self.sp3_container)
        sp3_layout.setContentsMargins(5, 3, 5, 3)
        sp3_layout.setSpacing(2)
        
        # Label SP3
        self.sp3_label = QLabel("📡 Téléchargement SP3/CLK")
        self.sp3_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.sp3_label.setStyleSheet("color: #3498db;")
        
        # Barre de progression SP3
        self.sp3_progress = QProgressBar()
        self.sp3_progress.setRange(0, 100)
        self.sp3_progress.setFixedHeight(8)
        self.sp3_progress.setTextVisible(False)
        
        # Message détaillé SP3
        self.sp3_detail = QLabel("En attente...")
        self.sp3_detail.setFont(QFont("Segoe UI", 7))
        self.sp3_detail.setStyleSheet("color: #bbb;")
        self.sp3_detail.setWordWrap(True)
        
        sp3_layout.addWidget(self.sp3_label)
        sp3_layout.addWidget(self.sp3_progress)
        sp3_layout.addWidget(self.sp3_detail)
        
        layout.addWidget(self.sp3_container)
    
    def create_baseline_progress_section(self, layout, baseline_id, title, color):
        """Crée une section de progression pour une baseline"""
        # Conteneur baseline
        container = QFrame()
        container.setObjectName(f"{baseline_id}Container")
        container.setVisible(False)
        
        baseline_layout = QVBoxLayout(container)
        baseline_layout.setContentsMargins(5, 3, 5, 3)
        baseline_layout.setSpacing(2)
        
        # Label baseline
        label = QLabel(title)
        label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        label.setStyleSheet(f"color: {color};")
        
        # Barre de progression baseline
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setFixedHeight(8)
        progress.setTextVisible(False)
        
        # Layout horizontal pour infos détaillées
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Époque actuelle
        epoch_label = QLabel("Époque: 0/0")
        epoch_label.setFont(QFont("Segoe UI", 7))
        epoch_label.setStyleSheet("color: #bbb;")
        
        # Qualité actuelle
        quality_label = QLabel("Q=?")
        quality_label.setFont(QFont("Segoe UI", 7, QFont.Bold))
        quality_label.setStyleSheet("color: #ffc107;")
        
        info_layout.addWidget(epoch_label)
        info_layout.addStretch()
        info_layout.addWidget(quality_label)
        
        baseline_layout.addWidget(label)
        baseline_layout.addWidget(progress)
        baseline_layout.addLayout(info_layout)
        
        # Stocker les références
        setattr(self, f"{baseline_id}_container", container)
        setattr(self, f"{baseline_id}_label", label)
        setattr(self, f"{baseline_id}_progress", progress)
        setattr(self, f"{baseline_id}_epoch", epoch_label)
        setattr(self, f"{baseline_id}_quality", quality_label)
        
        layout.addWidget(container)
    
    def apply_styles(self):
        """Applique les styles au widget de progression"""
        self.setStyleSheet("""
            QWidget#gnssProgressWidget {
                background-color: rgba(0, 122, 204, 0.1);
                border-radius: 8px;
                border: 1px solid rgba(0, 122, 204, 0.3);
                margin: 5px;
            }
            
            QFrame#sp3Container, QFrame#baseline1Container, QFrame#baseline2Container {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                border: 1px solid #444;
                margin: 2px 0px;
            }
            
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #333;
                text-align: center;
            }
            
            QProgressBar::chunk {
                border-radius: 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007acc, stop:1 #00ff88);
            }
            
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
    
    # === MÉTHODES DE CONTRÔLE WORKFLOW ===
    
    def start_gnss_processing(self):
        """Démarre l'affichage du traitement GNSS"""
        self.is_processing = True
        self.setVisible(True)
        self.global_status_label.setText("🚀 Traitement GNSS démarré")
        print("📊 GNSSProgressWidget: Traitement démarré")
    
    def stop_gnss_processing(self):
        """Arrête l'affichage et masque le widget"""
        self.is_processing = False
        
        # Masquer toutes les sections
        self.sp3_container.setVisible(False)
        self.baseline1_container.setVisible(False)
        self.baseline2_container.setVisible(False)
        
        # Reset des barres
        self.sp3_progress.setValue(0)
        self.baseline1_progress.setValue(0)
        self.baseline2_progress.setValue(0)
        
        # Masquer le widget avec délai
        QTimer.singleShot(3000, lambda: self.setVisible(False))
        
        print("📊 GNSSProgressWidget: Traitement terminé")
    
    # === MÉTHODES DE MISE À JOUR SP3 ===
    
    def show_sp3_phase(self):
        """Affiche la phase SP3/CLK"""
        self.current_phase = "sp3"
        self.sp3_container.setVisible(True)
        self.sp3_progress.setValue(0)
        self.sp3_detail.setText("Initialisation téléchargement...")
        self.global_status_label.setText("📡 Téléchargement SP3/CLK")
    
    def update_sp3_progress(self, percentage, message):
        """Met à jour la progression SP3"""
        if not self.is_processing:
            return
        
        # Protection contre les mises à jour trop fréquentes
        if hasattr(self, '_last_sp3_update') and self._last_sp3_update == (percentage, message):
            return
        self._last_sp3_update = (percentage, message)
        
        self.sp3_progress.setValue(percentage)
        self.sp3_detail.setText(message)
        
        # Couleur de la barre selon progression
        if percentage < 30:
            color = "#e74c3c"  # Rouge
        elif percentage < 70:
            color = "#f39c12"  # Orange
        else:
            color = "#27ae60"  # Vert
        
        self.sp3_progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
    
    def complete_sp3_phase(self, success=True):
        """Termine la phase SP3"""
        if success:
            self.sp3_progress.setValue(100)
            self.sp3_detail.setText("✅ Téléchargement terminé")
            self.sp3_label.setText("📡 SP3/CLK - Terminé")
        else:
            self.sp3_detail.setText("❌ Échec téléchargement")
            self.sp3_label.setText("📡 SP3/CLK - Échec")
        
        # Masquer après délai
        QTimer.singleShot(2000, lambda: self.sp3_container.setVisible(False))
    
    # === MÉTHODES DE MISE À JOUR BASELINES ===
    
    def show_baseline_phase(self, baseline_name):
        """Affiche la phase de calcul d'une baseline"""
        baseline_id = "baseline1" if "1" in baseline_name else "baseline2"
        self.current_phase = baseline_id
        
        container = getattr(self, f"{baseline_id}_container")
        progress = getattr(self, f"{baseline_id}_progress")
        epoch_label = getattr(self, f"{baseline_id}_epoch")
        quality_label = getattr(self, f"{baseline_id}_quality")
        
        container.setVisible(True)
        progress.setValue(0)
        epoch_label.setText("Époque: 0/0")
        quality_label.setText("Q=?")
        quality_label.setStyleSheet("color: #ffc107;")
        
        self.global_status_label.setText(f"📊 Calcul {baseline_name}")
    
    def update_baseline_progress(self, baseline_name, percentage, status):
        """Met à jour la progression d'une baseline"""
        if not self.is_processing:
            return
        
        # Protection contre les mises à jour trop fréquentes
        update_key = (baseline_name, percentage, status)
        if hasattr(self, '_last_baseline_update') and self._last_baseline_update == update_key:
            return
        self._last_baseline_update = update_key
        
        # Gestion dynamique des baselines
        # Déterminer quelle baseline utiliser selon le nom
        if "Port" in baseline_name and "Bow" in baseline_name:
            baseline_id = "baseline1"
        elif "Port" in baseline_name and "Stbd" in baseline_name:
            baseline_id = "baseline2"
        elif "Bow" in baseline_name and "Stbd" in baseline_name:
            baseline_id = "baseline2"  # Utiliser baseline2 pour la deuxième paire
        else:
            # Fallback : utiliser baseline1 par défaut
            baseline_id = "baseline1"
        
        # Vérifier que la baseline existe
        if not hasattr(self, f"{baseline_id}_progress"):
            print(f"⚠️ Baseline {baseline_id} non trouvée pour {baseline_name}")
            return
        
        progress = getattr(self, f"{baseline_id}_progress")
        epoch_label = getattr(self, f"{baseline_id}_epoch")
        quality_label = getattr(self, f"{baseline_id}_quality")
        
        # Mise à jour barre de progression
        progress.setValue(percentage)
        
        # Extraction époque et qualité du status
        try:
            if "Époque" in status:
                parts = status.split(" - ")
                epoch_info = parts[0] if parts else status
                quality_info = parts[1] if len(parts) > 1 else "Q=?"
                
                epoch_label.setText(epoch_info)
                quality_label.setText(quality_info)
                
                # Couleur selon qualité
                if "Q=1" in quality_info:
                    quality_label.setStyleSheet("color: #27ae60; font-weight: bold;")  # Vert
                elif "Q=2" in quality_info:
                    quality_label.setStyleSheet("color: #f39c12; font-weight: bold;")  # Orange
                else:
                    quality_label.setStyleSheet("color: #e74c3c; font-weight: bold;")  # Rouge
            else:
                epoch_label.setText(f"Époque: {percentage}%")
                quality_label.setText(status)
        except Exception as e:
            epoch_label.setText(f"Époque: {percentage}%")
            quality_label.setText("Q=?")
    
    def complete_baseline_phase(self, baseline_name, results=None):
        """Termine la phase d'une baseline"""
        # Gestion dynamique des baselines
        if "Port" in baseline_name and "Bow" in baseline_name:
            baseline_id = "baseline1"
        elif "Port" in baseline_name and "Stbd" in baseline_name:
            baseline_id = "baseline2"
        elif "Bow" in baseline_name and "Stbd" in baseline_name:
            baseline_id = "baseline2"
        else:
            baseline_id = "baseline1"
        
        container = getattr(self, f"{baseline_id}_container")
        progress = getattr(self, f"{baseline_id}_progress")
        label = getattr(self, f"{baseline_id}_label")
        epoch_label = getattr(self, f"{baseline_id}_epoch")
        quality_label = getattr(self, f"{baseline_id}_quality")
        
        # Finaliser l'affichage
        progress.setValue(100)
        
        if results:
            length = results.get('length_m', 0)
            q1_percent = results.get('quality_stats', {}).get('q1_percent', 0)
            
            label.setText(f"📊 {baseline_name} - {length:.3f}m")
            epoch_label.setText(f"Terminé - Q1: {q1_percent:.1f}%")
            quality_label.setText("✅")
            quality_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            label.setText(f"📊 {baseline_name} - Terminé")
            epoch_label.setText("Calcul terminé")
            quality_label.setText("✅")
        
        # Masquer après délai si pas de baseline suivante
        if baseline_id == "baseline2":
            QTimer.singleShot(3000, lambda: container.setVisible(False))
    
    def complete_all_processing(self, final_results=None):
        """Termine tout le traitement GNSS"""
        self.global_status_label.setText("🎉 Traitement GNSS terminé")
        
        if final_results:
            num_baselines = len(final_results)
            self.global_status_label.setText(f"🎉 {num_baselines} baselines calculées")
        
        # Arrêter le traitement après affichage des résultats
        QTimer.singleShot(5000, self.stop_gnss_processing)


class VerticalMenu(QWidget):
    """Menu vertical moderne avec barres de progression GNSS intégrées"""
    
    # Signal émis lors de la sélection d'une page
    page_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("verticalMenu")
        self.current_page = 0
        self.menu_buttons = []
        
        # Widget de progression GNSS
        self.gnss_progress = None
        
        # Configuration du menu
        self.setup_ui()
        self.setup_connections()
        
        print("✓ Menu vertical moderne avec GNSS initialisé")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur du menu"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === EN-TÊTE DU MENU ===
        self.create_header(main_layout)
        
        # === BOUTONS DE NAVIGATION ===
        self.create_navigation_buttons(main_layout)
        
        # === BARRES DE PROGRESSION GNSS ===
        self.create_gnss_progress_section(main_layout)
        
        # === SÉPARATEUR ===
        self.create_separator(main_layout)

        # === ESPACEUR FLEXIBLE ===
        main_layout.addStretch()
        
        # === PIED DU MENU ===
        self.create_footer(main_layout)
        
        # Appliquer le style moderne
        self.apply_modern_style()
    
    def create_header(self, layout):
        """Crée l'en-tête du menu avec logo et titre"""
        try:
            header_frame = QFrame()
            header_frame.setObjectName("menuHeader")
            header_frame.setFixedHeight(100)
            
            header_layout = QVBoxLayout(header_frame)
            header_layout.setContentsMargins(15, 15, 15, 15)
            header_layout.setSpacing(5)
            
            # Logo/Icône principal
            logo_label = QLabel("🚢")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setFont(QFont("Segoe UI", 32))
            logo_label.setStyleSheet("color: #007acc;")
            
            # Titre de l'application
            title_label = QLabel("CALIBRATION\nGNSS")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            title_label.setStyleSheet("color: #ffffff; line-height: 1.2;")
            
            header_layout.addWidget(logo_label)
            header_layout.addWidget(title_label)
            
            layout.addWidget(header_frame)
            
        except Exception as e:
            print(f"[WARNING] Erreur création header menu: {e}")
            # Header de secours
            fallback_header = QLabel("🚢 CALIBRATION GNSS")
            fallback_header.setAlignment(Qt.AlignCenter)
            fallback_header.setStyleSheet("color: white; font-weight: bold; padding: 20px;")
            layout.addWidget(fallback_header)
    
    def create_navigation_buttons(self, layout):
        """Crée les boutons de navigation principaux"""
        nav_frame = QFrame()
        nav_frame.setObjectName("navigationFrame")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 10, 0, 10)
        nav_layout.setSpacing(5)
        
        # Configuration des pages
        pages_config = [
            ("Accueil", "🏠", 0, "Tableau de bord principal"),
            ("DIMCON", "📐", 1, "Configuration des dimensions"),
            ("GNSS", "🛰️", 2, "Paramètres de positionnement"),
            ("Observations", "📊", 3, "Gestion des capteurs")
        ]
        
        # Créer les boutons
        for name, icon, page_idx, tooltip in pages_config:
            try:
                button = ModernMenuButton(name, icon, page_idx, self)
                button.setToolTip(tooltip)
                button.clicked.connect(lambda checked, idx=page_idx: self.select_page(idx))
                
                nav_layout.addWidget(button)
                self.menu_buttons.append(button)
                
            except Exception as e:
                print(f"[WARNING] Erreur création bouton {name}: {e}")
        
        # Sélectionner la page d'accueil par défaut
        if self.menu_buttons:
            self.menu_buttons[0].set_active(True)
        
        layout.addWidget(nav_frame)
    
    def create_gnss_progress_section(self, layout):
        """Crée la section des barres de progression GNSS"""
        try:
            # Créer le widget de progression GNSS
            self.gnss_progress = GNSSProgressWidget(self)
            layout.addWidget(self.gnss_progress)
            
            print("✅ Section progression GNSS ajoutée au menu")
            
        except Exception as e:
            print(f"[WARNING] Erreur création section GNSS: {e}")
    
    def create_separator(self, layout):
        """Crée un séparateur visuel"""
        try:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("""
                QFrame {
                    color: #404040;
                    background-color: #404040;
                    height: 1px;
                    margin: 10px 20px;
                }
            """)
            layout.addWidget(separator)
        except Exception as e:
            print(f"[WARNING] Erreur création séparateur: {e}")
    
    def create_footer(self, layout):
        """Crée le pied du menu avec informations de version"""
        try:
            footer_frame = QFrame()
            footer_frame.setObjectName("menuFooter")
            footer_frame.setFixedHeight(50)
            
            footer_layout = QVBoxLayout(footer_frame)
            footer_layout.setContentsMargins(15, 10, 15, 10)
            footer_layout.setSpacing(2)
            
            # Version de l'application
            version_label = QLabel("Version 2.0")
            version_label.setAlignment(Qt.AlignCenter)
            version_label.setFont(QFont("Segoe UI", 8))
            version_label.setStyleSheet("color: #666666;")
            
            # Copyright
            copyright_label = QLabel("© 2025 Marine Navigation")
            copyright_label.setAlignment(Qt.AlignCenter)
            copyright_label.setFont(QFont("Segoe UI", 7))
            copyright_label.setStyleSheet("color: #555555;")
            
            footer_layout.addWidget(version_label)
            footer_layout.addWidget(copyright_label)
            
            layout.addWidget(footer_frame)
            
        except Exception as e:
            print(f"[WARNING] Erreur création footer: {e}")
    
    def setup_connections(self):
        """Configure les connexions entre les composants"""
        try:
            # Connecter le signal de sélection de page
            self.page_selected.connect(self.on_page_selected)
            
        except Exception as e:
            print(f"[WARNING] Erreur setup connexions menu: {e}")
    
    def select_page(self, page_index):
        """Sélectionne une page et met à jour l'interface"""
        try:
            # Mettre à jour l'état des boutons
            for i, button in enumerate(self.menu_buttons):
                button.set_active(i == page_index)
            
            # Émettre le signal
            self.current_page = page_index
            self.page_selected.emit(page_index)
            
            print(f"✓ Page {page_index} sélectionnée")
            
        except Exception as e:
            print(f"[WARNING] Erreur sélection page {page_index}: {e}")
    
    def on_page_selected(self, page_index):
        """Gestionnaire de sélection de page"""
        # Connecter au QStackedWidget parent si disponible
        try:
            parent_window = self.parent()
            if parent_window and hasattr(parent_window, 'content_area'):
                parent_window.content_area.setCurrentIndex(page_index)
                print(f"✓ Navigation vers page {page_index}")
        except Exception as e:
            print(f"[WARNING] Erreur navigation: {e}")
    
    # === MÉTHODES DE CONNEXION AVEC LA PAGE GNSS ===
    
    def connect_gnss_signals(self, gnss_widget):
        """Connecte les signaux de la page GNSS au menu vertical"""
        if not self.gnss_progress:
            print("[WARNING] GNSSProgressWidget non disponible")
            return
        
        try:
            # Connecter les signaux SP3
            gnss_widget.sp3_progress_updated.connect(self.on_gnss_sp3_progress)
            
            # Connecter les signaux baseline
            gnss_widget.baseline_progress_updated.connect(self.on_gnss_baseline_progress)
            
            # Connecter la fin du traitement
            gnss_widget.processing_completed.connect(self.on_gnss_completed)
            
            print("✅ Signaux GNSS connectés au menu vertical")
            
        except Exception as e:
            print(f"[WARNING] Erreur connexion signaux GNSS: {e}")
    
    def on_gnss_sp3_progress(self, percentage, message):
        """Gère la progression SP3 depuis la page GNSS"""
        if self.gnss_progress:
            if percentage == 0:  # Démarrage SP3
                self.gnss_progress.start_gnss_processing()
                self.gnss_progress.show_sp3_phase()
            
            self.gnss_progress.update_sp3_progress(percentage, message)
            
            if percentage >= 100:  # Fin SP3
                self.gnss_progress.complete_sp3_phase(True)
    
    def on_gnss_baseline_progress(self, baseline_name, percentage, status):
        """Gère la progression baseline depuis la page GNSS"""
        if self.gnss_progress:
            if percentage == 0:  # Démarrage baseline
                if not self.gnss_progress.is_processing:
                    self.gnss_progress.start_gnss_processing()
                
                self.gnss_progress.show_baseline_phase(baseline_name)
            
            self.gnss_progress.update_baseline_progress(baseline_name, percentage, status)
            
            if percentage >= 100:  # Fin baseline (sera complété par on_gnss_completed)
                pass
    
    def on_gnss_completed(self, results):
        """Gère la fin du traitement GNSS complet"""
        if self.gnss_progress:
            # Compléter les baselines avec résultats
            if 'baseline_1' in results:
                self.gnss_progress.complete_baseline_phase("Baseline 1", results['baseline_1'])
            
            if 'baseline_2' in results:
                self.gnss_progress.complete_baseline_phase("Baseline 2", results['baseline_2'])
            
            # Compléter tout le traitement  
            self.gnss_progress.complete_all_processing(results)
    
    def apply_modern_style(self):
        """Applique le style moderne au menu avec support GNSS"""
        try:
            self.setStyleSheet("""
                /* === MENU PRINCIPAL === */
                QWidget#verticalMenu {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2c3e50, stop:1 #34495e);
                    border-right: 3px solid #007acc;
                    min-width: 220px;
                    max-width: 280px;
                }
                
                /* === EN-TÊTE === */
                QFrame#menuHeader {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #34495e, stop:1 #2c3e50);
                    border-bottom: 2px solid #007acc;
                    border-radius: 0px;
                }
                
                /* === FRAME DE NAVIGATION === */
                QFrame#navigationFrame {
                    background-color: transparent;
                    padding: 5px;
                }
                
                /* === SECTION PROGRESSION GNSS === */
                QWidget#gnssProgressWidget {
                    background-color: rgba(0, 122, 204, 0.1);
                    border-radius: 8px;
                    border: 1px solid rgba(0, 122, 204, 0.3);
                    margin: 5px;
                }
                
                /* === PIED DU MENU === */
                QFrame#menuFooter {
                    background-color: rgba(0, 0, 0, 0.3);
                    border-top: 1px solid #555555;
                }
                
                /* === LABELS === */
                QLabel {
                    background-color: transparent;
                    border: none;
                }
                
                /* === EFFETS DE TRANSPARENCE === */
                QWidget#verticalMenu:hover {
                    border-right: 3px solid #00ff88;
                }
            """)
            
        except Exception as e:
            print(f"[WARNING] Erreur application style menu: {e}")
    
    def paintEvent(self, event):
        """Dessine des effets visuels supplémentaires"""
        # Utiliser QTimer.singleShot pour éviter les blocages
        QTimer.singleShot(0, self._paint_async)
    
    def _paint_async(self):
        """Peinture asynchrone pour éviter les blocages"""
        try:
            # Appel simple du paintEvent parent
            super().paintEvent(None)
        except Exception as e:
            # Ignorer les erreurs de peinture pour éviter les boucles
            pass
    
    def sizeHint(self):
        """Taille suggérée pour le menu"""
        return self.minimumSize()
    
    def minimumSizeHint(self):
        """Taille minimum pour le menu"""
        return self.minimumSize()


# === FONCTION D'UTILITÉ ===

def create_vertical_menu(parent=None):
    """Crée un menu vertical de façon sécurisée"""
    try:
        return VerticalMenu(parent)
    except Exception as e:
        print(f"[ERROR] Erreur création menu vertical: {e}")
        
        # Menu de secours très simple
        from PyQt5.QtWidgets import QListWidget, QListWidgetItem
        
        fallback_menu = QListWidget(parent)
        fallback_menu.setObjectName("verticalMenu")
        
        # Ajouter des éléments de base
        items = ["🏠 Accueil", "📐 DIMCON", "🛰️ GNSS", "📊 Observations"]
        for item_text in items:
            item = QListWidgetItem(item_text)
            fallback_menu.addItem(item)
        
        fallback_menu.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border-right: 3px solid #007acc;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #007acc;
            }
        """)
        
        print("[FALLBACK] Menu vertical de secours créé")
        return fallback_menu


# === TEST AUTONOME ===
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from PyQt5.QtCore import QTimer
    import sys
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Test Menu Vertical avec GNSS")
            self.setGeometry(100, 100, 300, 800)
            
            # Créer le menu
            self.menu = VerticalMenu(self)
            self.setCentralWidget(self.menu)
            
            # Test des barres de progression
            self.test_gnss_progress()
        
        def test_gnss_progress(self):
            """Test des barres de progression GNSS"""
            if not self.menu.gnss_progress:
                print("❌ Pas de widget de progression GNSS")
                return
            
            print("🧪 Test des barres de progression GNSS...")
            
            # Simuler workflow GNSS
            def test_sp3():
                self.menu.gnss_progress.start_gnss_processing()
                self.menu.gnss_progress.show_sp3_phase()
                
                # Progression SP3
                for i in range(0, 101, 20):
                    QTimer.singleShot(i * 50, lambda p=i: 
                        self.menu.gnss_progress.update_sp3_progress(p, f"Téléchargement {p}%"))
                
                # Fin SP3, démarrage Baseline 1
                QTimer.singleShot(6000, test_baseline1)
            
            def test_baseline1():
                self.menu.gnss_progress.complete_sp3_phase(True)
                QTimer.singleShot(1000, lambda: self.menu.gnss_progress.show_baseline_phase("Baseline 1"))
                
                # Progression Baseline 1
                for i in range(0, 101, 10):
                    quality = "Q=1" if i > 50 else "Q=2" if i > 20 else "Q=5"
                    QTimer.singleShot(i * 30 + 7000, lambda p=i, q=quality: 
                        self.menu.gnss_progress.update_baseline_progress("Baseline 1", p, f"Époque {p}/100 - {q}"))
                
                # Fin Baseline 1, démarrage Baseline 2
                QTimer.singleShot(10000, test_baseline2)
            
            def test_baseline2():
                results1 = {'length_m': 45.678, 'quality_stats': {'q1_percent': 78.5}}
                self.menu.gnss_progress.complete_baseline_phase("Baseline 1", results1)
                QTimer.singleShot(1000, lambda: self.menu.gnss_progress.show_baseline_phase("Baseline 2"))
                
                # Progression Baseline 2
                for i in range(0, 101, 15):
                    quality = "Q=1" if i > 30 else "Q=2"
                    QTimer.singleShot(i * 25 + 11000, lambda p=i, q=quality: 
                        self.menu.gnss_progress.update_baseline_progress("Baseline 2", p, f"Époque {p}/100 - {q}"))
                
                # Fin complète
                QTimer.singleShot(13000, lambda: test_complete(results1))
            
            def test_complete(results1):
                results2 = {'length_m': 38.234, 'quality_stats': {'q1_percent': 85.2}}
                final_results = {'baseline_1': results1, 'baseline_2': results2}
                
                self.menu.gnss_progress.complete_baseline_phase("Baseline 2", results2)
                self.menu.gnss_progress.complete_all_processing(final_results)
            
            # Démarrer le test
            QTimer.singleShot(2000, test_sp3)
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("🧪 Test menu vertical avec barres GNSS démarré")
    print("   - Observez les barres de progression")
    print("   - Test automatique sur 15 secondes")
    
    sys.exit(app.exec_())