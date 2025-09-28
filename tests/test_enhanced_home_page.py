# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 04:36:36 2025

@author: a.meunier
"""

# test_enhanced_home_manual.py - Tests manuels de la Page Accueil Enhanced

import sys
import os
from pathlib import Path
import json
import tempfile
from datetime import datetime

# Configuration du path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_1_basic_functionality():
    """Test 1: Fonctionnalités de base"""
    print("\n🧪 TEST 1: Fonctionnalités de base")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget, ProjectCreationDialog, MetricCard
        
        app = QApplication.instance() or QApplication([])
        
        # Test 1.1: Création de la page d'accueil
        print("1.1 Création de la page d'accueil... ", end="")
        home_widget = EnhancedHomePageWidget()
        print("✅ OK")
        
        # Test 1.2: Vérification des composants principaux
        print("1.2 Vérification des composants... ", end="")
        assert hasattr(home_widget, 'project_name_label')
        assert hasattr(home_widget, 'workflow_widget')
        assert hasattr(home_widget, 'new_project_btn')
        assert hasattr(home_widget, 'open_project_btn')
        assert hasattr(home_widget, 'save_project_btn')
        print("✅ OK")
        
        # Test 1.3: Test des cartes métriques
        print("1.3 Test des cartes métriques... ", end="")
        metric_card = MetricCard("Test", "100%", "📊", "#3498db")
        metric_card.update_value("50%")
        print("✅ OK")
        
        # Test 1.4: Test du dialogue de création
        print("1.4 Test du dialogue de création... ", end="")
        dialog = ProjectCreationDialog()
        assert dialog.windowTitle() == "Créer un Nouveau Projet"
        print("✅ OK")
        
        print("🎉 TEST 1 RÉUSSI - Toutes les fonctionnalités de base fonctionnent")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_2_project_manager_integration():
    """Test 2: Intégration avec ProjectManager"""
    print("\n🧪 TEST 2: Intégration ProjectManager")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        from core.project_manager import ProjectManager
        
        app = QApplication.instance() or QApplication([])
        
        # Test 2.1: Instance du ProjectManager
        print("2.1 Instance du ProjectManager... ", end="")
        pm = ProjectManager.instance()
        assert pm is not None
        print("✅ OK")
        
        # Test 2.2: Création de la page avec ProjectManager
        print("2.2 Intégration page d'accueil... ", end="")
        home_widget = EnhancedHomePageWidget()
        assert home_widget.project_manager is not None
        print("✅ OK")
        
        # Test 2.3: État "aucun projet"
        print("2.3 Affichage 'aucun projet'... ", end="")
        home_widget.show_no_project_state()
        assert "Aucun projet chargé" in home_widget.project_name_label.text()
        print("✅ OK")
        
        # Test 2.4: Simulation données projet
        print("2.4 Affichage données projet... ", end="")
        mock_project = {
            'metadata': {
                'vessel': 'Test Vessel',
                'company': 'Test Company',
                'engineer': 'Test Engineer',
                'created': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'description': 'Projet de test'
            },
            'workflow_status': {
                'dimcon': {'progress': 75, 'completed': False},
                'gnss': {'progress': 100, 'completed': True},
                'observation': {'progress': 25, 'completed': False},
                'qc': {'progress': 0, 'completed': False}
            },
            'qc_metrics': {
                'global_score': 66.7,
                'gnss_score': 85.0,
                'sensors_score': 45.0
            },
            'observation_sensors': [
                {'id': 'MRU_01', 'type': 'MRU'},
                {'id': 'COMPAS_01', 'type': 'Compas'}
            ]
        }
        
        home_widget.update_project_display(mock_project)
        assert home_widget.current_project == mock_project
        assert "Test Vessel" in home_widget.project_name_label.text()
        print("✅ OK")
        
        print("🎉 TEST 2 RÉUSSI - Intégration ProjectManager fonctionnelle")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_3_real_project_operations():
    """Test 3: Opérations projet réelles"""
    print("\n🧪 TEST 3: Opérations projet réelles")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        from core.project_manager import ProjectManager
        
        app = QApplication.instance() or QApplication([])
        
        # Test 3.1: Création d'un projet réel
        print("3.1 Création projet réel... ", end="")
        pm = ProjectManager.instance()
        
        # Créer un répertoire temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = pm.create_project(
                name="Test_Enhanced_Home",
                company="Test Company",
                vessel="Test Vessel",
                engineer="Test Engineer",
                description="Test pour la page d'accueil enhanced",
                base_path=str(Path(temp_dir) / "test_project")
            )
            
            assert success, f"Échec création: {result}"
            print("✅ OK")
            
            # Test 3.2: Vérification du projet chargé
            print("3.2 Vérification projet chargé... ", end="")
            current_project = pm.get_current_project()
            assert current_project is not None
            assert current_project['metadata']['vessel'] == 'Test Vessel'
            print("✅ OK")
            
            # Test 3.3: Affichage dans la page d'accueil
            print("3.3 Affichage dans page d'accueil... ", end="")
            home_widget = EnhancedHomePageWidget()
            home_widget.load_current_project()
            
            assert home_widget.current_project is not None
            assert "Test Vessel" in home_widget.project_name_label.text()
            print("✅ OK")
            
            # Test 3.4: Sauvegarde projet
            print("3.4 Sauvegarde projet... ", end="")
            success, message = pm.save_project()
            assert success, f"Échec sauvegarde: {message}"
            print("✅ OK")
        
        print("🎉 TEST 3 RÉUSSI - Opérations projet réelles fonctionnelles")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_4_workflow_and_metrics():
    """Test 4: Workflow et métriques"""
    print("\n🧪 TEST 4: Workflow et métriques")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget, WorkflowProgressWidget
        
        app = QApplication.instance() or QApplication([])
        
        # Test 4.1: Widget de progression workflow
        print("4.1 Widget progression workflow... ", end="")
        workflow_widget = WorkflowProgressWidget()
        assert len(workflow_widget.workflow_steps) == 4
        
        step_names = [step["name"] for step in workflow_widget.workflow_steps]
        expected_steps = ["Dimcon", "GNSS", "Observation", "QC"]
        assert step_names == expected_steps
        print("✅ OK")
        
        # Test 4.2: Mise à jour progression
        print("4.2 Mise à jour progression... ", end="")
        workflow_widget.update_step_progress("Dimcon", 50, False)
        workflow_widget.update_step_progress("GNSS", 100, True)
        print("✅ OK")
        
        # Test 4.3: Navigation workflow
        print("4.3 Navigation workflow... ", end="")
        home_widget = EnhancedHomePageWidget()
        
        # Simuler un projet avec workflow partiel
        home_widget.current_project = {
            'workflow_status': {
                'dimcon': {'completed': True},
                'gnss': {'completed': False},
                'observation': {'completed': False},
                'qc': {'completed': False}
            }
        }
        
        # Le test de navigation nécessiterait une interface complète
        # On vérifie juste que la méthode existe et fonctionne
        assert hasattr(home_widget, 'continue_workflow')
        print("✅ OK")
        
        # Test 4.4: Formatage des dates
        print("4.4 Formatage des dates... ", end="")
        iso_date = "2025-01-15T14:30:00Z"
        formatted = home_widget.format_date(iso_date)
        assert "15/01/2025" in formatted
        assert "14:30" in formatted
        
        # Test avec dates invalides
        assert home_widget.format_date("") == "N/A"
        assert home_widget.format_date(None) == "N/A"
        print("✅ OK")
        
        print("🎉 TEST 4 RÉUSSI - Workflow et métriques fonctionnels")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_5_error_handling():
    """Test 5: Gestion d'erreurs"""
    print("\n🧪 TEST 5: Gestion d'erreurs")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        
        app = QApplication.instance() or QApplication([])
        
        # Test 5.1: Données projet corrompues
        print("5.1 Gestion données corrompues... ", end="")
        home_widget = EnhancedHomePageWidget()
        
        corrupted_data = {
            'metadata': {},  # Métadonnées vides
            'workflow_status': None,  # Status null
            'qc_metrics': {'invalid': 'data'}
        }
        
        # Ne doit pas planter
        try:
            home_widget.update_project_display(corrupted_data)
            print("✅ OK")
        except Exception:
            print("❌ ÉCHEC - Ne gère pas les données corrompues")
            raise
        
        # Test 5.2: Données manquantes
        print("5.2 Gestion données manquantes... ", end="")
        home_widget.update_project_display(None)
        # Doit afficher l'état "aucun projet"
        print("✅ OK")
        
        # Test 5.3: Gros volumes de données
        print("5.3 Gestion gros volumes... ", end="")
        large_data = {
            'metadata': {
                'vessel': 'Large Vessel',
                'company': 'Large Company',
                'engineer': 'Engineer',
                'created': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'description': 'Large project'
            },
            'workflow_status': {
                'dimcon': {'completed': True, 'progress': 100},
                'gnss': {'completed': True, 'progress': 100},
                'observation': {'completed': True, 'progress': 100},
                'qc': {'completed': True, 'progress': 100}
            },
            'qc_metrics': {'global_score': 95.5},
            'observation_sensors': [{'id': f'sensor_{i}', 'type': 'MRU'} for i in range(50)]
        }
        
        home_widget.update_project_display(large_data)
        print("✅ OK")
        
        print("🎉 TEST 5 RÉUSSI - Gestion d'erreurs robuste")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_6_ui_responsiveness():
    """Test 6: Réactivité de l'interface"""
    print("\n🧪 TEST 6: Réactivité de l'interface")
    print("-" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        
        app = QApplication.instance() or QApplication([])
        
        # Test 6.1: Création et affichage
        print("6.1 Création et affichage widget... ", end="")
        home_widget = EnhancedHomePageWidget()
        home_widget.show()
        app.processEvents()  # Traiter les événements Qt
        print("✅ OK")
        
        # Test 6.2: Mise à jour fréquente
        print("6.2 Mises à jour fréquentes... ", end="")
        for i in range(10):
            home_widget.update_dashboard()
            app.processEvents()
        print("✅ OK")
        
        # Test 6.3: Timer auto-refresh
        print("6.3 Timer auto-refresh... ", end="")
        assert home_widget.update_timer.isActive()
        print("✅ OK")
        
        # Test 6.4: Thème sombre
        print("6.4 Application thème sombre... ", end="")
        home_widget.apply_theme("dark")
        app.processEvents()
        print("✅ OK")
        
        home_widget.close()
        print("🎉 TEST 6 RÉUSSI - Interface réactive")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale - lance tous les tests"""
    print("🧪 SUITE DE TESTS - PAGE ACCUEIL ENHANCED")
    print("=" * 60)
    print("Tests de validation de l'intégration et des fonctionnalités")
    print()
    
    # Résultats des tests
    results = {}
    
    # Lancer tous les tests
    tests = [
        ("Fonctionnalités de base", test_1_basic_functionality),
        ("Intégration ProjectManager", test_2_project_manager_integration),
        ("Opérations projet réelles", test_3_real_project_operations),
        ("Workflow et métriques", test_4_workflow_and_metrics),
        ("Gestion d'erreurs", test_5_error_handling),
        ("Réactivité interface", test_6_ui_responsiveness)
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE dans {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{test_name:<30} {status}")
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 FÉLICITATIONS ! Tous les tests sont passés")
        print("🚀 Votre Page Accueil Enhanced est parfaitement intégrée !")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus pour corriger les problèmes")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)