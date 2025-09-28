# src/app/main.py - Application principale avec intégration GNSS complète

import sys
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QStackedWidget, QSplitter, QMessageBox, QMenuBar, QMenu, QAction,
    QStatusBar, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont


# --- Configuration du Path ---
try:
    current_dir = Path(__file__).parent.resolve()
    src_dir = next(p for p in current_dir.parents if p.name == 'src')
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    print(f"✅ Répertoire src trouvé: {src_dir}")
except (StopIteration, FileNotFoundError):
    print("❌ Erreur critique: Impossible de trouver le dossier 'src'.")
    sys.exit(1)

# --- Imports des modules avec diagnostic détaillé ---
print("\n🔍 === DIAGNOSTIC DES IMPORTS ===")

# Gestionnaires de données et de projet
try:
    from core.app_data import ApplicationData
    print("✅ ApplicationData importé")
except ImportError as e:
    print(f"❌ ApplicationData: {e}")
    ApplicationData = None

try:
    from core.project_manager import ProjectManager
    print("✅ ProjectManager importé")
except ImportError as e:
    print(f"❌ ProjectManager: {e}")
    ProjectManager = None

try:
    from core.progress_manager import ProgressManager
    print("✅ ProgressManager importé")
except ImportError as e:
    print(f"❌ ProgressManager: {e}")
    ProgressManager = None

# Menu vertical avec support GNSS
try:
    from app.gui.menu_vertical import VerticalMenu
    print("✅ VerticalMenu importé (version avec barres GNSS)")
except ImportError as e:
    print(f"❌ VerticalMenu: {e}")
    VerticalMenu = None

# Page d'accueil
try:
    from app.gui.page_accueil import HomePageWidget
    print("✅ HomePageWidget importé")
except ImportError as e:
    print(f"❌ HomePageWidget: {e}")
    HomePageWidget = None

# Page DIMCON
try:
    from app.gui.page_Dimcon import DimconWidget
    print("✅ DimconWidget importé depuis page_Dimcon")
except ImportError as e:
    print(f"❌ DimconWidget depuis page_Dimcon: {e}")
    try:
        from app.gui.page_dimcon import DimconWidget  # essayer minuscule
        print("✅ DimconWidget importé depuis page_dimcon (minuscule)")
    except ImportError as e2:
        print(f"❌ DimconWidget depuis page_dimcon: {e2}")
        DimconWidget = None

# Page GNSS (version sans barres internes)
try:
    from app.gui.page_GNSS import GnssWidget
    print("✅ GnssWidget importé (version sans barres internes)")
except ImportError as e:
    print(f"❌ GnssWidget: {e}")
    GnssWidget = None

# Page GNSS Post-Calcul
try:
    from app.gui.page_GNSSpostcalc import GNSSPostCalcWidget
    print("✅ GNSSPostCalcWidget importé")
except ImportError as e:
    print(f"❌ GNSSPostCalcWidget: {e}")
    GNSSPostCalcWidget = None

# Widget d'intégration deux lignes de base
try:
    from app.gui.dual_baseline_integration import DualBaselineIntegrationWidget
    print("✅ DualBaselineIntegrationWidget importé")
except ImportError as e:
    print(f"❌ DualBaselineIntegrationWidget: {e}")
    DualBaselineIntegrationWidget = None

# Page Observation
try:
    from app.gui.page_observation import ObservationWidget
    print("✅ ObservationWidget importé")
except ImportError as e:
    print(f"❌ ObservationWidget: {e}")
    ObservationWidget = None

# Log Widget
try:
    from app.gui.log_widget import LogWidget
    print("✅ LogWidget importé")
except ImportError as e:
    print(f"❌ LogWidget: {e}")
    LogWidget = None

print("🔍 === FIN DIAGNOSTIC IMPORTS ===\n")

# Vérification des imports critiques
critical_imports = [ApplicationData, ProjectManager, HomePageWidget]
missing_critical = [name for name, obj in zip(['ApplicationData', 'ProjectManager', 'HomePageWidget'], critical_imports) if obj is None]

if missing_critical:
    print(f"⚠️ ATTENTION: Imports critiques manquants: {missing_critical}")
else:
    print("✅ Tous les imports critiques sont disponibles")


class CalibrationMainWindow(QMainWindow):
    """
    Fenêtre principale de l'application de calibration GNSS.
    """
    
    def __init__(self):
        super().__init__()
        
        # === CONFIGURATION DE BASE ===
        self.setWindowTitle("🚢 Calibration GNSS - Application Complète")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # === GESTIONNAIRES DE DONNÉES ET PROJET ===
        try:
            if ApplicationData:
                self.app_data = ApplicationData()
                print("✅ ApplicationData créé")
            else:
                self.app_data = None
                print("❌ ApplicationData non disponible")
                    
            if ProjectManager:
                # ✅ DÉJÀ PRÉSENT - Vérification que c'est bien fait
                self.project_manager = ProjectManager.instance()
                print("✅ ProjectManager créé")
                
                # ✅ NOUVEAU : Configuration du projet avec app_data si disponible
                if self.app_data and hasattr(self.project_manager, 'set_app_data_reference'):
                    self.project_manager.set_app_data_reference(self.app_data)
                    print("🔗 ProjectManager connecté à ApplicationData")
            else:
                self.project_manager = None
                print("❌ ProjectManager non disponible")
            
            # ✅ NOUVEAU : Création de ProgressManager
            if ProgressManager:
                self.progress_manager = ProgressManager()
                print("✅ ProgressManager créé")
            else:
                self.progress_manager = None
                print("❌ ProgressManager non disponible")
            # === CORRECTION: Initialisation settings plus robuste ===
            try:
                self.settings = QSettings("MarineNavigation", "CalibrationGNSS")
                print(f"✅ Settings créé: {self.settings.organizationName()}")
            except Exception as e:
                print(f"❌ Erreur création settings: {e}")
                from PyQt5.QtCore import QObject
                self.settings = QObject()
                    
        except Exception as e:
            print(f"❌ Erreur initialisation gestionnaires: {e}")
            self.app_data = None
            self.project_manager = None
            self.settings = QSettings("MarineNavigation", "CalibrationGNSS")
                
        # === INTERFACE UTILISATEUR ===
        try:
            self.setup_ui()
            self.create_menus()
            self.create_status_bar()
            self.connect_all_signals()
            self.load_settings()
            
            # ✅ CORRECTION : Connecter les signaux de la page d'accueil APRÈS sa création
            self.connect_homepage_signals()
            
            self.show_welcome_message()
            
            print("✅ Application principale initialisée")
        except Exception as e:
            print(f"❌ Erreur initialisation interface: {e}")
            import traceback
            traceback.print_exc()
        
    def setup_ui(self):
        """Configure l'interface utilisateur principale."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        # ✅ MENU VERTICAL AVEC SUPPORT GNSS
        if VerticalMenu:
            try:
                self.vertical_menu = VerticalMenu()
                self.vertical_menu.setMaximumWidth(280)
                main_splitter.addWidget(self.vertical_menu)
                print("✅ Menu vertical créé avec support GNSS")
            except Exception as e:
                print(f"❌ Erreur création menu vertical: {e}")
                placeholder = QLabel("Menu\nIndisponible")
                placeholder.setMaximumWidth(280)
                main_splitter.addWidget(placeholder)
                self.vertical_menu = None
        else:
            print("❌ VerticalMenu non disponible")
            placeholder = QLabel("Menu\nIndisponible\n\nVerticalMenu\non importé")
            placeholder.setMaximumWidth(280)
            placeholder.setStyleSheet("color: red; background-color: #2d2d30; padding: 20px;")
            main_splitter.addWidget(placeholder)
            self.vertical_menu = None
        
        # Splitter contenu + log
        content_splitter = QSplitter(Qt.Vertical)
        
        # Stack des pages
        self.content_stack = QStackedWidget()
        content_splitter.addWidget(self.content_stack)
        
        # Widget de log
        if LogWidget:
            try:
                self.log_widget = LogWidget()
                self.log_widget.setMaximumHeight(200)
                content_splitter.addWidget(self.log_widget)
                print("✅ Widget de log créé")
            except Exception as e:
                print(f"❌ Erreur création log widget: {e}")
                log_placeholder = QLabel("Log indisponible")
                log_placeholder.setMaximumHeight(200)
                content_splitter.addWidget(log_placeholder)
                self.log_widget = None
        else:
            print("❌ LogWidget non disponible")
            log_placeholder = QLabel("Log indisponible\n\nLogWidget non importé")
            log_placeholder.setMaximumHeight(200)
            log_placeholder.setStyleSheet("color: red; background-color: #2d2d30; padding: 10px;")
            content_splitter.addWidget(log_placeholder)
            self.log_widget = None
        
        content_splitter.setSizes([600, 200])
        main_splitter.addWidget(content_splitter)
        main_splitter.setSizes([280, 1120])
        main_layout.addWidget(main_splitter)
        
        # IMPORTANT: Créer les pages APRÈS le menu vertical
        self.create_pages()
        
        # Rediriger la console vers le widget de log
        if self.log_widget and LogWidget and hasattr(LogWidget, 'redirect_console'):
            LogWidget.redirect_console(self.log_widget)
        
        print("✅ Interface principale configurée avec support GNSS")
    
    def connect_all_signals(self):
        """Connecte TOUS les signaux de l'application avec ProjectManager"""
        try:
            # Navigation - vérifier si les objets existent
            if self.vertical_menu and hasattr(self.vertical_menu, 'page_selected'):
                self.vertical_menu.page_selected.connect(self.navigate_to_page)
            
            if self.home_page and hasattr(self.home_page, 'module_navigation_requested'):
                self.home_page.module_navigation_requested.connect(self.navigate_to_module_by_name)

            # ✅ GESTION DE PROJET COMPLÈTE - NOUVEAUX SIGNAUX
            if self.project_manager:
                print("🔗 Connexion signaux ProjectManager...")
                
                # Signal de projet chargé
                if hasattr(self.project_manager, 'project_loaded'):
                    self.project_manager.project_loaded.connect(self.on_project_loaded)
                    print("  ✅ project_loaded connecté")
                
                # Signal de projet sauvegardé  
                if hasattr(self.project_manager, 'project_saved'):
                    self.project_manager.project_saved.connect(self.on_project_saved)
                    print("  ✅ project_saved connecté")
                
                # ✅ NOUVEAU : Signal workflow step completed
                if hasattr(self.project_manager, 'workflow_step_completed'):
                    self.project_manager.workflow_step_completed.connect(self.on_workflow_step_completed)
                    print("  ✅ workflow_step_completed connecté")
                
                # ✅ NOUVEAU : Signal QC score updated
                if hasattr(self.project_manager, 'qc_score_updated'):
                    self.project_manager.qc_score_updated.connect(self.on_qc_score_updated)
                    print("  ✅ qc_score_updated connecté")
                
                # ✅ NOUVEAU : Signal auto-save triggered
                if hasattr(self.project_manager, 'auto_save_triggered'):
                    self.project_manager.auto_save_triggered.connect(self.on_auto_save_triggered)
                    print("  ✅ auto_save_triggered connecté")
            
            # Données - vérifier si app_data existe
            if self.app_data and hasattr(self.app_data, 'data_changed'):
                self.app_data.data_changed.connect(self.on_data_changed)
            
            # ✅ SIGNAUX PROGRESSMANAGER POUR DASHBOARD
            if self.progress_manager:
                print("🔗 Connexion signaux ProgressManager...")
                if hasattr(self.progress_manager, 'progress_updated'):
                    self.progress_manager.progress_updated.connect(self.on_progress_updated)
                    print("  ✅ progress_updated connecté")
                if hasattr(self.progress_manager, 'module_completed'):
                    self.progress_manager.module_completed.connect(self.on_module_completed)
                    print("  ✅ module_completed connecté")
            
            # ✅ SIGNAUX GNSS POUR LOGGING ET INTÉGRATION
            if hasattr(self, 'gnss_page') and self.gnss_page:
                # Les signaux GNSS sont déjà connectés au menu vertical
                # Mais on peut aussi les écouter ici pour logging/debug
                if hasattr(self.gnss_page, 'processing_completed'):
                    self.gnss_page.processing_completed.connect(self.on_gnss_workflow_completed)
                if hasattr(self.gnss_page, 'sp3_progress_updated'):
                    self.gnss_page.sp3_progress_updated.connect(self.on_gnss_sp3_progress)
                if hasattr(self.gnss_page, 'baseline_progress_updated'):
                    self.gnss_page.baseline_progress_updated.connect(self.on_gnss_baseline_progress)
                print("✅ Signaux GNSS connectés pour logging")
            
            print("✅ Tous les signaux connectés")
            
        except Exception as e:
            print(f"❌ Erreur connexion signaux: {e}")
    
    def connect_homepage_signals(self):
        """Connecte les signaux spécifiques à la page d'accueil APRÈS sa création"""
        try:
            if not self.home_page or not self.project_manager:
                print("⚠️ HomePage ou ProjectManager non disponible pour connexion")
                return
            
            print("🔗 Connexion signaux HomePage...")
            
            # Connexion directe ProjectManager → HomePage
            if hasattr(self.project_manager, 'workflow_step_completed'):
                self.project_manager.workflow_step_completed.connect(self.home_page.on_workflow_step_completed)
                print("  ✅ workflow_step_completed connecté à HomePage")
            
            if hasattr(self.project_manager, 'qc_score_updated'):
                self.project_manager.qc_score_updated.connect(self.home_page.on_qc_score_updated)
                print("  ✅ qc_score_updated connecté à HomePage")
            
            print("✅ Signaux HomePage connectés")
            
        except Exception as e:
            print(f"❌ Erreur connexion signaux HomePage: {e}")
    
    def on_project_saved(self, path: str):
        """Gère la sauvegarde d'un projet"""
        try:
            project_name = Path(path).stem
            # logs désactivés pour sauvegarde
            self.set_status("")
            
            # Mettre à jour le titre de la fenêtre si nécessaire
            if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
                vessel = self.project_manager.current_project.get("metadata", {}).get("vessel", "Projet")
                self.setWindowTitle(f"🚢 Calibration GNSS - [{vessel}] - Sauvegardé")
        except Exception as e:
            print(f"❌ Erreur gestion sauvegarde: {e}")
    
    def on_workflow_step_completed(self, step_name: str, completed: bool):
        """Gère la completion d'une étape du workflow"""
        try:
            status_icon = "✅" if completed else "⏳"
            step_names = {
                "dimcon": "DIMCON",
                "gnss": "GNSS", 
                "observation": "Observation",
                "qc": "Contrôle Qualité"
            }
            
            display_name = step_names.get(step_name, step_name)
            self.set_status(f"{status_icon} {display_name} {'terminé' if completed else 'en cours'}")
            
            print(f"📊 Workflow - {display_name}: {'✅ Terminé' if completed else '⏳ En cours'}")
            
            # Mettre à jour les barres de progression du menu vertical si disponible
            if self.vertical_menu and hasattr(self.vertical_menu, 'update_module_progress'):
                progress = 100 if completed else 50
                self.vertical_menu.update_module_progress(step_name.upper(), progress)
            
            # Déclencher le calcul de progression si ProgressManager est disponible
            if hasattr(self, 'progress_manager') and self.progress_manager and hasattr(self, 'app_data') and self.app_data:
                print(f"🔄 Calcul progression déclenché pour workflow: {step_name}")
                self.progress_manager.calculate_all_progress(self.app_data)
            
            # Mettre à jour le dashboard immédiatement
            if hasattr(self, 'home_page') and self.home_page:
                self.home_page.refresh_dashboard_data()
                
        except Exception as e:
            print(f"❌ Erreur gestion workflow step: {e}")
    
    def on_qc_score_updated(self, score: float):
        """Gère la mise à jour du score QC global"""
        try:
            score_icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            self.set_status(f"{score_icon} Score QC: {score:.1f}%")
            
            print(f"🎯 Score QC global: {score:.1f}%")
            
            # Mettre à jour l'affichage dans le menu vertical ou la page d'accueil
            if hasattr(self, 'home_page') and self.home_page and hasattr(self.home_page, 'update_qc_display'):
                self.home_page.update_qc_display(score)
                
        except Exception as e:
            print(f"❌ Erreur gestion QC score: {e}")
    
    def on_progress_updated(self, module_name: str, progress: float):
        """Gère la mise à jour de progression d'un module depuis ProgressManager"""
        try:
            # Vérifier si la progression a changé avant d'afficher
            if not hasattr(self, '_last_progress'):
                self._last_progress = {}
            
            last_progress = self._last_progress.get(module_name, -1)
            if progress != last_progress:
                # Silencer: ne pas imprimer pour éviter le spam
                self._last_progress[module_name] = progress
            
            # Transmettre à HomePageWidget si disponible
            if hasattr(self, 'home_page') and self.home_page:
                self.home_page.on_progress_updated(module_name, progress)
        except Exception as e:
            print(f"❌ Erreur gestion progression: {e}")
    
    def on_module_completed(self, module_name: str):
        """Gère la completion d'un module depuis ProgressManager"""
        try:
            # Vérifier si le module a déjà été marqué comme terminé
            if not hasattr(self, '_completed_modules'):
                self._completed_modules = set()
            
            if module_name not in self._completed_modules:
                # Silencer: ne pas imprimer pour éviter les doublons
                self._completed_modules.add(module_name)
            
            # Transmettre à HomePageWidget si disponible
            if hasattr(self, 'home_page') and self.home_page:
                self.home_page.on_module_completed(module_name)
        except Exception as e:
            print(f"❌ Erreur gestion completion module: {e}")
    
    def on_auto_save_triggered(self):
        """Gère les auto-sauvegardes"""
        try:
            self.set_status("💾 Auto-sauvegarde...")
            print("🔄 Auto-sauvegarde déclenchée")
            
            # Optionnel: afficher une notification discrète
            # QTimer.singleShot(2000, lambda: self.set_status("Prêt"))
            
        except Exception as e:
            print(f"❌ Erreur gestion auto-save: {e}")
    
    def create_pages(self):
        """Crée et configure toutes les pages de l'application avec intégration GNSS."""
        print("\n🔍 === CRÉATION DES PAGES ===")
        
        # === PAGE D'ACCUEIL ===
        if HomePageWidget:
            try:
                print("📝 Création page d'accueil avec settings...")
                
                if hasattr(self, 'settings') and self.settings is not None:
                    print(f"✅ Settings disponible: {type(self.settings)}")
                    self.home_page = HomePageWidget(app_data=self.app_data, settings=self.settings, progress_manager=self.progress_manager)
                else:
                    print("⚠️ Settings non disponible, création sans settings")
                    self.home_page = HomePageWidget(app_data=self.app_data, settings=None, progress_manager=self.progress_manager)
                
                self.content_stack.addWidget(self.home_page)
                print("✅ Page d'accueil créée")
                
                if hasattr(self.home_page, 'check_widgets_status'):
                    self.home_page.check_widgets_status()
                
            except Exception as e:
                print(f"❌ Erreur page d'accueil: {e}")
                self.home_page = None
        else:
            print("❌ HomePageWidget non disponible")
            self.home_page = None
        
        # === PAGE DIMCON ===
        if DimconWidget:
            try:
                print("📝 Création page DIMCON...")
                self.dimcon_page = DimconWidget(app_data=self.app_data)
                self.content_stack.addWidget(self.dimcon_page)
                print("✅ Page DIMCON créée")
            except Exception as e:
                print(f"❌ Erreur page DIMCON: {e}")
                self.dimcon_page = None
        else:
            print("❌ DimconWidget non disponible")
            self.dimcon_page = None
        
        # === PAGE GNSS AVEC CONNEXION MENU VERTICAL ===
        if GnssWidget:
            try:
                print("📝 Création page GNSS...")
                self.gnss_page = GnssWidget(
                    app_data=self.app_data,
                    project_manager=self.project_manager,
                    parent=self
                )
                
                # ✅ CONNEXION AVEC LE MENU VERTICAL POUR LES BARRES DE PROGRESSION
                if self.vertical_menu and hasattr(self.vertical_menu, 'connect_gnss_signals'):
                    print("🔗 Connexion page GNSS au menu vertical...")
                    try:
                        self.vertical_menu.connect_gnss_signals(self.gnss_page)
                        print("✅ Barres de progression GNSS connectées au menu vertical")
                    except Exception as e:
                        print(f"❌ Erreur connexion barres GNSS: {e}")
                elif self.gnss_page and hasattr(self.gnss_page, 'connect_to_vertical_menu'):
                    print("🔗 Connexion alternative page GNSS au menu vertical...")
                    try:
                        self.gnss_page.connect_to_vertical_menu(self.vertical_menu)
                        print("✅ Connexion alternative réussie")
                    except Exception as e:
                        print(f"❌ Erreur connexion alternative: {e}")
                else:
                    print("⚠️ Menu vertical sans support GNSS ou méthode de connexion manquante")
                
                self.content_stack.addWidget(self.gnss_page)
                print("✅ Page GNSS créée et connectée")
                
            except Exception as e:
                print(f"❌ Erreur page GNSS: {e}")
                print(f"🔍 Type d'erreur: {type(e).__name__}")
                if "PyQt5" in str(e) or "ModuleNotFoundError" in str(e):
                    print("💡 Solution: Installer PyQt5 avec 'pip install PyQt5'")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Erreur GNSS", f"Impossible d'afficher GNSS: {e}")
                self.gnss_page = None
        
        # === PAGE GNSS POST-CALCUL ===
        if GNSSPostCalcWidget:
            try:
                print("📝 Création page GNSS Post-Calcul...")
                self.gnss_postcalc_page = GNSSPostCalcWidget(
                    app_data=self.app_data,
                    project_manager=self.project_manager,
                    parent=self
                )
                
                # Connexion des signaux
                self.gnss_postcalc_page.reset_requested.connect(self.on_gnss_reset_requested)
                self.gnss_postcalc_page.recalculate_requested.connect(self.on_gnss_recalculate_requested)
                
                self.content_stack.addWidget(self.gnss_postcalc_page)
                print("✅ Page GNSS Post-Calcul créée")
                
            except Exception as e:
                print(f"❌ Erreur page GNSS Post-Calcul: {e}")
                self.gnss_postcalc_page = None
        else:
            print("❌ GNSSPostCalcWidget non disponible")
            self.gnss_postcalc_page = None
        
        # === PAGE OBSERVATION ===
        if ObservationWidget:
            try:
                print("📝 Création page Observation...")
                self.observation_page = ObservationWidget()
                if hasattr(self.observation_page, 'set_data_model') and self.app_data:
                    self.observation_page.set_data_model(self.app_data)
                self.content_stack.addWidget(self.observation_page)
                print("✅ Page Observation créée")
            except Exception as e:
                print(f"❌ Erreur page Observation: {e}")
                self.observation_page = None
        else:
            print("❌ ObservationWidget non disponible")
            self.observation_page = None
        
        # === PAGE DEUX LIGNES DE BASE ===
        if DualBaselineIntegrationWidget:
            try:
                print("📝 Création page Deux Lignes de Base...")
                self.dual_baseline_page = DualBaselineIntegrationWidget(
                    project_manager=self.project_manager,
                    progress_manager=self.progress_manager,
                    parent=self
                )
                
                # Connexion des signaux
                self.dual_baseline_page.processing_completed.connect(self.on_dual_baseline_completed)
                self.dual_baseline_page.step_completed.connect(self.on_dual_baseline_step_completed)
                
                self.content_stack.addWidget(self.dual_baseline_page)
                print("✅ Page Deux Lignes de Base créée")
                
            except Exception as e:
                print(f"❌ Erreur page Deux Lignes de Base: {e}")
                self.dual_baseline_page = None
        else:
            print("❌ DualBaselineIntegrationWidget non disponible")
            self.dual_baseline_page = None
        
        # === PAGE QC (PLACEHOLDER) ===
        print("📝 Création page QC (placeholder)...")
        try:
            qc_widget = QWidget()
            qc_layout = QVBoxLayout(qc_widget)
            qc_label = QLabel("🔍 MODULE QUALITÉ\n\nContrôle qualité et validation\n(En développement)")
            qc_label.setAlignment(Qt.AlignCenter)
            qc_label.setStyleSheet("""
                QLabel {
                    font-size: 16px; 
                    color: white; 
                    background-color: #2d2d30; 
                    padding: 40px;
                    border-radius: 8px;
                    border: 2px dashed #555;
                }
            """)
            qc_layout.addWidget(qc_label)
            self.content_stack.addWidget(qc_widget)
            self.qc_page = qc_widget
            print("✅ Page QC créée")
        except Exception as e:
            print(f"❌ Erreur page QC: {e}")
            self.qc_page = None
        
        # === RÉSUMÉ ===
        total_pages = self.content_stack.count()
        print(f"\n📊 {total_pages} pages créées:")
        for i in range(total_pages):
            widget = self.content_stack.widget(i)
            widget_name = type(widget).__name__
            print(f"   • Page {i}: {widget_name}")
        
        # Activer la première page
        if total_pages > 0:
            self.content_stack.setCurrentIndex(0)
            print(f"📍 Page active: {type(self.content_stack.currentWidget()).__name__}")
        
        print("🔍 === FIN CRÉATION PAGES ===\n")
    
    def create_menus(self):
        """Crée la barre de menus."""
        try:
            menubar = self.menuBar()
            
            # Menu Fichier
            file_menu = menubar.addMenu("📁 Fichier")
            new_action = QAction("🆕 Nouveau Projet", self, triggered=self.new_project, shortcut="Ctrl+N")
            open_action = QAction("📂 Ouvrir Projet", self, triggered=self.open_project, shortcut="Ctrl+O")
            save_action = QAction("💾 Sauvegarder", self, triggered=self.save_project, shortcut="Ctrl+S")
            exit_action = QAction("❌ Quitter", self, triggered=self.close, shortcut="Ctrl+Q")
            
            file_menu.addActions([new_action, open_action, save_action])
            file_menu.addSeparator()
            file_menu.addAction(exit_action)
            
            # Menu Outils
            tools_menu = menubar.addMenu("🔧 Outils")
            settings_action = QAction("⚙️ Paramètres", self, shortcut="Ctrl+,")
            gnss_test_action = QAction("🛰️ Test GNSS", self, triggered=self.test_gnss_workflow)
            tools_menu.addAction(settings_action)
            tools_menu.addSeparator()
            tools_menu.addAction(gnss_test_action)
            
            # Menu Aide
            help_menu = menubar.addMenu("❓ Aide")
            about_action = QAction("📖 À propos", self, triggered=self.show_about)
            help_menu.addAction(about_action)
            
            print("✅ Menus créés")
        except Exception as e:
            print(f"❌ Erreur création menus: {e}")

    def create_status_bar(self):
        """Crée la barre d'état."""
        try:
            status_bar = self.statusBar()
            self.status_label = QLabel("Initialisation...")
            status_bar.addWidget(self.status_label)
            print("✅ Barre d'état créée")
        except Exception as e:
            print(f"❌ Erreur création barre d'état: {e}")
            self.status_label = None

    def connect_signals(self):
        """Connecte tous les signaux de l'application."""
        try:
            # Navigation - vérifier si les objets existent
            if self.vertical_menu and hasattr(self.vertical_menu, 'page_selected'):
                self.vertical_menu.page_selected.connect(self.navigate_to_page)
            
            if self.home_page and hasattr(self.home_page, 'module_navigation_requested'):
                self.home_page.module_navigation_requested.connect(self.navigate_to_module_by_name)

            # Gestion de projet - vérifier si le project_manager existe
            if self.project_manager:
                if hasattr(self.project_manager, 'project_loaded'):
                    self.project_manager.project_loaded.connect(self.on_project_loaded)
                if hasattr(self.project_manager, 'project_saved'):
                    self.project_manager.project_saved.connect(
                        lambda path: None
                    )

            # Données - vérifier si app_data existe
            if self.app_data and hasattr(self.app_data, 'data_changed'):
                self.app_data.data_changed.connect(self.on_data_changed)
            
            # ✅ SIGNAUX GNSS POUR LOGGING ET INTÉGRATION
            if hasattr(self, 'gnss_page') and self.gnss_page:
                # Les signaux GNSS sont déjà connectés au menu vertical
                # Mais on peut aussi les écouter ici pour logging/debug
                if hasattr(self.gnss_page, 'processing_completed'):
                    self.gnss_page.processing_completed.connect(self.on_gnss_workflow_completed)
                if hasattr(self.gnss_page, 'sp3_progress_updated'):
                    self.gnss_page.sp3_progress_updated.connect(self.on_gnss_sp3_progress)
                if hasattr(self.gnss_page, 'baseline_progress_updated'):
                    self.gnss_page.baseline_progress_updated.connect(self.on_gnss_baseline_progress)
                print("✅ Signaux GNSS connectés pour logging")
            
            print("✅ Signaux connectés")
        except Exception as e:
            print(f"❌ Erreur connexion signaux: {e}")

    # --- NOUVEAUX GESTIONNAIRES GNSS ---
    
    def on_gnss_workflow_completed(self, results):
        """Gère la fin du workflow GNSS pour logging et intégration"""
        print("🔍 DEBUG: on_gnss_workflow_completed appelé")
        print(f"🔍 DEBUG: Résultats reçus: {results}")
        
        try:
            num_baselines = len([k for k in results.keys() if 'baseline' in k])
            
            self.set_status(f"🛰️ GNSS terminé - {num_baselines} baselines calculées")
            print(f"🎉 Workflow GNSS terminé: {num_baselines} baselines")
            
            # Sauvegarder les résultats dans le projet
            if self.project_manager and hasattr(self.project_manager, 'update_gnss_results'):
                self.project_manager.update_gnss_results(results)
            
            # Mettre à jour app_data si disponible
            if self.app_data and hasattr(self.app_data, 'gnss_results'):
                self.app_data.gnss_results = results
                if hasattr(self.app_data, 'data_changed'):
                    self.app_data.data_changed.emit("gnss")
            
            # ✅ NOUVEAU : Navigation automatique vers la page post-calcul
            print("🛰️ Calculs GNSS terminés - Navigation vers la page post-calcul")
            # Attendre un peu pour que les fichiers soient bien écrits
            QTimer.singleShot(3000, lambda: self.navigate_to_page(3))  # Page post-calcul (index 3)
            self.set_status("🛰️ Calculs terminés - Affichage des statistiques")
            
        except Exception as e:
            print(f"❌ Erreur gestion fin GNSS: {e}")
    
    def on_gnss_sp3_progress(self, percentage, message):
        """Gère la progression SP3 pour logging"""
        print(f"📡 SP3: {percentage}% - {message}")
        if percentage == 0:
            self.set_status("📡 Démarrage téléchargement SP3...")
        elif percentage == 100:
            self.set_status("✅ SP3 téléchargé")
    
    def on_gnss_baseline_progress(self, baseline_name, percentage, status):
        """Gère la progression baseline pour logging"""
        print(f"📊 {baseline_name}: {percentage}% - {status}")
        if percentage == 0:
            self.set_status(f"📊 Démarrage {baseline_name}...")
        elif percentage == 100:
            self.set_status(f"✅ {baseline_name} terminé")
    
    def test_gnss_workflow(self):
        """Fonction de test du workflow GNSS"""
        if hasattr(self, 'gnss_page') and self.gnss_page:
            # Naviguer vers la page GNSS
            self.navigate_to_page(2)  # Index GNSS
            self.set_status("🧪 Test workflow GNSS - Naviguez vers la page GNSS")
            print("🧪 Navigation vers page GNSS pour test")
        else:
            QMessageBox.information(self, "Test GNSS", 
                                  "Page GNSS non disponible pour le test.")
    
    # --- GESTIONNAIRES GNSS POST-CALCUL ---
    
    def on_gnss_reset_requested(self):
        """Gère la demande de réinitialisation des calculs GNSS"""
        try:
            print("🔄 Réinitialisation des calculs GNSS demandée")
            
            # Supprimer les fichiers de résultats
            if self.project_manager and self.project_manager.current_project:
                project_path = Path(self.project_manager.current_project)
                processed_dir = project_path / "data" / "processed" / "gnss"
                
                if processed_dir.exists():
                    import shutil
                    shutil.rmtree(processed_dir)
                    print(f"✅ Dossier de résultats supprimé: {processed_dir}")
                
                # Mettre à jour le statut du projet
                if hasattr(self.project_manager, 'update_gnss_status'):
                    self.project_manager.update_gnss_status("not_started")
            
            # Naviguer vers la page de calcul
            self.navigate_to_page(2)  # Page GNSS
            
            # Rafraîchir la page post-calcul si elle existe
            if hasattr(self, 'gnss_postcalc_page') and self.gnss_postcalc_page:
                self.gnss_postcalc_page.load_project_stats()
            
            self.set_status("🔄 Calculs GNSS réinitialisés")
            QMessageBox.information(self, "Réinitialisation", 
                                   "Les calculs GNSS ont été réinitialisés.\n"
                                   "Vous pouvez maintenant relancer les calculs.")
            
        except Exception as e:
            print(f"❌ Erreur réinitialisation GNSS: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la réinitialisation: {e}")
    
    def on_gnss_recalculate_requested(self):
        """Gère la demande de recalcul des calculs GNSS"""
        try:
            print("⚡ Recalcul des calculs GNSS demandé")
            
            # Naviguer vers la page de calcul
            self.navigate_to_page(2)  # Page GNSS
            
            # Déclencher automatiquement le calcul si possible
            if hasattr(self, 'gnss_page') and self.gnss_page:
                if hasattr(self.gnss_page, 'start_calculation'):
                    # Attendre un peu pour que la page soit chargée
                    QTimer.singleShot(1000, self.gnss_page.start_calculation)
                    self.set_status("⚡ Recalcul GNSS en cours...")
                else:
                    self.set_status("⚡ Naviguez vers la page GNSS pour relancer les calculs")
            
            QMessageBox.information(self, "Recalcul", 
                                   "Navigation vers la page de calcul.\n"
                                   "Les calculs vont être relancés automatiquement.")
            
        except Exception as e:
            print(f"❌ Erreur recalcul GNSS: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du recalcul: {e}")
    
    def check_gnss_calculations_status(self):
        """Vérifie si des calculs GNSS ont déjà été réalisés"""
        try:
            if not self.project_manager or not self.project_manager.project_path:
                return False
                
            project_path = Path(self.project_manager.project_path)
            processed_dir = project_path / "data" / "processed" / "gnss"
            
            if not processed_dir.exists():
                return False
            
            # Vérifier s'il y a des fichiers de résultats
            pos_files = list(processed_dir.glob("*.pos"))
            stat_files = list(processed_dir.glob("*.stat"))
            
            return len(pos_files) > 0 or len(stat_files) > 0
            
        except Exception as e:
            print(f"❌ Erreur vérification statut GNSS: {e}")
            return False
    
    def on_dual_baseline_completed(self, results):
        """Gère la fin du traitement des deux lignes de base"""
        print("🎉 Traitement des deux lignes de base terminé!")
        print(f"Résultats: {results}")
        
        # Mettre à jour le statut dans le projet
        if self.project_manager and self.project_manager.current_project:
            self.project_manager.current_project['workflow_status']['gnss_finalized'] = {
                'completed': True,
                'timestamp': datetime.now().isoformat(),
                'progress': 100
            }
            self.project_manager.save_project(auto=True)
    
    def on_dual_baseline_step_completed(self, step_name, result):
        """Gère la fin d'une étape du traitement des deux lignes de base"""
        print(f"✓ Étape {step_name} terminée: {result.get('status', 'unknown')}")
        
        # Mettre à jour la progression globale
        if self.progress_manager:
            if step_name == "rtk_processing":
                self.progress_manager.update_progress("GNSS_FINALIZED", 50.0)
            elif step_name == "data_preparation":
                self.progress_manager.update_progress("GNSS_FINALIZED", 100.0)

    # --- SLOTS ET GESTIONNAIRES D'ÉVÉNEMENTS ---
    
    def navigate_to_page(self, page_index: int):
        """Navigue vers une page via son index."""
        try:
            if 0 <= page_index < self.content_stack.count():
                self.content_stack.setCurrentIndex(page_index)
                widget_name = self.content_stack.widget(page_index).__class__.__name__
                self.set_status(f"Module actif : {widget_name}")
                
                # ✅ NOUVEAU : Rafraîchir la page post-calcul si c'est elle qui est sélectionnée
                if page_index == 3 and hasattr(self, 'gnss_postcalc_page') and self.gnss_postcalc_page:
                    print("🔄 Rafraîchissement de la page post-calcul")
                    self.gnss_postcalc_page.load_project_stats()
                
                # Mettre à jour le menu vertical
                if self.vertical_menu and hasattr(self.vertical_menu, 'select_page'):
                    # Ne pas créer de boucle si c'est déjà sélectionné
                    if hasattr(self.vertical_menu, 'current_page') and self.vertical_menu.current_page != page_index:
                        self.vertical_menu.select_page(page_index)
                        
        except Exception as e:
            print(f"❌ Erreur navigation page: {e}")

    def navigate_to_module_by_name(self, module_name: str):
        """Navigue vers un module via son nom (str)."""
        try:
            module_map = {
                "DIMCON": 1, 
                "GNSS": 2, 
                "GNSS_POSTCALC": 3,  # Page post-calcul
                "OBSERVATION": 4, 
                "QC": 5
            }
            index = module_map.get(module_name.upper(), 0)
            self.navigate_to_page(index)
            print(f"🧭 Navigation vers module {module_name} (index {index})")
        except Exception as e:
            print(f"❌ Erreur navigation module: {e}")

    def on_project_loaded(self, project_data: dict):
        """Met à jour l'application lorsqu'un projet est chargé - VERSION ENRICHIE"""
        try:
            vessel = project_data.get("metadata", {}).get("vessel", "Projet")
            company = project_data.get("metadata", {}).get("company", "")
            
            # Mettre à jour le titre de la fenêtre
            title = f"🚢 Calibration GNSS - [{vessel}]"
            if company:
                title += f" ({company})"
            self.setWindowTitle(title)
            
            self.set_status("✅ Projet chargé avec succès")
            
            # Mettre à jour la page d'accueil
            if self.home_page and hasattr(self.home_page, 'on_project_loaded'):
                self.home_page.on_project_loaded(project_data)
            
            # ✅ NOUVEAU : Synchroniser avec ApplicationData
            if self.app_data:
                print("🔄 Synchronisation données projet → ApplicationData")
                
                # Correspondre à la structure de ApplicationData
                if hasattr(self.app_data, 'dimcon'):
                    dimcon_points = project_data.get("dimcon_data", {}).get("points", {})
                    if dimcon_points:
                        self.app_data.dimcon = dimcon_points
                        print(f"  ✅ DIMCON: {len(dimcon_points)} points")
                
                if hasattr(self.app_data, 'gnss_data'):
                    gnss_config = project_data.get("gnss_config", {})
                    if gnss_config:
                        self.app_data.gnss_data.update(gnss_config)
                        print(f"  ✅ GNSS: Configuration mise à jour")
                
                # ✅ NOUVEAU : Charger les métadonnées GNSS enrichies
                if hasattr(self.project_manager, 'load_gnss_metadata_to_app_data'):
                    self.project_manager.load_gnss_metadata_to_app_data(self.app_data)
                    print("  ✅ Métadonnées GNSS enrichies chargées")
                
                # Notifier toutes les pages du changement
                if hasattr(self.app_data, 'data_changed'):
                    self.app_data.data_changed.emit("all")
            
            # ✅ NOUVEAU : Mettre à jour les barres de progression
            workflow_status = project_data.get("workflow_status", {})
            if self.vertical_menu and hasattr(self.vertical_menu, 'update_from_project'):
                self.vertical_menu.update_from_project(workflow_status)
            
            # ✅ NOUVEAU : Émettre les signaux de workflow pour synchronisation
            for step_name, step_data in workflow_status.items():
                if isinstance(step_data, dict) and step_data.get("completed"):
                    self.on_workflow_step_completed(step_name, True)
            
            print(f"✅ Projet chargé et synchronisé: {vessel}")
            
            # ✅ NOUVEAU : Navigation automatique vers la page post-calcul si des fichiers .pos existent
            if self.project_manager and hasattr(self.project_manager, 'should_navigate_to_finalization'):
                if self.project_manager.should_navigate_to_finalization():
                    print("🛰️ Fichiers .pos existants détectés - Navigation automatique vers la finalisation")
                    QTimer.singleShot(2000, lambda: self.navigate_to_page(3))  # Page post-calcul
                    self.set_status("🛰️ Fichiers .pos détectés - Affichage de la finalisation")
                else:
                    print("📊 Aucun fichier .pos détecté - Navigation normale")
            else:
                print("📊 ProjectManager non disponible - Navigation normale")
            
        except Exception as e:
            print(f"❌ Erreur chargement projet: {e}")
            import traceback
            traceback.print_exc()

    def on_data_changed(self, section: str):
        """Réagit aux changements de données."""
        try:
            print(f"Changement de données détecté dans la section : {section}")
            self.set_status(f"Données '{section}' mises à jour.")
            
            # Déclencher le calcul de progression si ProgressManager est disponible
            if hasattr(self, 'progress_manager') and self.progress_manager and hasattr(self, 'app_data') and self.app_data:
                print(f"🔄 Calcul progression déclenché pour section: {section}")
                self.progress_manager.calculate_all_progress(self.app_data)
            
            # Mettre à jour l'affichage si nécessaire
            if hasattr(self, 'home_page') and self.home_page:
                self.home_page.refresh_all_data()
                
        except Exception as e:
            print(f"❌ Erreur gestion changement données: {e}")

    # --- ACTIONS DE MENU ---
    
    def new_project(self):
        """Création de projet avec vérification ProjectManager"""
        try:
            if not self.project_manager:
                QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                  "Le gestionnaire de projet n'est pas disponible.")
                return
                
            if self.home_page and hasattr(self.home_page, 'create_new_project'):
                # Naviguer vers la page d'accueil
                self.navigate_to_page(0)
                self.home_page.create_new_project()
            else:
                QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                  "La page d'accueil n'est pas disponible.")
        except Exception as e:
            print(f"❌ Erreur création projet: {e}")

    def open_project(self):
        """Ouverture de projet avec vérification ProjectManager"""
        try:
            if not self.project_manager:
                QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                  "Le gestionnaire de projet n'est pas disponible.")
                return
                
            if self.home_page and hasattr(self.home_page, 'open_existing_project'):
                # Naviguer vers la page d'accueil
                self.navigate_to_page(0)
                self.home_page.open_existing_project()
            else:
                QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                  "La page d'accueil n'est pas disponible.")
        except Exception as e:
            print(f"❌ Erreur ouverture projet: {e}")

    def save_project(self):
        """Sauvegarde de projet avec vérification ProjectManager"""
        try:
            if not self.project_manager:
                QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                  "Le gestionnaire de projet n'est pas disponible.")
                return
                
            # ✅ NOUVEAU : Sauvegarde directe via ProjectManager si projet actuel
            if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
                # Synchroniser app_data vers projet avant sauvegarde
                if self.app_data and hasattr(self.project_manager, 'update_gnss_metadata_in_project'):
                    self.project_manager.update_gnss_metadata_in_project(self.app_data)
                
                success, message = self.project_manager.save_project()
                if success:
                    QMessageBox.information(self, "Sauvegarde", message)
                else:
                    QMessageBox.warning(self, "Erreur Sauvegarde", message)
            else:
                # Fallback vers la page d'accueil
                if self.home_page and hasattr(self.home_page, 'save_current_project'):
                    self.home_page.save_current_project()
                else:
                    QMessageBox.warning(self, "Fonctionnalité indisponible", 
                                      "Aucun projet à sauvegarder.")
        except Exception as e:
            print(f"❌ Erreur sauvegarde projet: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde :\n{str(e)}")
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        about_text = """
🚢 <b>Calibration GNSS</b><br>
Version 2.0<br><br>

Application de calibration GNSS pour navires<br>
avec support complet des workflows:<br><br>

• <b>DIMCON</b> - Configuration dimensions<br>
• <b>GNSS</b> - Traitement RTK avec SP3<br>
• <b>Observations</b> - Gestion capteurs<br>
• <b>QC</b> - Contrôle qualité<br><br>

© 2025 Marine Navigation
        """
        QMessageBox.about(self, "À propos", about_text)

    def show_welcome_message(self):
        """Affiche un message de bienvenue avec diagnostic"""
        QTimer.singleShot(1000, lambda: self.set_status("Prêt - Créez ou ouvrez un projet."))
        QTimer.singleShot(2000, self.run_full_diagnostic)
    
    def run_full_diagnostic(self):
        """Lance un diagnostic complet de l'application avec ProjectManager"""
        print("\n🔬 === DIAGNOSTIC COMPLET APPLICATION ===")
        
        checks = [
            ("QApplication", QApplication.instance() is not None),
            ("Settings", hasattr(self, 'settings') and self.settings is not None),
            ("AppData", hasattr(self, 'app_data') and self.app_data is not None),
            ("ProjectManager", hasattr(self, 'project_manager') and self.project_manager is not None),
            ("VerticalMenu", hasattr(self, 'vertical_menu') and self.vertical_menu is not None),
            ("HomePageWidget", hasattr(self, 'home_page') and self.home_page is not None),
            ("GnssWidget", hasattr(self, 'gnss_page') and self.gnss_page is not None),
            ("ContentStack", hasattr(self, 'content_stack') and self.content_stack is not None)
        ]
        
        for check_name, check_result in checks:
            status = "✅ OK" if check_result else "❌ MANQUE"
            print(f"   {check_name:<15}: {status}")
        
        # ✅ NOUVEAU : Diagnostic ProjectManager spécifique
        if hasattr(self, 'project_manager') and self.project_manager:
            print("\n📁 Diagnostic ProjectManager:")
            pm_checks = [
                ("Instance", self.project_manager is not None),
                ("Projet actuel", hasattr(self.project_manager, 'current_project') and self.project_manager.current_project is not None),
                ("Auto-save", hasattr(self.project_manager, 'auto_save_enabled')),
                ("Signaux", hasattr(self.project_manager, 'project_loaded')),
                ("Validation RINEX", hasattr(self.project_manager, 'valider_import_rinex_dans_projet'))
            ]
            
            for check_name, check_result in pm_checks:
                status = "✅ OK" if check_result else "❌ MANQUE"
                print(f"   {check_name:<15}: {status}")
            
            # Informations sur le projet actuel
            if hasattr(self.project_manager, 'get_project_info'):
                project_info = self.project_manager.get_project_info()
                if project_info:
                    print(f"   Projet: {project_info.get('name', 'N/A')}")
                    print(f"   Navire: {project_info.get('metadata', {}).get('vessel', 'N/A')}")
        
        # Diagnostic spécifique GNSS
        if hasattr(self, 'gnss_page') and self.gnss_page:
            print("\n🛰️ Diagnostic GNSS:")
            gnss_checks = [
                ("SP3 Support", hasattr(self.gnss_page, 'sp3_progress_updated')),
                ("RTK Support", hasattr(self.gnss_page, 'baseline_progress_updated')),
                ("Menu Connection", self.vertical_menu and hasattr(self.vertical_menu, 'gnss_progress')),
                ("ProjectManager Connection", hasattr(self.gnss_page, 'project_manager') and self.gnss_page.project_manager is not None)
            ]
            for check_name, check_result in gnss_checks:
                status = "✅ OK" if check_result else "❌ MANQUE"
                print(f"   {check_name:<15}: {status}")
        
        print("🔬 === FIN DIAGNOSTIC ===\n")
    def set_status(self, message: str):
        """Met à jour la barre d'état de manière sécurisée."""
        try:
            if self.status_label:
                self.status_label.setText(message)
            print(f"📊 Status: {message}")
        except Exception as e:
            print(f"❌ Erreur mise à jour status: {e}")

    # --- GESTION DE LA FENÊTRE ---

    def load_settings(self):
        """Charge la géométrie de la fenêtre."""
        try:
            if hasattr(self.settings, 'value'):
                geometry = self.settings.value("geometry")
                if geometry:
                    self.restoreGeometry(geometry)
            print("✅ Paramètres chargés")
        except Exception as e:
            print(f"❌ Erreur chargement paramètres: {e}")

    def save_settings(self):
        """Sauvegarde la géométrie de la fenêtre."""
        try:
            if hasattr(self.settings, 'setValue'):
                self.settings.setValue("geometry", self.saveGeometry())
            print("✅ Paramètres sauvegardés")
        except Exception as e:
            print(f"❌ Erreur sauvegarde paramètres: {e}")

    def closeEvent(self, event):
        """Gère la fermeture de l'application avec ProjectManager"""
        try:
            # Sauvegarder les paramètres
            self.save_settings()
            
            # ✅ NOUVEAU : Synchroniser et fermer le projet via ProjectManager
            if self.project_manager:
                print("📁 Fermeture du projet...")
                
                # Synchroniser app_data vers projet avant fermeture
                if self.app_data and hasattr(self.project_manager, 'update_gnss_metadata_in_project'):
                    try:
                        self.project_manager.update_gnss_metadata_in_project(self.app_data)
                        print("✅ Données synchronisées avant fermeture")
                    except Exception as e:
                        print(f"⚠️ Erreur synchronisation finale: {e}")
                
                # Fermer le projet proprement
                if hasattr(self.project_manager, 'close_project'):
                    self.project_manager.close_project()
                    print("✅ Projet fermé")
            
            print("👋 Fermeture de l'application.")
            event.accept()
            
        except Exception as e:
            print(f"❌ Erreur fermeture: {e}")
            event.accept()  # Forcer la fermeture même en cas d'erreur


def main():
    """Fonction principale de l'application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Appliquer un style sombre global
    dark_stylesheet = """
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        QMainWindow, QDialog {
            background-color: #1e1e1e;
        }
        QMenuBar {
            background-color: #2d2d30;
        }
        QStatusBar {
            background-color: #2d2d30;
        }
    """
    app.setStyleSheet(dark_stylesheet)

    try:
        window = CalibrationMainWindow()
        window.show()
        print("🚀 Application lancée avec succès")
        sys.exit(app.exec_())
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "Erreur Fatale", f"Impossible de lancer l'application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()