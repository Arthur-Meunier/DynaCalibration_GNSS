# page_accueil.py - Version refactorisée et fonctionnelle

import os
import json
import sys
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox,
    QFileDialog, QProgressDialog, QApplication, QDialog, QTextEdit,
    QPushButton, QTabWidget, QLabel, QLineEdit, QDialogButtonBox, 
    QButtonGroup, QRadioButton, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QSettings
from PyQt5.QtGui import QFont

# === CONFIGURATION DES IMPORTS ===
print("🔍 Configuration des imports pour page_accueil...")

# Ajout du répertoire racine au PYTHONPATH
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

print(f"📁 Racine du projet: {root_dir}")

# === IMPORTS DES MODULES DE L'APPLICATION ===
IMPORTS_SUCCESS = True
missing_modules = []

try:
    # Widgets de l'interface graphique - NOMS CORRECTS
    from app.gui.html_dashboard_widget import HTMLCircularDashboard as CircularDashboardWidget
    from app.gui.project_info_widget import ProjectInfoWidget
    from app.gui.quick_actions_widget import QuickActionsWidget
    from app.gui.status_bar_widget import StatusBarWidget
    print("✅ Widgets GUI importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import widgets GUI: {e}")
    missing_modules.append("GUI Widgets")
    # Classes de remplacement pour éviter les crashes
    CircularDashboardWidget = ProjectInfoWidget = QuickActionsWidget = StatusBarWidget = QWidget
    IMPORTS_SUCCESS = False

try:
    # Modules principaux (core)
    from core.project_manager import ProjectManager
    from core.app_data import ApplicationData
    print("✅ Modules core importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import modules core: {e}")
    missing_modules.append("Core Modules")
    ProjectManager = ApplicationData = None
    IMPORTS_SUCCESS = False

if not IMPORTS_SUCCESS:
    print(f"⚠️ Modules manquants: {', '.join(missing_modules)}")
    print("   L'application fonctionnera en mode dégradé")

try:
    from core.progress_manager import ProgressManager
    PROGRESS_MANAGER_AVAILABLE = True
    print("✅ ProgressManager importé avec succès")
except ImportError as e:
    print(f"⚠️ ProgressManager non disponible: {e}")
    PROGRESS_MANAGER_AVAILABLE = False


# === CLASSES UTILITAIRES ===

class StatisticsDialog(QDialog):
    """Dialogue d'affichage des statistiques détaillées du projet"""
    
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.init_dialog()
        self.setup_ui()
        self.load_statistics()

    def init_dialog(self):
        """Initialise les propriétés du dialogue"""
        self.setWindowTitle("📊 Statistiques Détaillées du Projet")
        self.setModal(True)
        self.resize(800, 600)

    def setup_ui(self):
        """Configure l'interface du dialogue"""
        layout = QVBoxLayout(self)
        
        # Système d'onglets
        self.tabs = QTabWidget()
        
        # Configuration des onglets
        tab_configs = [
            ("overview_tab", "📋 Vue d'ensemble"),
            ("dimcon_tab", "📐 DIMCON"),
            ("gnss_tab", "🛰️ GNSS"),
            ("obs_tab", "📊 Capteurs")
        ]
        
        for attr_name, tab_title in tab_configs:
            tab_widget = QTextEdit()
            tab_widget.setReadOnly(True)
            tab_widget.setFont(QFont("Consolas", 10))
            setattr(self, attr_name, tab_widget)
            self.tabs.addTab(tab_widget, tab_title)
        
        layout.addWidget(self.tabs)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("📄 Exporter Statistiques")
        export_btn.clicked.connect(self.export_statistics)
        
        close_btn = QPushButton("✖️ Fermer")
        close_btn.clicked.connect(self.accept)
        
        buttons_layout.addWidget(export_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        self.apply_styles()

    def apply_styles(self):
        """Applique le thème sombre"""
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: white; }
            QTabWidget::pane { border: 1px solid #555; background-color: #2d2d30; }
            QTabBar::tab { 
                background-color: #3e3e42; color: white; padding: 8px 16px; 
                margin-right: 2px; border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected { background-color: #007acc; }
            QTabBar::tab:hover { background-color: #505050; }
            QTextEdit { 
                background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #555; 
                font-family: 'Consolas', monospace; line-height: 1.4;
            }
            QPushButton { 
                background-color: #007acc; color: white; border: none; 
                padding: 8px 16px; border-radius: 4px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004577; }
        """)

    def load_statistics(self):
        """Charge et affiche les statistiques dans chaque onglet"""
        if not self.project_data:
            for tab in [self.overview_tab, self.dimcon_tab, self.gnss_tab, self.obs_tab]:
                tab.setText("❌ Aucune donnée de projet disponible")
            return
        
        # Chargement des statistiques par onglet
        self.overview_tab.setText(self.generate_overview_stats())
        self.dimcon_tab.setText(self.generate_dimcon_stats())
        self.gnss_tab.setText(self.generate_gnss_stats())
        self.obs_tab.setText(self.generate_observation_stats())

    def generate_overview_stats(self):
        """Génère les statistiques générales du projet"""
        metadata = self.project_data.get('metadata', {})
        workflow = self.project_data.get('workflow_status', {})
        
        stats = f"""
=== STATISTIQUES GÉNÉRALES DU PROJET ===

📋 Informations Projet:
   • Nom: {metadata.get('vessel', 'Non défini')}
   • Société: {metadata.get('company', 'Non définie')}
   • Ingénieur: {metadata.get('engineer', 'Non défini')}
   • Version: {metadata.get('version', '1.0')}
   • Créé: {metadata.get('created', 'Non défini')[:16]}
   • Modifié: {metadata.get('last_modified', 'Non défini')[:16]}

📊 Progression du Workflow:
"""
        
        modules = ['dimcon', 'gnss', 'observation', 'qc']
        total_progress = 0
        completed_modules = 0
        
        for module in modules:
            module_data = workflow.get(module, {})
            progress = module_data.get('progress', 0)
            completed = module_data.get('completed', False)
            
            status = "✅ Terminé" if completed else f"🔄 {progress:.0f}%"
            stats += f"   • {module.upper():<12}: {status}\n"
            
            total_progress += progress
            if completed:
                completed_modules += 1
        
        avg_progress = total_progress / len(modules) if modules else 0
        
        stats += f"""
📈 Résumé Global:
   • Progression totale: {avg_progress:.1f}%
   • Modules terminés: {completed_modules}/{len(modules)}
   • Modules en cours: {len(modules) - completed_modules}
"""
        return stats

    def generate_dimcon_stats(self):
        """Génère les statistiques DIMCON"""
        dimcon_data = self.project_data.get('dimcon_data', {})
        points = dimcon_data.get('points', {})
        
        stats = "=== STATISTIQUES DIMCON ===\n\n📐 Configuration Géométrique:\n\n"
        
        required_points = ['Bow', 'Port', 'Stb']
        defined_count = 0
        
        for point in required_points:
            if point in points:
                coords = points[point]
                x, y, z = coords.get('X', 0), coords.get('Y', 0), coords.get('Z', 0)
                
                if abs(x) > 0.001 or abs(y) > 0.001 or abs(z) > 0.001:
                    defined_count += 1
                    stats += f"   ✅ {point:<4}: X={x:>8.3f}m, Y={y:>8.3f}m, Z={z:>8.3f}m\n"
                else:
                    stats += f"   ❌ {point:<4}: Non défini\n"
            else:
                stats += f"   ❌ {point:<4}: Non configuré\n"
        
        stats += f"\n✅ Statut: {defined_count}/{len(required_points)} points définis"
        return stats

    def generate_gnss_stats(self):
        """Génère les statistiques GNSS"""
        gnss_data = self.project_data.get('gnss_data', {})
        
        stats = f"""
=== STATISTIQUES GNSS ===

🛰️ Configuration:
   • Station de base: {gnss_data.get('base_station', 'Non définie')}
   • Convergence méridienne: {gnss_data.get('meridian_convergence', 0):.6f}°
   • Facteur d'échelle: {gnss_data.get('scale_factor', 1.0):.8f}

📡 Points mobiles: {len(gnss_data.get('rovers', []))}
"""
        return stats

    def generate_observation_stats(self):
        """Génère les statistiques des capteurs"""
        sensors = self.project_data.get('observation_sensors', [])
        
        stats = f"""
=== STATISTIQUES CAPTEURS ===

📊 Configuration:
   • Nombre total: {len(sensors)}
   • Configurés: {sum(1 for s in sensors if s.get('configured', False))}
"""
        return stats

    def export_statistics(self):
        """Exporte les statistiques vers un fichier"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter les statistiques",
                f"stats_projet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Fichiers texte (*.txt);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("RAPPORT STATISTIQUE COMPLET\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n\n")
                    
                    # Export de tous les onglets
                    tabs_content = [
                        ("VUE D'ENSEMBLE", self.overview_tab.toPlainText()),
                        ("DIMCON", self.dimcon_tab.toPlainText()),
                        ("GNSS", self.gnss_tab.toPlainText()),
                        ("CAPTEURS", self.obs_tab.toPlainText())
                    ]
                    
                    for title, content in tabs_content:
                        f.write(f"\n{title}\n")
                        f.write("-" * len(title) + "\n")
                        f.write(content)
                        f.write("\n\n")
                
                QMessageBox.information(self, "Export Réussi", 
                                      f"Statistiques exportées vers:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'Export", 
                               f"Impossible d'exporter:\n{str(e)}")


class ExportThread(QThread):
    """Thread pour l'export de rapport en arrière-plan"""
    
    progress_updated = pyqtSignal(int, str)
    export_finished = pyqtSignal(bool, str)
    
    def __init__(self, project_manager, export_format, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.export_format = export_format
    
    def run(self):
        """Exécute l'export en arrière-plan"""
        try:
            self.progress_updated.emit(10, "Initialisation de l'export...")
            
            # Simulation de progression (remplacer par le vrai travail)
            steps = [20, 40, 60, 80, 95]
            messages = [
                "Collecte des données...",
                "Formatage du rapport...",
                "Génération du fichier...",
                "Finalisation...",
                "Export terminé"
            ]
            
            for step, message in zip(steps, messages):
                self.msleep(300)  # Simulation du travail
                self.progress_updated.emit(step, message)
            
            # Export réel si le project_manager le supporte
            if hasattr(self.project_manager, 'export_report'):
                success, result = self.project_manager.export_report(self.export_format)
            else:
                # Fallback pour la compatibilité
                success, result = True, f"Export {self.export_format} simulé"
            
            self.progress_updated.emit(100, "Terminé")
            self.export_finished.emit(success, result)
            
        except Exception as e:
            self.export_finished.emit(False, str(e))


# === CLASSE PRINCIPALE ===

class HomePageWidget(QWidget):
    """
    Page d'accueil principale de l'application de calibration GNSS
    Interface unifiée avec dashboard, informations projet et actions rapides
    """
    
    # Signaux principaux
    module_navigation_requested = pyqtSignal(str)  # Navigation vers un module
    
    # CORRECTION 1: Remplacer le constructeur __init__
    def __init__(self, app_data=None, settings=None, progress_manager=None, parent=None):
        super().__init__(parent)
        
        # === DEBUG: Diagnostic détaillé des imports ===
        print("\n🔍 === DIAGNOSTIC IMPORTS DÉTAILLÉ ===")
        
        # Test d'import individuel de chaque widget
        widget_imports = {}
        
        try:
            from app.gui.html_dashboard_widget import HTMLCircularDashboard
            widget_imports['HTMLCircularDashboard'] = "✅ OK"
            print("✅ HTMLCircularDashboard importé")
        except Exception as e:
            widget_imports['HTMLCircularDashboard'] = f"❌ {e}"
            print(f"❌ HTMLCircularDashboard: {e}")
        
        try:
            from app.gui.project_info_widget import ProjectInfoWidget
            widget_imports['ProjectInfoWidget'] = "✅ OK"
            print("✅ ProjectInfoWidget importé")
        except Exception as e:
            widget_imports['ProjectInfoWidget'] = f"❌ {e}"
            print(f"❌ ProjectInfoWidget: {e}")
        
        try:
            from app.gui.quick_actions_widget import QuickActionsWidget
            widget_imports['QuickActionsWidget'] = "✅ OK"
            print("✅ QuickActionsWidget importé")
        except Exception as e:
            widget_imports['QuickActionsWidget'] = f"❌ {e}"
            print(f"❌ QuickActionsWidget: {e}")
        
        try:
            from app.gui.status_bar_widget import StatusBarWidget
            widget_imports['StatusBarWidget'] = "✅ OK"
            print("✅ StatusBarWidget importé")
        except Exception as e:
            widget_imports['StatusBarWidget'] = f"❌ {e}"
            print(f"❌ StatusBarWidget: {e}")
        
        print("🔍 === FIN DIAGNOSTIC IMPORTS ===\n")
        
        # Forcer IMPORTS_SUCCESS selon les imports réels
        self.imports_success = all("✅" in status for status in widget_imports.values())
        print(f"📊 IMPORTS_SUCCESS: {self.imports_success}")
        
        # Reste du constructeur existant...
        try:
            if settings is not None:
                self.settings = settings
            else:
                self.settings = QSettings("CalibrationGNSS", "MainApp")
            print(f"✅ Settings initialisé: {type(self.settings)}")
        except Exception as e:
            print(f"❌ Erreur settings: {e}")
            from PyQt5.QtCore import QObject
            self.settings = QObject()  # Fallback
        
        self.current_project_data = None
        self.auto_save_enabled = True
        
        self.app_data = app_data 
        self.progress_manager = progress_manager
        self.project_manager = self.create_project_manager()
        
        # === Initialisation défensive des widgets ===
        self.dashboard = None
        self.project_info = None
        self.quick_actions = None
        self.status_bar = None
        
        self.setup_timers()
        
        # === Initialisation de l'interface avec diagnostic ===
        try:
            print("\n🔧 === INITIALISATION INTERFACE ===")
            self.initialize_interface()
            print("✅ Interface HomePageWidget initialisée")
            
            # Diagnostic post-initialisation
            self.check_widgets_status()
            
        except Exception as e:
            print(f"❌ Erreur initialisation interface: {e}")
            
        
        if PROGRESS_MANAGER_AVAILABLE:
            self.progress_manager = ProgressManager()
        else:
            self.progress_manager = None
    
    def setup_timers(self):
        """Configure les timers de mise à jour et sauvegarde"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_all_data)
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_project)

    def initialize_interface(self):
        """Initialise l'interface utilisateur"""
        try:
            if self.imports_success:
                self.setup_main_ui()
                self.connect_signals()
                self.apply_styles()
                
                # Démarrage des timers avec des intervalles plus longs pour éviter les blocages
                self.update_timer.start(15000)    # Mise à jour toutes les 15s
                self.auto_save_timer.start(120000) # Sauvegarde toutes les 2min
                
                # Initialiser l'état des boutons (aucun projet chargé)
                self.set_project_loaded(False)
                
                print("✅ Page d'accueil initialisée avec succès")
            else:
                
                print("⚠️ Page d'accueil en mode dégradé")
                
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            

    def create_project_manager(self):
        """Crée le gestionnaire de projet"""
        if not self.imports_success or ProjectManager is None:
            print("⚠️ ProjectManager non disponible")
            return None
        
        try:
            # Utiliser singleton si disponible
            if hasattr(ProjectManager, 'instance'):
                pm = ProjectManager.instance()
            else:
                pm = ProjectManager()
            
            # Connecter les signaux si disponibles
            if hasattr(pm, 'project_loaded'):
                pm.project_loaded.connect(self.on_project_loaded)
            if hasattr(pm, 'project_saved'):
                pm.project_saved.connect(self.on_project_saved)
            
            print("✅ ProjectManager créé avec succès")
            return pm
            
        except Exception as e:
            print(f"❌ Erreur création ProjectManager: {e}")
            return None

    
    def setup_main_ui(self):
        """Configure l'interface principale avec diagnostic détaillé"""
        print("\n🏗️ === SETUP INTERFACE PRINCIPALE ===")
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        content_grid = QGridLayout()
        content_grid.setSpacing(15)
        
        # === DASHBOARD avec diagnostic détaillé ===
        print("🔄 Création dashboard...")
        try:
            self.dashboard = CircularDashboardWidget()
            self.dashboard.setMinimumSize(350, 350)
            print(f"✅ Dashboard créé: {type(self.dashboard)}")
            
            # 🔧 FORCER LA MISE À JOUR DU DASHBOARD AU DÉMARRAGE
            QTimer.singleShot(2000, self.refresh_dashboard_data)
            print("🔄 Mise à jour dashboard programmée (2s)")
            
        except Exception as e:
            print(f"❌ Erreur création dashboard: {e}")
            import traceback
            traceback.print_exc()
            self.dashboard = QWidget()  # Widget vide de remplacement
            print("⚠️ Dashboard de secours créé")
        
        # === PROJECT_INFO avec diagnostic détaillé ===
        print("🔄 Création project_info...")
        try:
            self.project_info = ProjectInfoWidget(progress_manager=self.progress_manager, app_data=self.app_data)
            print(f"✅ ProjectInfoWidget créé: {type(self.project_info)}")
        except Exception as e:
            print(f"❌ Erreur création project_info: {e}")
            import traceback
            traceback.print_exc()
            self.project_info = QLabel("❌ ProjectInfoWidget\nindisponible")
            self.project_info.setAlignment(Qt.AlignCenter)
            self.project_info.setStyleSheet("""
                QLabel {
                    background-color: #2d2d30;
                    border: 2px solid #dc3545;
                    border-radius: 8px;
                    padding: 20px;
                    color: #ffffff;
                }
            """)
            print("⚠️ ProjectInfoWidget de secours créé")
        
        # === QUICK_ACTIONS avec diagnostic détaillé ===
        print("🔄 Création quick_actions...")
        try:
            self.quick_actions = QuickActionsWidget()
            print(f"✅ QuickActionsWidget créé: {type(self.quick_actions)}")
        except Exception as e:
            print(f"❌ Erreur création quick_actions: {e}")
            import traceback
            traceback.print_exc()
            self.quick_actions = QLabel("❌ QuickActionsWidget\nindisponible")
            self.quick_actions.setAlignment(Qt.AlignCenter)
            print("⚠️ QuickActionsWidget de secours créé")
        
        # Assemblage
        print("🔧 Assemblage des widgets...")
        try:
            content_grid.addWidget(self.dashboard, 0, 0, 2, 1)
            content_grid.addWidget(self.project_info, 0, 1, 1, 1)
            content_grid.addWidget(self.quick_actions, 1, 1, 1, 1)
            
            content_grid.setColumnStretch(0, 2)
            content_grid.setColumnStretch(1, 1)
            
            main_layout.addLayout(content_grid)
            print("✅ Widgets assemblés dans la grille")
        except Exception as e:
            print(f"❌ Erreur assemblage widgets: {e}")
            import traceback
            traceback.print_exc()
        
        # === STATUS_BAR avec diagnostic détaillé ===
        print("🔄 Création status_bar...")
        try:
            self.status_bar = StatusBarWidget()
            main_layout.addWidget(self.status_bar)
            print(f"✅ StatusBarWidget créé: {type(self.status_bar)}")
        except Exception as e:
            print(f"❌ Erreur création status_bar: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar = QLabel("Status: Prêt")
            main_layout.addWidget(self.status_bar)
            print("⚠️ StatusBar de secours créé")
        
        print("✅ Interface principale configurée avec diagnostic détaillé")
        
        # Diagnostic final des widgets
        self.check_widgets_status()    
    def check_widgets_status(self):
        """Vérifie l'état de tous les widgets pour debugging - VERSION ÉTENDUE"""
        print("\n🔍 === DIAGNOSTIC WIDGETS DÉTAILLÉ ===")
        
        widgets_status = {
            'dashboard': self.dashboard,
            'project_info': self.project_info,
            'quick_actions': self.quick_actions,
            'status_bar': self.status_bar,
            'settings': getattr(self, 'settings', None)
        }
        
        all_widgets_ok = True
        
        for name, widget in widgets_status.items():
            if widget is not None:
                widget_type = type(widget).__name__
                
                # Vérifier si c'est le bon type de widget
                if name == 'dashboard' and 'HTMLCircularDashboard' not in widget_type and widget_type != 'QWidget':
                    print(f"⚠️ {name}: {widget_type} (type inattendu)")
                    all_widgets_ok = False
                elif name in ['project_info', 'quick_actions', 'status_bar'] and 'Widget' not in widget_type and widget_type != 'QLabel':
                    print(f"⚠️ {name}: {widget_type} (type inattendu)")
                    all_widgets_ok = False
                else:
                    print(f"✅ {name}: {widget_type}")
                    
                    # Tester les méthodes principales si c'est un vrai widget
                    if hasattr(widget, 'setEnabled'):
                        try:
                            widget.setEnabled(True)
                            print(f"   └─ setEnabled: OK")
                        except Exception as e:
                            print(f"   └─ setEnabled: ❌ {e}")
                            all_widgets_ok = False
            else:
                print(f"❌ {name}: None")
                all_widgets_ok = False
        
        print(f"\n📊 Statut global des widgets: {'✅ OK' if all_widgets_ok else '❌ PROBLÈME'}")
        print("🔍 === FIN DIAGNOSTIC WIDGETS ===\n")
        
        # Si des widgets sont manquants, proposer une réparation
        if not all_widgets_ok:
            print("🔧 === TENTATIVE DE RÉPARATION ===")
            self.repair_missing_widgets()
        
        return widgets_status
    
    def repair_missing_widgets(self):
        """Tente de réparer les widgets manquants"""
        print("🔧 Tentative de réparation des widgets...")
        
        try:
            # Réparation dashboard
            if self.dashboard is None:
                print("🔧 Réparation dashboard...")
                try:
                    from app.gui.html_dashboard_widget import HTMLCircularDashboard
                    self.dashboard = HTMLCircularDashboard()
                    print("✅ Dashboard réparé")
                except:
                    self.dashboard = QWidget()
                    print("⚠️ Dashboard remplacé par widget générique")
            
            # Réparation project_info
            if self.project_info is None:
                print("🔧 Réparation project_info...")
                try:
                    from app.gui.project_info_widget import ProjectInfoWidget
                    self.project_info = ProjectInfoWidget(progress_manager=self.progress_manager, app_data=self.app_data)
                    print("✅ ProjectInfo réparé")
                except:
                    self.project_info = QLabel("Info Projet")
                    print("⚠️ ProjectInfo remplacé par label")
            
            # Réparation quick_actions
            if self.quick_actions is None:
                print("🔧 Réparation quick_actions...")
                try:
                    from app.gui.quick_actions_widget import QuickActionsWidget
                    self.quick_actions = QuickActionsWidget()
                    print("✅ QuickActions réparé")
                except:
                    self.quick_actions = QLabel("Actions Rapides")
                    print("⚠️ QuickActions remplacé par label")
            
            # Réparation status_bar
            if self.status_bar is None:
                print("🔧 Réparation status_bar...")
                try:
                    from app.gui.status_bar_widget import StatusBarWidget
                    self.status_bar = StatusBarWidget()
                    print("✅ StatusBar réparé")
                except:
                    self.status_bar = QLabel("Status: Prêt")
                    print("⚠️ StatusBar remplacé par label")
                    
            print("🔧 === FIN RÉPARATION ===")
            
        except Exception as e:
            print(f"❌ Erreur durant la réparation: {e}")
            import traceback
            traceback.print_exc()
    def connect_signals(self):
        """Connecte tous les signaux des widgets"""
        try:
            # Signaux du dashboard
            if self.dashboard and hasattr(self.dashboard, 'segment_clicked'):
                self.dashboard.segment_clicked.connect(self.on_dashboard_segment_clicked)
             # === NOUVEAU : Connexion pour tâches détaillées ===
            if self.dashboard and hasattr(self.dashboard, 'task_selected'):
                self.dashboard.task_selected.connect(self.on_task_selected)
                print("✅ Signal task_selected connecté")
            
            # === NOUVEAU : Signaux ProgressManager ===
            if hasattr(self, 'progress_manager') and self.progress_manager:
                if hasattr(self.progress_manager, 'progress_updated'):
                    self.progress_manager.progress_updated.connect(self.on_progress_updated)           
                if hasattr(self.progress_manager, 'module_completed'):
                    self.progress_manager.module_completed.connect(self.on_module_completed)
                print("✅ Signaux ProgressManager connectés")
            
            # === CORRECTION : Connexion directe ProjectManager → Dashboard ===
            if hasattr(self, 'project_manager') and self.project_manager:
                if hasattr(self.project_manager, 'workflow_step_completed'):
                    self.project_manager.workflow_step_completed.connect(self.on_workflow_step_completed)
                    print("✅ Signal workflow_step_completed connecté au dashboard")
                if hasattr(self.project_manager, 'qc_score_updated'):
                    self.project_manager.qc_score_updated.connect(self.on_qc_score_updated)
                    print("✅ Signal qc_score_updated connecté au dashboard")
            # Signaux des informations projet
            if self.project_info and hasattr(self.project_info, 'edit_requested'):
                self.project_info.edit_requested.connect(self.edit_project_info)
            
            # Signaux des actions rapides (sans settings)
            if self.quick_actions:
                if hasattr(self.quick_actions, 'statistics_requested'):
                    self.quick_actions.statistics_requested.connect(self.show_detailed_statistics)
                if hasattr(self.quick_actions, 'export_requested'):
                    self.quick_actions.export_requested.connect(self.export_project_report)
                if hasattr(self.quick_actions, 'save_requested'):
                    self.quick_actions.save_requested.connect(self.save_current_project)
                if hasattr(self.quick_actions, 'refresh_requested'):
                    self.quick_actions.refresh_requested.connect(self.force_refresh)
            
            # Signaux de la barre d'état
            if self.status_bar:
                if hasattr(self.status_bar, 'save_requested'):
                    self.status_bar.save_requested.connect(self.save_current_project)
                if hasattr(self.status_bar, 'module_indicator_clicked'):
                    self.status_bar.module_indicator_clicked.connect(self.on_module_indicator_clicked)
            
            print("✅ Signaux connectés")
            
        except Exception as e:
            print(f"❌ Erreur connexion signaux: {e}")

    def apply_styles(self):
        """Applique le thème global"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

    # === GESTION DE PROJET ===

    def create_new_project(self):
        """Crée un nouveau projet avec dialogue complet"""
        print("🆕 Création d'un nouveau projet")
        
        if not self.project_manager:
            QMessageBox.warning(self, "Indisponible", 
                              "Gestionnaire de projet non disponible")
            return
        
        # Créer le dialogue personnalisé
        dialog = QDialog(self)
        dialog.setWindowTitle("Créer un Nouveau Projet")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        # Layout principal
        layout = QVBoxLayout(dialog)
        
        # === CHAMPS DU FORMULAIRE ===
        
        # Nom du projet
        layout.addWidget(QLabel("Nom du projet *:"))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Ex: Calibration_Vessel_2024")
        layout.addWidget(name_edit)
        
        # Navire
        layout.addWidget(QLabel("Navire *:"))
        vessel_edit = QLineEdit()
        vessel_edit.setPlaceholderText("Ex: MV Atlantic Explorer")
        layout.addWidget(vessel_edit)
        
        # Société
        layout.addWidget(QLabel("Société *:"))
        company_edit = QLineEdit()
        company_edit.setPlaceholderText("Ex: Marine Dynamics Ltd")
        layout.addWidget(company_edit)
        
        # Ingénieur
        layout.addWidget(QLabel("Ingénieur responsable *:"))
        engineer_edit = QLineEdit()
        engineer_edit.setPlaceholderText("Ex: Jean Dupont")
        layout.addWidget(engineer_edit)
        
        # Répertoire de base (optionnel)
        layout.addWidget(QLabel("Répertoire de base (optionnel):"))
        base_path_layout = QHBoxLayout()
        base_path_edit = QLineEdit()
        base_path_edit.setPlaceholderText("Laissez vide pour utiliser le répertoire par défaut")
        browse_btn = QPushButton("📁 Parcourir")
        
        def browse_directory():
            directory = QFileDialog.getExistingDirectory(
                dialog, "Choisir le répertoire de base", 
                os.path.expanduser("~")
            )
            if directory:
                base_path_edit.setText(directory)
        
        browse_btn.clicked.connect(browse_directory)
        base_path_layout.addWidget(base_path_edit)
        base_path_layout.addWidget(browse_btn)
        layout.addLayout(base_path_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(80)
        description_edit.setPlaceholderText("Description optionnelle du projet...")
        layout.addWidget(description_edit)
        
        # === BOUTONS D'ACTION ===
        buttons_layout = QHBoxLayout()
        
        create_btn = QPushButton("✅ Créer le Projet")
        create_btn.setDefault(True)
        cancel_btn = QPushButton("❌ Annuler")
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(create_btn)
        layout.addLayout(buttons_layout)
        
        # === STYLE DU DIALOGUE ===
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                font-weight: bold;
                color: #ffffff;
                margin-top: 8px;
            }
            QLineEdit, QTextEdit {
                background-color: #2d2d30;
                border: 2px solid #3e3e42;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #007acc;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004577;
            }
            QPushButton#cancel {
                background-color: #6c757d;
            }
            QPushButton#cancel:hover {
                background-color: #545b62;
            }
        """)
        
        cancel_btn.setObjectName("cancel")
        
        # === CONNEXIONS ===
        cancel_btn.clicked.connect(dialog.reject)
        
        def validate_and_create():
            # Utiliser QTimer.singleShot pour éviter les blocages
            QTimer.singleShot(0, lambda: self._create_project_async(
                name_edit, vessel_edit, company_edit, engineer_edit, 
                description_edit, base_path_edit, dialog
            ))
        
        create_btn.clicked.connect(validate_and_create)
        
        # Focus sur le premier champ
        name_edit.setFocus()
        
        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            pass  # Le projet a été créé avec succès
    
    def _create_project_async(self, name_edit, vessel_edit, company_edit, engineer_edit, 
                             description_edit, base_path_edit, dialog):
        """Création asynchrone du projet"""
        try:
            # Vérifier les champs obligatoires
            required_fields = [
                (name_edit, "Nom du projet"),
                (vessel_edit, "Navire"),
                (company_edit, "Société"),
                (engineer_edit, "Ingénieur responsable")
            ]
            
            missing_fields = []
            for field, label in required_fields:
                if not field.text().strip():
                    missing_fields.append(label)
            
            if missing_fields:
                QMessageBox.warning(dialog, "Champs manquants", 
                                  f"Veuillez remplir les champs obligatoires:\n• " + 
                                  "\n• ".join(missing_fields))
                return
            
            # Valider le nom de projet (pas de caractères spéciaux)
            project_name = name_edit.text().strip()
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
            if any(char in project_name for char in invalid_chars):
                QMessageBox.warning(dialog, "Nom invalide", 
                                  "Le nom du projet ne peut pas contenir les caractères:\n" +
                                  "< > : \" | ? * / \\")
                return
            
            # Créer le projet
            success, result = self.project_manager.create_project(
                name=project_name,
                company=company_edit.text().strip(),
                vessel=vessel_edit.text().strip(),
                engineer=engineer_edit.text().strip(),
                description=description_edit.toPlainText().strip(),
                base_path=base_path_edit.text().strip() if base_path_edit.text().strip() else None
            )
            
            if success:
                QMessageBox.information(dialog, "Projet Créé avec Succès", 
                                      f"✅ Projet créé: {project_name}\n"
                                      f"📁 Emplacement: {result}")
                print(f"✅ Projet créé: {project_name}")
                dialog.accept()
                
                # IMPORTANT: Activer les boutons après création réussie
                self.set_project_loaded(True)
                
                # Rafraîchir l'interface
                self.force_refresh()
            else:
                QMessageBox.critical(dialog, "Erreur de Création", 
                                   f"❌ Impossible de créer le projet:\n{result}")
                print(f"❌ Erreur création: {result}")
                
        except Exception as e:
            QMessageBox.critical(dialog, "Erreur Inattendue", 
                               f"❌ Exception lors de la création:\n{str(e)}")
            print(f"❌ Exception création projet: {e}")

    def open_existing_project(self, file_path=None):
        """Ouvre un projet existant"""
        print("📂 Ouverture de projet")
        
        if not self.project_manager:
            QMessageBox.warning(self, "Indisponible", 
                              "Gestionnaire de projet non disponible")
            return
        
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Ouvrir un projet", os.path.expanduser("~"),
                "Fichiers projet (*.json);;Tous les fichiers (*.*)"
            )
        
        if file_path and os.path.exists(file_path):
            try:
                success, result = self.project_manager.load_project(file_path)
                if success:
                    QMessageBox.information(self, "Succès", 
                                          f"Projet ouvert: {os.path.basename(file_path)}")
                    
                    # IMPORTANT: Activer les boutons après ouverture réussie
                    self.set_project_loaded(True)
                    
                    print(f"✅ Projet ouvert: {file_path}")
                else:
                    QMessageBox.critical(self, "Erreur", f"Échec: {result}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Exception: {e}")

    def save_current_project(self):
        """Sauvegarde le projet actuel"""
        print("💾 Sauvegarde du projet")
        
        if not self.project_manager:
            QMessageBox.warning(self, "Indisponible", "Pas de gestionnaire de projet")
            return
        
        try:
            success, message = self.project_manager.save_current_project()
            if success:
                if self.status_bar and hasattr(self.status_bar, 'show_save_feedback'):
                    self.status_bar.show_save_feedback(True)
                print("✅ Projet sauvegardé")
            else:
                QMessageBox.critical(self, "Erreur", f"Échec sauvegarde: {message}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Exception: {e}")

    def auto_save_project(self):
        """Sauvegarde automatique (logs réduits)"""
        if (self.auto_save_enabled and self.project_manager and 
            self.current_project_data):
            # Utiliser QTimer.singleShot pour éviter les blocages
            QTimer.singleShot(0, self._auto_save_async)
    
    def _auto_save_async(self):
        """Sauvegarde asynchrone du projet"""
        try:
            if (self.auto_save_enabled and self.project_manager and 
                self.current_project_data):
                self.project_manager.save_current_project()
        except Exception as e:
            print(f"❌ Erreur sauvegarde auto: {e}")

    # === CALLBACKS DE PROJET ===

    @pyqtSlot(dict)
    def on_project_loaded(self, project_data):
        """Appelé quand un projet est chargé"""
        print("✅ Projet chargé dans l'interface")
        self.current_project_data = project_data
        
        # IMPORTANT: Activer les boutons après chargement
        self.set_project_loaded(True)
        
        self.refresh_all_data()

    @pyqtSlot(str)
    def on_project_saved(self, file_path):
        """Appelé quand un projet est sauvegardé"""
        # log désactivé

    # === ACTIONS UTILISATEUR ===
    
    def show_detailed_statistics(self):
        """Affiche les statistiques détaillées avec informations de progression"""
        print("📊 Affichage des statistiques")
        
        if not self.current_project_data:
            QMessageBox.warning(self, "Aucun projet", 
                              "Aucun projet chargé pour les statistiques")
            return
        
        # === NOUVEAU : Utiliser ProgressManager si disponible ===
        if hasattr(self, 'progress_manager') and self.progress_manager:
            try:
                all_progress = self.progress_manager.calculate_all_progress(self.app_data)    
                # Créer un dialogue avancé
                dialog = QDialog(self)
                dialog.setWindowTitle("📊 Statistiques Avancées")
                dialog.setModal(True)
                dialog.resize(800, 600)
                
                layout = QVBoxLayout(dialog)
                
                # Onglets pour différents types de stats
                tabs = QTabWidget()
                
                # === Onglet progression détaillée ===
                progress_tab = QTextEdit()
                progress_tab.setReadOnly(True)
                
                progress_text = self.generate_progress_report(all_progress)
                progress_tab.setText(progress_text)
                tabs.addTab(progress_tab, "📈 Progression Détaillée")
                
                # === Onglet prérequis ===
                requirements_tab = QTextEdit()
                requirements_tab.setReadOnly(True)
                
                req_text = self.generate_requirements_report()
                requirements_tab.setText(req_text)
                tabs.addTab(requirements_tab, "📋 Prérequis par Tâche")
                
                # === Onglet statistiques classiques (votre code existant) ===
                classic_tab = QTextEdit()
                classic_tab.setReadOnly(True)
                classic_stats = self.generate_classic_statistics()  # Votre méthode existante
                classic_tab.setText(classic_stats)
                tabs.addTab(classic_tab, "📊 Statistiques Classiques")
                
                layout.addWidget(tabs)
                
                # Boutons
                buttons = QDialogButtonBox(QDialogButtonBox.Close)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.exec_()
                
            except Exception as e:
                print(f"❌ Erreur statistiques avancées: {e}")
                # Fallback vers votre ancien système
                self.show_classic_statistics()
        else:
            # === FALLBACK : Votre ancien système ===
            self.show_classic_statistics()


    def export_project_report(self):
        """Exporte un rapport du projet"""
        print("📄 Export de rapport")
        
        if not self.project_manager or not self.current_project_data:
            QMessageBox.warning(self, "Aucun projet", "Aucun projet à exporter")
            return
        
        # Dialogue simple pour le format
        formats = ["JSON", "Texte", "HTML"]
        format_choice, ok = QInputDialog.getItem(self, "Format d'export", 
                                               "Choisir le format:", formats, 0, False)
        
        if ok:
            # Lancer l'export
            progress = QProgressDialog("Export en cours...", "Annuler", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            self.export_thread = ExportThread(self.project_manager, format_choice.lower())
            self.export_thread.progress_updated.connect(
                lambda val, msg: (progress.setValue(val), progress.setLabelText(msg))
            )
            self.export_thread.export_finished.connect(self.on_export_finished)
            self.export_thread.export_finished.connect(progress.close)
            self.export_thread.start()

    @pyqtSlot(bool, str)
    def on_export_finished(self, success, result):
        """Callback de fin d'export"""
        if success:
            QMessageBox.information(self, "Export Réussi", f"Rapport exporté: {result}")
        else:
            QMessageBox.critical(self, "Erreur Export", f"Échec: {result}")

    def edit_project_info(self):
        """Édite les informations du projet"""
        print("✏️ Édition des informations projet")
        
        if not self.current_project_data:
            QMessageBox.warning(self, "Aucun projet", 
                              "Aucun projet n'est chargé pour être édité.")
            return
        
        # Créer le dialogue d'édition
        dialog = QDialog(self)
        dialog.setWindowTitle("✏️ Éditer les Informations du Projet")
        dialog.setModal(True)
        dialog.resize(500, 450)
        
        layout = QVBoxLayout(dialog)
        
        # Récupérer les métadonnées actuelles
        metadata = self.current_project_data.get('metadata', {})
        
        # === CHAMPS D'ÉDITION ===
        
        # Nom du projet
        layout.addWidget(QLabel("Nom du projet *:"))
        name_edit = QLineEdit(metadata.get('name', ''))
        layout.addWidget(name_edit)
        
        # Navire
        layout.addWidget(QLabel("Navire *:"))
        vessel_edit = QLineEdit(metadata.get('vessel', ''))
        layout.addWidget(vessel_edit)
        
        # Société
        layout.addWidget(QLabel("Société *:"))
        company_edit = QLineEdit(metadata.get('company', ''))
        layout.addWidget(company_edit)
        
        # Ingénieur
        layout.addWidget(QLabel("Ingénieur responsable *:"))
        engineer_edit = QLineEdit(metadata.get('engineer', ''))
        layout.addWidget(engineer_edit)
        
        # Version
        layout.addWidget(QLabel("Version:"))
        version_edit = QLineEdit(metadata.get('version', '1.0'))
        layout.addWidget(version_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(80)
        description_edit.setPlainText(metadata.get('description', ''))
        layout.addWidget(description_edit)
        
        # Informations en lecture seule
        layout.addWidget(QLabel("Informations système:"))
        info_text = QTextEdit()
        info_text.setMaximumHeight(100)
        info_text.setReadOnly(True)
        
        info_content = f"""Créé: {metadata.get('created', 'Non défini')}
Dernière modification: {metadata.get('last_modified', 'Non défini')}
Fichier: {metadata.get('file_path', 'Non sauvegardé')}"""
        
        info_text.setPlainText(info_content)
        layout.addWidget(info_text)
        
        # === BOUTONS ===
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setDefault(True)
        cancel_btn = QPushButton("❌ Annuler")
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)
        
        # === STYLE DU DIALOGUE ===
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                font-weight: bold;
                color: #ffffff;
                margin-top: 8px;
            }
            QLineEdit, QTextEdit {
                background-color: #2d2d30;
                border: 2px solid #3e3e42;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #007acc;
            }
            QTextEdit[readOnly="true"] {
                background-color: #3a3a3a;
                color: #cccccc;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004577;
            }
            QPushButton#cancel {
                background-color: #6c757d;
            }
            QPushButton#cancel:hover {
                background-color: #545b62;
            }
        """)
        
        cancel_btn.setObjectName("cancel")
        
        # === CONNEXIONS ===
        cancel_btn.clicked.connect(dialog.reject)
        
        def save_changes():
            # Vérifier les champs obligatoires
            required_fields = [
                (name_edit, "Nom du projet"),
                (vessel_edit, "Navire"),
                (company_edit, "Société"),
                (engineer_edit, "Ingénieur responsable")
            ]
            
            missing_fields = []
            for field, label in required_fields:
                if not field.text().strip():
                    missing_fields.append(label)
            
            if missing_fields:
                QMessageBox.warning(dialog, "Champs manquants", 
                                  f"Veuillez remplir les champs obligatoires:\n• " + 
                                  "\n• ".join(missing_fields))
                return
            
            # Mettre à jour les métadonnées
            try:
                self.current_project_data['metadata'].update({
                    'name': name_edit.text().strip(),
                    'vessel': vessel_edit.text().strip(),
                    'company': company_edit.text().strip(),
                    'engineer': engineer_edit.text().strip(),
                    'version': version_edit.text().strip() or "1.0",
                    'description': description_edit.toPlainText().strip(),
                    'last_modified': datetime.now().isoformat()
                })
                
                # Sauvegarder via le project manager si disponible
                if self.project_manager:
                    success, message = self.project_manager.save_current_project()
                    if success:
                        QMessageBox.information(dialog, "Modifications Sauvegardées", 
                                              "✅ Les informations du projet ont été mises à jour.")
                        print("✅ Informations projet sauvegardées")
                    else:
                        QMessageBox.warning(dialog, "Erreur de Sauvegarde", 
                                          f"⚠️ Modifications appliquées mais pas sauvegardées:\n{message}")
                else:
                    QMessageBox.information(dialog, "Modifications Appliquées", 
                                          "✅ Les informations ont été mises à jour en mémoire.")
                
                # Rafraîchir l'interface
                self.refresh_all_data()
                
                dialog.accept()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Erreur", 
                                   f"❌ Impossible de sauvegarder les modifications:\n{str(e)}")
                print(f"❌ Erreur sauvegarde édition: {e}")
        
        save_btn.clicked.connect(save_changes)
        
        # Focus sur le premier champ
        name_edit.setFocus()
        
        # Afficher le dialogue
        dialog.exec_()

    def force_refresh(self):
        """Force la mise à jour des données"""
        print("🔄 Actualisation forcée")
        self.refresh_all_data()

    def on_dashboard_segment_clicked(self, segment_name):
        """Gère le clic sur un segment du dashboard"""
        print(f"🎯 Navigation vers: {segment_name}")
        self.module_navigation_requested.emit(segment_name)

    @pyqtSlot(str, float)
    def on_progress_updated(self, module_name: str, progress: float):
        """Gère la mise à jour de progression d'un module"""
        try:
            # Vérifier si la progression a changé avant d'afficher
            if not hasattr(self, '_last_progress'):
                self._last_progress = {}
            
            last_progress = self._last_progress.get(module_name, -1)
            if progress != last_progress:
                # Silencer: ne pas imprimer
                self._last_progress[module_name] = progress
            
            # Mettre à jour le dashboard immédiatement
            self.refresh_dashboard_data()
        except Exception as e:
            print(f"❌ Erreur mise à jour progression: {e}")
    
    @pyqtSlot(str)
    def on_module_completed(self, module_name: str):
        """Gère la completion d'un module"""
        try:
            # Vérifier si le module a déjà été marqué comme terminé
            if not hasattr(self, '_completed_modules'):
                self._completed_modules = set()
            
            if module_name not in self._completed_modules:
                # Silencer: ne pas imprimer
                self._completed_modules.add(module_name)
            
            # Mettre à jour le dashboard
            self.refresh_dashboard_data()
        except Exception as e:
            print(f"❌ Erreur completion module: {e}")
    
    @pyqtSlot(str, bool)
    def on_workflow_step_completed(self, step_name: str, completed: bool):
        """Gère la completion d'une étape de workflow"""
        try:
            print(f"🔄 Étape workflow terminée: {step_name}")
            # Mettre à jour le dashboard immédiatement
            self.refresh_dashboard_data()
        except Exception as e:
            print(f"❌ Erreur workflow step: {e}")
    
    @pyqtSlot(float)
    def on_qc_score_updated(self, score: float):
        """Gère la mise à jour du score QC"""
        try:
            print(f"📈 Score QC mis à jour: {score:.1f}%")
            # Mettre à jour le dashboard
            self.refresh_dashboard_data()
        except Exception as e:
            print(f"❌ Erreur QC score: {e}")
    
    def get_current_project_data(self):
        """Récupère les données actuelles du projet depuis ProjectManager"""
        try:
            if hasattr(self, 'app_data') and self.app_data and hasattr(self, 'project_manager') and self.project_manager:
                # Récupérer les données depuis ProjectManager
                if hasattr(self.project_manager, 'current_project') and self.project_manager.current_project:
                    return self.project_manager.current_project
                
                # Fallback: créer un dict basé sur app_data
                project_data = {
                    'metadata': {
                        'vessel': getattr(self.app_data, 'vessel', 'Projet'),
                        'company': getattr(self.app_data, 'company', ''),
                        'engineer': getattr(self.app_data, 'engineer', ''),
                        'created': getattr(self.app_data, 'created', ''),
                        'last_modified': getattr(self.app_data, 'last_modified', ''),
                        'version': getattr(self.app_data, 'version', '1.0')
                    },
                    'workflow_status': {}  # ProgressManager gère cela
                }
                return project_data
            
            return {'workflow_status': {}}
            
        except Exception as e:
            print(f"❌ Erreur get_current_project_data: {e}")
            return {'workflow_status': {}}
    def refresh_dashboard_data(self):
        """Met à jour le dashboard avec les données actuelles"""
        # Vérifier si les données ont changé avant d'afficher
        if not hasattr(self, '_last_dashboard_refresh'):
            self._last_dashboard_refresh = None
        
        current_time = datetime.now()
        if (self._last_dashboard_refresh and 
            (current_time - self._last_dashboard_refresh).total_seconds() < 2):
            return  # Éviter les rafraîchissements trop fréquents
        
        self._last_dashboard_refresh = current_time
        print("🔄 refresh_dashboard_data() appelée")
        
        try:
            if not self.app_data:
                print("❌ app_data non disponible")
                return
            
            print(f"✅ app_data disponible: {type(self.app_data)}")
            
            # Utiliser ProgressManager si disponible
            if hasattr(self, 'progress_manager') and self.progress_manager:
                print("✅ ProgressManager disponible")
                
                # Calculer la progression via ProgressManager
                all_progress_details = self.progress_manager.calculate_all_progress(self.app_data)
                
                if self.dashboard and hasattr(self.dashboard, 'set_all_progress'):
                    try:
                        # Vérifier que le dashboard JavaScript est prêt
                        if hasattr(self.dashboard, 'page') and self.dashboard.page():
                            self.dashboard.set_all_progress(all_progress_details)
                            print("📊 Dashboard mis à jour via ProgressManager")
                        else:
                            # Afficher le message seulement une fois
                            if not hasattr(self, '_js_not_ready_logged'):
                                print("⚠️ Dashboard JavaScript pas encore prêt, réessai dans 1s")
                                self._js_not_ready_logged = True
                            QTimer.singleShot(1000, self.refresh_dashboard_data)
                    except Exception as e:
                        print(f"❌ Erreur mise à jour dashboard: {e}")
                        # Réessayer dans 1s
                        QTimer.singleShot(1000, self.refresh_dashboard_data)
                
                # Synchroniser ProjectInfoWidget avec les mêmes données
                if hasattr(self, 'project_info') and self.project_info and hasattr(self.project_info, 'update_progress_metrics'):
                    # Passer les vraies données du projet pour que ProgressManager soit utilisé
                    project_data = self.get_current_project_data()
                    self.project_info.update_progress_metrics(project_data)
                    # Afficher le message seulement une fois
                    if not hasattr(self, '_project_info_sync_logged'):
                        print("📊 ProjectInfoWidget synchronisé avec dashboard")
                        self._project_info_sync_logged = True
                    
            else:
                # Fallback avec calcul simple
                progress_data = self.calculate_progress()
                if self.dashboard and hasattr(self.dashboard, 'set_all_progress'):
                    self.dashboard.set_all_progress(progress_data)
                    print("📊 Dashboard mis à jour via calcul simple")
                    
        except Exception as e:
            print(f"❌ Erreur refresh dashboard: {e}")

    def on_module_indicator_clicked(self, module_name):
        """Gère le clic sur un indicateur de module"""
        print(f"🎯 Module sélectionné: {module_name}")
        self.module_navigation_requested.emit(module_name)

    # === MISE À JOUR DES DONNÉES ===

    def refresh_all_data(self):
        """Met à jour toutes les données de l'interface pour le nouveau dashboard."""
        if not self.app_data:
            return
        
        # Protection renforcée contre les appels trop fréquents
        import time
        current_time = time.time()
        if hasattr(self, '_last_refresh_time') and current_time - self._last_refresh_time < 2.0:
            return
        self._last_refresh_time = current_time
        
        # Protection contre les appels simultanés
        if hasattr(self, '_refresh_in_progress') and self._refresh_in_progress:
            return
        self._refresh_in_progress = True
        
        # Utiliser QTimer.singleShot pour éviter les blocages
        QTimer.singleShot(0, self._refresh_async)
    
    def _refresh_async(self):
        """Rafraîchissement asynchrone pour éviter les blocages"""
        try:
            # --- Logique de mise à jour de la progression ---
            if hasattr(self, 'progress_manager') and self.progress_manager:
                self._update_progress_async()
            else:
                # Fallback si ProgressManager n'est pas disponible
                self._update_progress_fallback()
    
            # --- Mise à jour des autres informations de l'interface ---
            # Mettre à jour les informations du projet (cette partie est correcte et reste)
            if (self.project_info and self.current_project_data and
                hasattr(self.project_info, 'update_project_info')):
                self.project_info.update_project_info(self.current_project_data)
    
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour de l'interface: {e}")
        finally:
            # Libérer le verrou
            self._refresh_in_progress = False
    
    def _update_progress_async(self):
        """Met à jour la progression de manière asynchrone"""
        try:
            all_progress_details = self.progress_manager.calculate_all_progress(self.app_data)
            # Mettre à jour le dashboard principal
            if self.dashboard and hasattr(self.dashboard, 'set_all_progress'):
                self.dashboard.set_all_progress(all_progress_details)
    
            # Mettre à jour les autres widgets
            progress_simple = {module: data['progress'] for module, data in all_progress_details.items()}
            if self.status_bar and hasattr(self.status_bar, 'update_module_progress'):
                self.status_bar.update_module_progress(progress_simple)
        except Exception as e:
            print(f"❌ Erreur mise à jour progression async: {e}")
    
    def _update_progress_fallback(self):
        """Met à jour la progression avec le fallback"""
        try:
            progress_data = self.calculate_progress()
            if self.dashboard and hasattr(self.dashboard, 'set_all_progress'):
                self.dashboard.set_all_progress(progress_data)
        except Exception as e:
            print(f"❌ Erreur mise à jour progression fallback: {e}")

    def calculate_progress(self):
        """Calcule la progression de tous les modules"""
        return {
            'DIMCON': self.calculate_dimcon_progress(),
            'GNSS': self.calculate_gnss_progress(),
            'OBSERVATION': self.calculate_observation_progress(),
            'QC': self.calculate_qc_progress()
        }

    def calculate_dimcon_progress(self):
        """Calcule la progression DIMCON"""
        if not hasattr(self.app_data, 'dimcon'):
            return 0
        
        dimcon = self.app_data.dimcon
        required_points = ['Bow', 'Port', 'Stb']
        defined_points = 0
        
        for point in required_points:
            if point in dimcon:
                coords = dimcon[point]
                if any(abs(coords.get(coord, 0)) > 0.001 for coord in ['X', 'Y', 'Z']):
                    defined_points += 1
        
        return (defined_points / len(required_points)) * 100

    def calculate_gnss_progress(self):
        """Calcule la progression GNSS"""
        if not hasattr(self.app_data, 'gnss_data'):
            return 0
        
        gnss = self.app_data.gnss_data
        progress = 0
        
        if gnss.get('base_station'): progress += 30
        if gnss.get('rovers'): progress += 30
        if gnss.get('meridian_convergence', 0) != 0: progress += 20
        if gnss.get('scale_factor', 1) != 1: progress += 20
        
        return min(100, progress)

    def calculate_observation_progress(self):
        """Calcule la progression OBSERVATION"""
        if not hasattr(self.app_data, 'observation_sensors'):
            return 0
        
        sensors = self.app_data.observation_sensors
        if not sensors:
            return 0
        
        configured = sum(1 for s in sensors if s.get('configured', False))
        return (configured / len(sensors)) * 100

    def calculate_qc_progress(self):
        """Calcule la progression QC"""
        if not hasattr(self.app_data, 'qc_metrics'):
            return 0
        
        return self.app_data.qc_metrics.get('global_score', 0)

    def get_status_message(self, progress):
        """Génère le message de statut basé sur la progression"""
        if progress >= 80:
            return f"🟢 PROJET PRÊT ({progress:.0f}%)"
        elif progress >= 60:
            return f"🟡 CONFIGURATION AVANCÉE ({progress:.0f}%)"
        elif progress >= 30:
            return f"🔄 EN CONFIGURATION ({progress:.0f}%)"
        else:
            return f"🔴 INITIALISATION ({progress:.0f}%)"

    # === MÉTHODES PUBLIQUES ===

    def set_app_data(self, app_data):
        """Met à jour les données de l'application"""
        self.app_data = app_data
        project_loaded = app_data is not None
        
        # Informer les widgets
        self.set_project_loaded(project_loaded)
        
        self.refresh_all_data()
        print(f"📊 App data {'définie' if project_loaded else 'supprimée'}")

    def set_project_loaded(self, loaded):
        """Active/désactive les boutons selon l'état du projet"""
        print(f"🔄 Mise à jour état projet: {'chargé' if loaded else 'non chargé'}")
        
        # Informer tous les widgets qui en ont besoin
        widgets_to_update = [
            (self.quick_actions, 'set_project_loaded'),
            (self.status_bar, 'set_project_loaded'),
            (self.project_info, 'enable_edit_button')
        ]
        
        for widget, method_name in widgets_to_update:
            if widget and hasattr(widget, method_name):
                try:
                    getattr(widget, method_name)(loaded)
                    print(f"✅ {widget.__class__.__name__}.{method_name}({loaded})")
                except Exception as e:
                    print(f"❌ Erreur {widget.__class__.__name__}.{method_name}: {e}")

    def get_current_project(self):
        """Retourne les données du projet actuel"""
        return self.current_project_data

    def is_project_loaded(self):
        """Vérifie si un projet est chargé"""
        return self.current_project_data is not None
    
    def on_task_selected(self, module_name, task_id):
        """NOUVELLE MÉTHODE : Gère la sélection d'une tâche spécifique"""
        print(f"🎯 Tâche sélectionnée: {module_name}.{task_id}")
        
        # Afficher les prérequis de la tâche si ProgressManager disponible
        if hasattr(self, 'progress_manager') and self.progress_manager:
            requirements = self.progress_manager.get_task_requirements(module_name, task_id)
            if requirements:
                req_text = "\n• ".join(requirements)
                QMessageBox.information(
                    self, 
                    f"Tâche {task_id}",
                    f"Prérequis pour {module_name}.{task_id}:\n\n• {req_text}"
                )
        
        # Émettre le signal existant pour navigation
        self.module_navigation_requested.emit(module_name)
    def on_progress_updated(self, module, progress):
        """NOUVELLE MÉTHODE : Gestionnaire de mise à jour de progression"""
    # log désactivé pour réduire le bruit
    
    def on_module_completed(self, module):
        """NOUVELLE MÉTHODE : Gestionnaire de module terminé"""
    # log désactivé pour réduire le bruit
        
        # Notification visuelle si possible
        if self.status_bar and hasattr(self.status_bar, 'show_module_completed'):
            self.status_bar.show_module_completed(module)
    def generate_progress_report(self, all_progress):
        """NOUVELLE MÉTHODE : Génère un rapport de progression détaillé"""
        report = "=== RAPPORT DE PROGRESSION DÉTAILLÉ ===\n\n"
        report += f"Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n\n"
        
        total_progress = 0
        total_modules = len(all_progress)
        
        for module_name, module_data in all_progress.items():
            report += f"📋 MODULE {module_name}\n"
            report += "=" * 50 + "\n"
            report += f"Progression globale: {module_data['progress']:.1f}%\n"
            report += f"Statut: {'✅ Terminé' if module_data['completed'] else '🔄 En cours'}\n"
            report += f"Tâches: {module_data['completed_tasks']}/{module_data['total_tasks']}\n\n"
            
            # Détail des tâches
            for task in module_data['tasks']:
                status_icon = "✅" if task['status'] == "validated" else "🔄" if task['status'] == "in_progress" else "❌"
                report += f"  {status_icon} {task['name']}: {task['progress']:.1f}%\n"
                if 'message' in task:
                    report += f"     {task['message']}\n"
            
            report += "\n"
            total_progress += module_data['progress']
        
        # Résumé global
        avg_progress = total_progress / total_modules if total_modules > 0 else 0
        report += f"📊 RÉSUMÉ GLOBAL\n"
        report += "=" * 50 + "\n"
        report += f"Progression moyenne: {avg_progress:.1f}%\n"
        report += f"Modules terminés: {sum(1 for m in all_progress.values() if m['completed'])}/{total_modules}\n"
        
        return report
    
    def generate_requirements_report(self):
        """NOUVELLE MÉTHODE : Génère un rapport des prérequis par tâche"""
        if not hasattr(self, 'progress_manager') or not self.progress_manager:
            return "ProgressManager non disponible"
        
        report = "=== PRÉREQUIS PAR TÂCHE ===\n\n"
        
        for module_name in ['DIMCON', 'GNSS', 'OBSERVATION', 'QC']:
            report += f"📋 {module_name}\n"
            report += "-" * 30 + "\n"
            
            if module_name in self.progress_manager.modules:
                tasks = self.progress_manager.modules[module_name]
                for task in tasks:
                    report += f"\n🔹 {task.name} ({task.id})\n"
                    report += f"   Description: {task.description}\n"
                    report += f"   Poids: {task.weight * 100:.0f}%\n"
                    
                    # Prérequis
                    requirements = self.progress_manager.get_task_requirements(module_name, task.id)
                    if requirements:
                        report += f"   Prérequis:\n"
                        for req in requirements:
                            report += f"     • {req}\n"
                    else:
                        report += f"   Prérequis: Aucun\n"
            
            report += "\n"
        
        return report
    
    def generate_classic_statistics(self):
        """MÉTHODE À GARDER : Votre ancienne méthode de génération de statistiques"""
        # Gardez votre code existant ici
        pass
    
    def show_classic_statistics(self):
        """MÉTHODE À GARDER : Votre ancien dialogue de statistiques"""
        # Gardez votre code existant ici - celui avec StatisticsDialog
        dialog = StatisticsDialog(self.current_project_data, self)
        dialog.exec_()


# === TEST ET LANCEMENT ===

def main():
    """Fonction principale pour tester la page d'accueil"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Créer et configurer la page d'accueil
    widget = HomePageWidget()
    
    # Connecter les signaux de test
    widget.module_navigation_requested.connect(
        lambda module: print(f"🎯 Navigation demandée vers: {module}")
    )
    
    # Configurer la fenêtre
    widget.setWindowTitle("Page d'Accueil - Calibration GNSS")
    widget.resize(1200, 800)
    widget.show()
    
    print("🚀 Page d'accueil démarrée")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())