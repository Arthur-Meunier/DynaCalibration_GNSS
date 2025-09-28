# setup_reports_system.py
# Script d'installation et configuration du système de rapports

import os
import sys
import subprocess
from pathlib import Path
import json

def check_and_install_dependencies():
    """Vérifie et installe les dépendances requises"""
    print("🔍 Vérification des dépendances...")
    
    required_packages = [
        'reportlab',
        'matplotlib', 
        'pillow',  # Pour le traitement d'images
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MANQUANT")
    
    if missing_packages:
        print(f"\n📦 Installation des packages manquants: {', '.join(missing_packages)}")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installé")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur installation {package}: {e}")
                return False
    
    print("🎉 Toutes les dépendances sont installées !")
    return True

def create_directory_structure(base_path):
    """Crée la structure de répertoires pour le système"""
    print("📁 Création de la structure de répertoires...")
    
    directories = [
        "core/reports",
        "core/logs", 
        "logs",
        "reports/output",
        "reports/templates",
        "reports/assets"
    ]
    
    base = Path(base_path)
    
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ {full_path}")
    
    # Créer les fichiers __init__.py
    init_files = [
        "core/__init__.py",
        "core/reports/__init__.py", 
        "core/logs/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = base / init_file
        if not init_path.exists():
            init_path.touch()
            print(f"✅ {init_path}")

def create_config_file(base_path):
    """Crée le fichier de configuration par défaut"""
    print("⚙️ Création du fichier de configuration...")
    
    config = {
        "reports": {
            "output_directory": "reports/output",
            "templates_directory": "reports/templates", 
            "assets_directory": "reports/assets",
            "default_format": "PDF",
            "default_style": "professional",
            "auto_open_after_generation": True,
            "include_charts_by_default": True,
            "include_logs_by_default": True,
            "max_log_entries_in_report": 100
        },
        "logging": {
            "base_directory": "logs",
            "max_memory_cache": 1000,
            "auto_archive_days": 30,
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "session_timeout_minutes": 60
        },
        "company": {
            "default_name": "Société de Calibration",
            "default_address": "",
            "default_phone": "",
            "default_email": "",
            "default_website": "",
            "logo_path": ""
        },
        "advanced": {
            "pdf_compression": True,
            "image_dpi": 150,
            "chart_size_inches": [8, 6],
            "parallel_generation": False
        }
    }
    
    config_path = Path(base_path) / "config" / "reports_config.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuration créée: {config_path}")
    return config_path

def create_example_usage(base_path):
    """Crée des exemples d'utilisation"""
    print("📝 Création des exemples d'utilisation...")
    
    example_code = '''# exemple_utilisation_rapports.py
"""
Exemples d'utilisation du système de rapports
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def exemple_rapport_simple():
    """Exemple de génération d'un rapport simple"""
    from core.reports.report_generator import generate_quick_report
    from core.project_manager import ProjectManager
    
    # Charger un projet
    pm = ProjectManager.instance()
    
    # Générer un rapport rapide
    success = generate_quick_report(
        pm, 
        "rapport_exemple.pdf", 
        "complete"
    )
    
    if success:
        print("✅ Rapport généré: rapport_exemple.pdf")
    else:
        print("❌ Erreur génération rapport")

def exemple_rapport_personnalise():
    """Exemple de rapport avec configuration personnalisée"""
    from core.reports.report_generator import ReportGenerator, ReportConfig, ReportData
    from core.project_manager import ProjectManager
    from core.logs.log_manager import get_log_manager
    
    # Configuration personnalisée
    config = ReportConfig(
        template_type="complete",
        include_charts=True,
        include_logs=True,
        include_matrices=True,
        chart_style="professional",
        company_info={
            'name': 'Ma Société de Calibration',
            'address': '123 Rue de la Navigation, 75001 Paris',
            'phone': '+33 1 23 45 67 89',
            'email': 'contact@calibration.fr'
        }
    )
    
    # Récupérer les données du projet
    pm = ProjectManager.instance()
    current_project = pm.get_current_project()
    
    if not current_project:
        print("❌ Aucun projet chargé")
        return
    
    # Récupérer les logs
    log_manager = get_log_manager()
    logs_data = log_manager.export_logs_for_report() if log_manager else []
    
    # Préparer les données du rapport
    report_data = ReportData(
        project_metadata=current_project.get('metadata', {}),
        workflow_status=current_project.get('workflow_status', {}),
        qc_metrics=current_project.get('qc_metrics', {}),
        sensor_data=current_project.get('observation_sensors', []),
        calculation_results=current_project.get('calculations', {}),
        logs_summary=logs_data
    )
    
    # Générer le rapport
    generator = ReportGenerator(config)
    success = generator.generate_complete_report(
        report_data, 
        "rapport_personnalise.pdf"
    )
    
    if success:
        print("✅ Rapport personnalisé généré: rapport_personnalise.pdf")
    else:
        print("❌ Erreur génération rapport personnalisé")

def exemple_logs():
    """Exemple d'utilisation du système de logs"""
    from core.logs.log_manager import get_log_manager, log_info, log_user_action
    
    # Récupérer le log manager
    log_manager = get_log_manager()
    
    # Démarrer une session pour un projet
    session_id = log_manager.start_project_session("mon_projet_test")
    print(f"Session démarrée: {session_id}")
    
    # Logger des événements
    log_info("Début des opérations de test")
    log_user_action("Test système rapports", {"module": "exemple"})
    
    # Récupérer les logs récents
    recent_logs = log_manager.get_recent_logs(count=10)
    print(f"Logs récents: {len(recent_logs)} entrées")
    
    # Statistiques
    stats = log_manager.get_log_statistics()
    print(f"Statistiques: {stats}")
    
    # Terminer la session
    log_manager.end_current_session()

if __name__ == "__main__":
    print("🧪 Tests du système de rapports")
    print("=" * 50)
    
    print("\\n1️⃣ Test rapport simple")
    try:
        exemple_rapport_simple()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\\n2️⃣ Test rapport personnalisé")
    try:
        exemple_rapport_personnalise()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\\n3️⃣ Test système de logs")
    try:
        exemple_logs()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\\n✅ Tests terminés")
'''
    
    example_path = Path(base_path) / "exemple_utilisation_rapports.py"
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print(f"✅ Exemple créé: {example_path}")

def integrate_with_main_app(base_path):
    """Crée le code d'intégration avec l'application principale"""
    print("🔗 Création du code d'intégration...")
    
    integration_code = '''# integration_rapports_main.py
"""
Code d'intégration du système de rapports avec l'application principale
À ajouter dans main.py
"""

def integrate_reports_system():
    """Intègre le système de rapports dans l'application"""
    
    # 1. Initialiser le système de logs
    from core.logs.log_manager import init_log_manager
    
    # Initialiser avec le répertoire de logs du projet
    log_manager = init_log_manager("logs")
    print("[OK] Système de logs initialisé")
    
    # 2. Intégrer avec la Page Accueil Enhanced
    def enhance_home_page(home_widget, project_manager):
        """Améliore la page d'accueil avec les fonctionnalités de rapports"""
        from app.gui.reports_integration import add_reports_section_to_home, setup_logging_for_project
        
        # Ajouter les fonctionnalités de rapports
        add_reports_section_to_home(home_widget)
        
        # Configurer les logs pour le projet
        setup_logging_for_project(project_manager)
        
        print("[OK] Page d'accueil améliorée avec système de rapports")
    
    return enhance_home_page

# Exemple d'utilisation dans MainWindow.__init__()
def exemple_integration_main_window():
    """
    Exemple d'intégration dans la classe MainWindow
    """
    
    # Dans MainWindow.__init__(), après la création de la page d'accueil :
    
    # Intégrer le système de rapports
    enhance_home_page = integrate_reports_system()
    
    # Améliorer la page d'accueil
    enhance_home_page(self.page_home, self.project_manager)
    
    # Démarrer une session de logs pour l'application
    from core.logs.log_manager import get_log_manager, log_info
    
    log_manager = get_log_manager()
    log_manager.start_project_session("application_session")
    log_info("Application démarrée", module="main", user_action=True)

# Code à ajouter dans MainWindow.closeEvent()
def exemple_fermeture_application():
    """Code à ajouter lors de la fermeture de l'application"""
    
    from core.logs.log_manager import get_log_manager, log_info
    
    log_manager = get_log_manager()
    if log_manager:
        log_info("Fermeture application", module="main", user_action=True)
        log_manager.end_current_session()
'''
    
    integration_path = Path(base_path) / "integration_rapports_main.py"
    with open(integration_path, 'w', encoding='utf-8') as f:
        f.write(integration_code)
    
    print(f"✅ Intégration créée: {integration_path}")

def create_quick_test():
    """Crée un test rapide du système"""
    print("🧪 Création du test rapide...")
    
    test_code = '''# test_rapide_rapports.py
"""
Test rapide du système de rapports - Version autonome
"""

import sys
from pathlib import Path
import tempfile

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_import_modules():
    """Test d'import des modules"""
    print("📦 Test imports...")
    
    try:
        from core.reports.report_generator import ReportGenerator, ReportConfig, ReportData
        print("✅ report_generator")
    except ImportError as e:
        print(f"❌ report_generator: {e}")
        return False
    
    try:
        from core.logs.log_manager import ProjectLogManager, get_log_manager
        print("✅ log_manager")
    except ImportError as e:
        print(f"❌ log_manager: {e}")
        return False
    
    try:
        import reportlab
        print("✅ reportlab")
    except ImportError as e:
        print(f"❌ reportlab: {e}")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib")
    except ImportError as e:
        print(f"❌ matplotlib: {e}")
        return False
    
    return True

def test_report_generation():
    """Test de génération de rapport"""
    print("\\n📄 Test génération rapport...")
    
    try:
        from core.reports.report_generator import ReportGenerator, ReportConfig, ReportData
        
        # Données de test
        test_project_data = {
            'metadata': {
                'vessel': 'Navire Test',
                'company': 'Société Test',
                'engineer': 'Ingénieur Test',
                'created': '2025-01-15T10:00:00Z',
                'last_modified': '2025-01-15T15:30:00Z',
                'description': 'Projet de test pour le système de rapports'
            },
            'workflow_status': {
                'dimcon': {'progress': 100, 'completed': True},
                'gnss': {'progress': 75, 'completed': False},
                'observation': {'progress': 50, 'completed': False},
                'qc': {'progress': 0, 'completed': False}
            },
            'qc_metrics': {
                'global_score': 62.5,
                'gnss_score': 85.0,
                'sensors_score': 40.0
            },
            'observation_sensors': [
                {'id': 'MRU_Test', 'type': 'MRU'},
                {'id': 'Compas_Test', 'type': 'Compas'}
            ]
        }
        
        # Préparer les données du rapport
        report_data = ReportData(
            project_metadata=test_project_data['metadata'],
            workflow_status=test_project_data['workflow_status'],
            qc_metrics=test_project_data['qc_metrics'],
            sensor_data=test_project_data['observation_sensors']
        )
        
        # Configuration
        config = ReportConfig(
            template_type="complete",
            include_charts=False,  # Désactiver pour éviter les dépendances matplotlib
            include_logs=False
        )
        
        # Générer le rapport
        generator = ReportGenerator(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            success = generator.generate_complete_report(report_data, tmp_file.name)
            
            if success:
                print(f"✅ Rapport généré: {tmp_file.name}")
                
                # Vérifier que le fichier existe et a une taille > 0
                tmp_path = Path(tmp_file.name)
                if tmp_path.exists() and tmp_path.stat().st_size > 0:
                    print(f"✅ Fichier valide: {tmp_path.stat().st_size} bytes")
                    return True
                else:
                    print("❌ Fichier invalide ou vide")
                    return False
            else:
                print("❌ Échec génération rapport")
                return False
    
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_log_system():
    """Test du système de logs"""
    print("\\n📝 Test système de logs...")
    
    try:
        from core.logs.log_manager import ProjectLogManager, get_log_manager
        
        # Initialiser avec répertoire temporaire
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_manager = ProjectLogManager(tmp_dir)
            
            # Démarrer une session
            session_id = log_manager.start_project_session("test_project")
            print(f"✅ Session créée: {session_id}")
            
            # Ajouter des logs
            log_manager.log_info("Test message INFO")
            log_manager.log_warning("Test message WARNING")
            log_manager.log_user_action("Test action utilisateur", {"test": True})
            
            # Récupérer les logs
            recent_logs = log_manager.get_recent_logs(count=10)
            print(f"✅ Logs récupérés: {len(recent_logs)} entrées")
            
            # Statistiques
            stats = log_manager.get_log_statistics()
            print(f"✅ Statistiques: {stats.get('total_logs', 0)} logs")
            
            # Terminer la session
            log_manager.end_current_session()
            print("✅ Session terminée")
            
            return True
    
    except Exception as e:
        print(f"❌ Erreur logs: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🧪 TEST RAPIDE - SYSTÈME DE RAPPORTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports modules", test_import_modules()))
    
    # Test 2: Génération rapport
    results.append(("Génération rapport", test_report_generation()))
    
    # Test 3: Système logs
    results.append(("Système logs", test_log_system()))
    
    # Résultats
    print("\\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{len(results)} tests réussis")
    
    if passed == len(results):
        print("\\n🎉 Tous les tests sont passés !")
        print("🚀 Le système de rapports est opérationnel !")
    else:
        print(f"\\n⚠️ {len(results) - passed} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
'''
    
    test_path = Path("test_rapide_rapports.py")
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print(f"✅ Test créé: {test_path}")

def main():
    """Fonction principale d'installation"""
    print("🚀 INSTALLATION SYSTÈME DE RAPPORTS")
    print("=" * 60)
    print("Installation et configuration du système de logs/rapports")
    print("pour l'application de calibration")
    print()
    
    # Détecter le répertoire de base
    base_path = Path.cwd()
    if (base_path / "src").exists():
        src_path = base_path / "src"
    else:
        src_path = base_path
    
    print(f"📁 Répertoire de base: {base_path}")
    print(f"📁 Répertoire src: {src_path}")
    print()
    
    # Étapes d'installation
    steps = [
        ("Vérification dépendances", lambda: check_and_install_dependencies()),
        ("Structure répertoires", lambda: create_directory_structure(src_path)),
        ("Fichier configuration", lambda: create_config_file(base_path)),
        ("Exemples d'utilisation", lambda: create_example_usage(base_path)),
        ("Code d'intégration", lambda: integrate_with_main_app(base_path)),
        ("Test rapide", lambda: create_quick_test())
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"\\n⚙️ {step_name}...")
        try:
            result = step_func()
            if result is False:
                print(f"❌ Échec: {step_name}")
                results.append((step_name, False))
            else:
                print(f"✅ Terminé: {step_name}")
                results.append((step_name, True))
        except Exception as e:
            print(f"❌ Erreur {step_name}: {e}")
            results.append((step_name, False))
    
    # Résumé final
    print("\\n" + "=" * 60)
    print("📊 RÉSUMÉ INSTALLATION")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for step_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{step_name:<25} {status}")
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} étapes réussies")
    
    if passed == total:
        print("\\n🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !")
        print("\\n📋 PROCHAINES ÉTAPES:")
        print("1. Testez le système: python test_rapide_rapports.py")
        print("2. Intégrez dans main.py (voir integration_rapports_main.py)")
        print("3. Personnalisez config/reports_config.json")
        print("4. Ajoutez vos templates dans reports/templates/")
        print("\\n🚀 Le système de rapports est prêt à l'emploi !")
        
    else:
        print(f"\\n⚠️ {total - passed} étape(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus et relancez l'installation")
        print("💡 Assurez-vous d'avoir les droits d'écriture dans le répertoire")

if __name__ == "__main__":
    main()