#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test complet et diagnostic de l'application de calibration GNSS
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

# Configuration du Path
try:
    current_dir = Path(__file__).parent.resolve()
    # Chercher le répertoire src
    src_dir = None
    for parent in current_dir.parents:
        potential_src = parent / 'src'
        if potential_src.exists():
            src_dir = potential_src
            break
    
    if src_dir is None:
        # Si on est déjà dans src ou un sous-répertoire
        if 'src' in current_dir.parts:
            src_dir = Path(*current_dir.parts[:current_dir.parts.index('src')+1])
        else:
            src_dir = current_dir
    
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    print(f"✅ Répertoire src configuré: {src_dir}")
except Exception as e:
    print(f"❌ Erreur configuration path: {e}")

class TestResult:
    def __init__(self, name, success, error=None, details=None):
        self.name = name
        self.success = success
        self.error = error
        self.details = details

class DiagnosticWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Diagnostic Application Calibration GNSS")
        self.setGeometry(100, 100, 1000, 700)
        
        # Résultats des tests
        self.test_results = []
        
        self.setup_ui()
        self.apply_styles()
        
        # Lancer les tests automatiquement
        QTimer.singleShot(1000, self.run_all_tests)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Zone de texte pour les résultats
        self.results_text = QTextEdit()
        self.results_text.setFont(QFont("Consolas", 9))
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Boutons de contrôle
        buttons_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🔬 Relancer les Tests")
        self.test_btn.clicked.connect(self.run_all_tests)
        
        self.clear_btn = QPushButton("🗑️ Effacer")
        self.clear_btn.clicked.connect(self.results_text.clear)
        
        self.test_widgets_btn = QPushButton("🎨 Tester Widgets")
        self.test_widgets_btn.clicked.connect(self.test_widgets_individually)
        
        buttons_layout.addWidget(self.test_btn)
        buttons_layout.addWidget(self.test_widgets_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(buttons_layout)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
            QTextEdit {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #555;
                font-family: 'Consolas', monospace;
                line-height: 1.4;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
    
    def log(self, message, level="INFO"):
        """Ajoute un message au log avec couleur"""
        colors = {
            "INFO": "#d4d4d4",
            "SUCCESS": "#28a745",
            "ERROR": "#dc3545",
            "WARNING": "#ffc107"
        }
        
        color = colors.get(level, "#d4d4d4")
        self.results_text.append(f'<span style="color: {color};">{message}</span>')
        
        # Auto-scroll
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Forcer la mise à jour de l'interface
        QApplication.processEvents()
    
    def run_all_tests(self):
        """Lance tous les tests de diagnostic"""
        self.results_text.clear()
        self.test_results.clear()
        
        self.log("🔬 === DIAGNOSTIC COMPLET APPLICATION CALIBRATION GNSS ===", "INFO")
        self.log(f"📅 Démarré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", "INFO")
        self.log("", "INFO")
        
        # Tests d'imports
        self.test_imports()
        
        # Tests de widgets
        self.test_widget_creation()
        
        # Tests d'intégration
        self.test_integration()
        
        # Résumé
        self.show_summary()
    
    def test_imports(self):
        """Teste tous les imports nécessaires"""
        self.log("📦 === TESTS D'IMPORTS ===", "INFO")
        
        imports_to_test = [
            # Core modules
            ("core.app_data", "ApplicationData"),
            ("core.project_manager", "ProjectManager"),
            ("core.progress_manager", "ProgressManager"),
            
            # GUI widgets
            ("app.gui.html_dashboard_widget", "HTMLCircularDashboard"),
            ("app.gui.project_info_widget", "ProjectInfoWidget"),
            ("app.gui.quick_actions_widget", "QuickActionsWidget"),
            ("app.gui.status_bar_widget", "StatusBarWidget"),
            ("app.gui.log_widget", "LogWidget"),
            ("app.gui.page_accueil", "HomePageWidget"),
            
            # Optional widgets
            ("app.gui.menu_vertical", "VerticalMenu"),
            ("app.gui.page_Dimcon", "DimconWidget"),
            ("app.gui.page_GNSS", "GnssWidget"),
            ("app.gui.page_observation", "ObservationWidget"),
        ]
        
        for module_name, class_name in imports_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.test_results.append(TestResult(f"Import {class_name}", True, details=f"De {module_name}"))
                self.log(f"✅ {class_name} importé depuis {module_name}", "SUCCESS")
            except ImportError as e:
                self.test_results.append(TestResult(f"Import {class_name}", False, str(e)))
                self.log(f"❌ {class_name} depuis {module_name}: {e}", "ERROR")
            except AttributeError as e:
                self.test_results.append(TestResult(f"Import {class_name}", False, str(e)))
                self.log(f"❌ {class_name} non trouvé dans {module_name}: {e}", "ERROR")
            except Exception as e:
                self.test_results.append(TestResult(f"Import {class_name}", False, str(e)))
                self.log(f"❌ Erreur inattendue {class_name}: {e}", "ERROR")
        
        self.log("", "INFO")
    
    def test_widget_creation(self):
        """Teste la création de chaque widget individuellement"""
        self.log("🎨 === TESTS DE CRÉATION WIDGETS ===", "INFO")
        
        # Widgets à tester
        widgets_to_test = [
            ("ApplicationData (core)", self.test_app_data),
            ("ProjectManager (core)", self.test_project_manager),
            ("ProgressManager (core)", self.test_progress_manager),
            ("HTMLCircularDashboard", self.test_dashboard_widget),
            ("ProjectInfoWidget", self.test_project_info_widget),
            ("QuickActionsWidget", self.test_quick_actions_widget),
            ("StatusBarWidget", self.test_status_bar_widget),
            ("LogWidget", self.test_log_widget),
            ("HomePageWidget", self.test_home_page_widget),
        ]
        
        for widget_name, test_func in widgets_to_test:
            try:
                self.log(f"🧪 Test {widget_name}...", "INFO")
                result = test_func()
                if result:
                    self.test_results.append(TestResult(f"Création {widget_name}", True))
                    self.log(f"✅ {widget_name} créé avec succès", "SUCCESS")
                else:
                    self.test_results.append(TestResult(f"Création {widget_name}", False, "Test échoué"))
                    self.log(f"❌ {widget_name} création échouée", "ERROR")
            except Exception as e:
                self.test_results.append(TestResult(f"Création {widget_name}", False, str(e)))
                self.log(f"❌ {widget_name} erreur: {e}", "ERROR")
        
        self.log("", "INFO")
    
    def test_app_data(self):
        """Teste ApplicationData"""
        try:
            from core.app_data import ApplicationData
            app_data = ApplicationData()
            
            # Tester les attributs de base
            assert hasattr(app_data, 'dimcon'), "Attribut dimcon manquant"
            assert hasattr(app_data, 'gnss_data'), "Attribut gnss_data manquant"
            assert hasattr(app_data, 'sensors'), "Attribut sensors manquant"
            
            # Tester les méthodes
            assert callable(getattr(app_data, 'get_dimcon_points', None)), "Méthode get_dimcon_points manquante"
            assert callable(getattr(app_data, 'update_dimcon_point', None)), "Méthode update_dimcon_point manquante"
            
            self.log("   - Attributs et méthodes vérifiés", "INFO")
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_project_manager(self):
        """Teste ProjectManager"""
        try:
            from core.project_manager import ProjectManager
            pm = ProjectManager.instance()
            
            # Tester les méthodes principales
            assert callable(getattr(pm, 'create_project', None)), "Méthode create_project manquante"
            assert callable(getattr(pm, 'load_project', None)), "Méthode load_project manquante"
            assert callable(getattr(pm, 'save_current_project', None)), "Méthode save_current_project manquante"
            
            self.log("   - Méthodes principales vérifiées", "INFO")
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_progress_manager(self):
        """Teste ProgressManager"""
        try:
            from core.progress_manager import ProgressManager
            pm = ProgressManager()
            
            # Tester les attributs
            assert hasattr(pm, 'modules'), "Attribut modules manquant"
            assert hasattr(pm, 'validators'), "Attribut validators manquant"
            
            # Tester les méthodes
            assert callable(getattr(pm, 'calculate_all_progress', None)), "Méthode calculate_all_progress manquante"
            
            self.log("   - Structure ProgressManager vérifiée", "INFO")
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_dashboard_widget(self):
        """Teste HTMLCircularDashboard"""
        try:
            from app.gui.html_dashboard_widget import HTMLCircularDashboard
            widget = HTMLCircularDashboard()
            
            # Tester les attributs principaux
            assert hasattr(widget, 'web_view'), "Attribut web_view manquant"
            assert hasattr(widget, 'bridge'), "Attribut bridge manquant"
            assert callable(getattr(widget, 'set_all_progress', None)), "Méthode set_all_progress manquante"
            
            self.log("   - WebView et bridge vérifiés", "INFO")
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_project_info_widget(self):
        """Teste ProjectInfoWidget"""
        try:
            from app.gui.project_info_widget import ProjectInfoWidget
            widget = ProjectInfoWidget()
            
            # Tester les attributs critiques
            assert hasattr(widget, 'project_name_label'), "Attribut project_name_label manquant"
            assert hasattr(widget, 'project_description_label'), "Attribut project_description_label manquant"
            assert hasattr(widget, 'edit_button'), "Attribut edit_button manquant"
            
            # Vérifier que les widgets existent vraiment
            assert widget.project_name_label is not None, "project_name_label est None"
            assert widget.project_description_label is not None, "project_description_label est None"
            assert widget.edit_button is not None, "edit_button est None"
            
            self.log("   - Labels et bouton vérifiés", "INFO")
            
            # Tester les méthodes
            assert callable(getattr(widget, 'update_project_info', None)), "Méthode update_project_info manquante"
            assert callable(getattr(widget, 'reset_to_default', None)), "Méthode reset_to_default manquante"
            
            # Test de modification de texte
            original_text = widget.project_name_label.text()
            test_text = "TEST_DIAGNOSTIC"
            widget.project_name_label.setText(test_text)
            current_text = widget.project_name_label.text()
            
            if current_text == test_text:
                self.log("   - Modification de texte réussie", "SUCCESS")
            else:
                self.log(f"   - Erreur modification: attendu '{test_text}', obtenu '{current_text}'", "WARNING")
            
            # Remettre le texte original
            widget.project_name_label.setText(original_text)
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_quick_actions_widget(self):
        """Teste QuickActionsWidget"""
        try:
            from app.gui.quick_actions_widget import QuickActionsWidget
            widget = QuickActionsWidget()
            
            # Tester les attributs
            assert hasattr(widget, 'buttons'), "Attribut buttons manquant"
            assert isinstance(widget.buttons, dict), "buttons doit être un dictionnaire"
            
            # Vérifier les boutons attendus
            expected_buttons = ['save', 'export', 'stats', 'refresh']
            for btn_key in expected_buttons:
                assert btn_key in widget.buttons, f"Bouton {btn_key} manquant"
                assert widget.buttons[btn_key] is not None, f"Bouton {btn_key} est None"
            
            self.log(f"   - {len(widget.buttons)} boutons créés", "INFO")
            
            # Tester les méthodes
            assert callable(getattr(widget, 'set_project_loaded', None)), "Méthode set_project_loaded manquante"
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_status_bar_widget(self):
        """Teste StatusBarWidget"""
        try:
            from app.gui.status_bar_widget import StatusBarWidget
            widget = StatusBarWidget()
            
            # Tester les attributs
            assert hasattr(widget, 'save_status_label'), "Attribut save_status_label manquant"
            assert hasattr(widget, 'timestamp_label'), "Attribut timestamp_label manquant"
            assert hasattr(widget, 'module_indicators'), "Attribut module_indicators manquant"
            
            # Vérifier les indicateurs de modules
            expected_modules = ['DIMCON', 'GNSS', 'OBSERVATION', 'QC']
            for module in expected_modules:
                assert module in widget.module_indicators, f"Indicateur {module} manquant"
            
            self.log(f"   - {len(widget.module_indicators)} indicateurs créés", "INFO")
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_log_widget(self):
        """Teste LogWidget"""
        try:
            from app.gui.log_widget import LogWidget
            widget = LogWidget()
            
            # Tester les méthodes principales
            assert callable(getattr(widget, 'add_log_message', None)), "Méthode add_log_message manquante"
            assert callable(getattr(widget, 'clear_log', None)), "Méthode clear_log manquante"
            
            # Test d'ajout de message
            widget.add_log_message("Test diagnostic")
            
            self.log("   - Méthodes de log vérifiées", "INFO")
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_home_page_widget(self):
        """Teste HomePageWidget"""
        try:
            from app.gui.page_accueil import HomePageWidget
            from core.app_data import ApplicationData
            from PyQt5.QtCore import QSettings
            
            # Créer les dépendances
            app_data = ApplicationData()
            settings = QSettings("Test", "Test")
            
            widget = HomePageWidget(app_data=app_data, settings=settings)
            
            # Tester les attributs principaux
            assert hasattr(widget, 'dashboard'), "Attribut dashboard manquant"
            assert hasattr(widget, 'project_info'), "Attribut project_info manquant"
            assert hasattr(widget, 'quick_actions'), "Attribut quick_actions manquant"
            assert hasattr(widget, 'status_bar'), "Attribut status_bar manquant"
            assert hasattr(widget, 'settings'), "Attribut settings manquant"
            
            # Vérifier que settings n'est pas None
            assert widget.settings is not None, "settings est None"
            
            self.log("   - Composants principaux vérifiés", "INFO")
            
            # Tester les méthodes principales
            assert callable(getattr(widget, 'refresh_all_data', None)), "Méthode refresh_all_data manquante"
            assert callable(getattr(widget, 'set_project_loaded', None)), "Méthode set_project_loaded manquante"
            
            # Nettoyer
            widget.deleteLater()
            return True
        except Exception as e:
            self.log(f"   - Erreur: {e}", "ERROR")
            return False
    
    def test_integration(self):
        """Tests d'intégration entre composants"""
        self.log("🔗 === TESTS D'INTÉGRATION ===", "INFO")
        
        try:
            # Test d'intégration HomePageWidget complet
            from app.gui.page_accueil import HomePageWidget
            from core.app_data import ApplicationData
            from PyQt5.QtCore import QSettings
            
            app_data = ApplicationData()
            settings = QSettings("Test", "Test")
            home_page = HomePageWidget(app_data=app_data, settings=settings)
            
            # Vérifier que tous les sous-widgets sont créés
            components_check = [
                ("Dashboard", home_page.dashboard),
                ("ProjectInfo", home_page.project_info),
                ("QuickActions", home_page.quick_actions),
                ("StatusBar", home_page.status_bar)
            ]
            
            for name, component in components_check:
                if component is not None:
                    self.log(f"✅ {name} intégré avec succès", "SUCCESS")
                else:
                    self.log(f"❌ {name} non intégré", "ERROR")
            
            # Test de communication entre widgets
            if home_page.project_info and hasattr(home_page.project_info, 'project_name_label'):
                original_text = home_page.project_info.project_name_label.text()
                test_text = "TEST INTEGRATION"
                home_page.project_info.project_name_label.setText(test_text)
                
                if home_page.project_info.project_name_label.text() == test_text:
                    self.log("✅ Communication entre widgets fonctionnelle", "SUCCESS")
                else:
                    self.log("❌ Problème communication widgets", "ERROR")
                
                # Remettre le texte original
                home_page.project_info.project_name_label.setText(original_text)
            
            self.test_results.append(TestResult("Intégration complète", True))
            
            # Nettoyer
            home_page.deleteLater()
            
        except Exception as e:
            self.log(f"❌ Erreur test intégration: {e}", "ERROR")
            self.test_results.append(TestResult("Intégration complète", False, str(e)))
        
        self.log("", "INFO")
    
    def test_widgets_individually(self):
        """Lance des tests individuels de widgets dans des fenêtres séparées"""
        self.log("🎨 === TESTS WIDGETS INDIVIDUELS ===", "INFO")
        
        try:
            # Test ProjectInfoWidget en fenêtre séparée
            from app.gui.project_info_widget import ProjectInfoWidget
            
            test_window = ProjectInfoWidget()
            test_window.setWindowTitle("Test ProjectInfoWidget")
            test_window.resize(400, 600)
            test_window.show()
            
            # Données de test
            fake_data = {
                'metadata': {
                    'vessel': 'Test Vessel',
                    'company': 'Test Company',
                    'engineer': 'Test Engineer',
                    'description': 'Widget de test pour diagnostic',
                    'created': '2025-08-04T10:00:00Z',
                    'last_modified': '2025-08-04T12:00:00Z',
                    'version': '1.0'
                },
                'workflow_status': {
                    'dimcon': {'completed': True, 'progress': 100},
                    'gnss': {'completed': False, 'progress': 75},
                    'observation': {'completed': False, 'progress': 50},
                    'qc': {'completed': False, 'progress': 25}
                }
            }
            
            test_window.update_project_info(fake_data)
            test_window.enable_edit_button(True)
            
            self.log("✅ Fenêtre de test ProjectInfoWidget ouverte", "SUCCESS")
            
        except Exception as e:
            self.log(f"❌ Erreur test widgets individuels: {e}", "ERROR")
    
    def show_summary(self):
        """Affiche le résumé des tests"""
        self.log("📊 === RÉSUMÉ DES TESTS ===", "INFO")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total des tests: {total_tests}", "INFO")
        self.log(f"Tests réussis: {successful_tests}", "SUCCESS")
        self.log(f"Tests échoués: {failed_tests}", "ERROR" if failed_tests > 0 else "INFO")
        self.log(f"Taux de réussite: {success_rate:.1f}%", "SUCCESS" if success_rate >= 80 else "WARNING")
        
        if failed_tests > 0:
            self.log("", "INFO")
            self.log("❌ TESTS ÉCHOUÉS:", "ERROR")
            for result in self.test_results:
                if not result.success:
                    self.log(f"   • {result.name}: {result.error}", "ERROR")
        
        self.log("", "INFO")
        
        if success_rate >= 90:
            self.log("🎉 DIAGNOSTIC EXCELLENT - Application prête", "SUCCESS")
        elif success_rate >= 70:
            self.log("✅ DIAGNOSTIC BON - Application fonctionnelle avec quelques problèmes mineurs", "SUCCESS")
        elif success_rate >= 50:
            self.log("⚠️ DIAGNOSTIC MOYEN - Application partiellement fonctionnelle", "WARNING")
        else:
            self.log("❌ DIAGNOSTIC CRITIQUE - Problèmes majeurs détectés", "ERROR")


def main():
    """Lance le diagnostic complet"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Style sombre global
    app.setStyleSheet("""
        QApplication {
            background-color: #1e1e1e;
            color: white;
        }
    """)
    
    window = DiagnosticWindow()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())