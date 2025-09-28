# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 21:40:21 2025

@author: a.meunier
"""

# integration_check.py - Script de contrôle pour vérifier l'intégration

import sys
import traceback
from pathlib import Path

def check_integration():
    """Vérifie que l'intégration du nouveau système fonctionne correctement"""
    
    print("🔍 === CONTRÔLE D'INTÉGRATION DU SYSTÈME DE PROGRESSION ===\n")
    
    results = {
        "imports": False,
        "progress_manager": False,
        "dashboard": False,
        "page_accueil": False,
        "validateurs": False,
        "compatibility": False
    }
    
    # === TEST 1: IMPORTS ===
    print("1️⃣  Test des imports...")
    try:
        from progress_manager import ProgressManager, TaskValidator, Task, TaskStatus
        print("   ✅ progress_manager importé")
        
        from app.gui.html_dashboard_widget import HTMLCircularDashboard
        print("   ✅ html_dashboard_widget importé")
        
        from app.gui.page_accueil import HomePageWidget
        print("   ✅ page_accueil importé")
        
        results["imports"] = True
        print("   🎉 Tous les imports réussis\n")
        
    except Exception as e:
        print(f"   ❌ Erreur import: {e}")
        print("   💡 Vérifiez que les fichiers sont dans les bons répertoires\n")
        return results
    
    # === TEST 2: PROGRESS MANAGER ===
    print("2️⃣  Test du ProgressManager...")
    try:
        pm = ProgressManager()
        
        # Vérifier les modules
        expected_modules = ['DIMCON', 'GNSS', 'OBSERVATION', 'QC']
        for module in expected_modules:
            if module in pm.modules:
                tasks_count = len(pm.modules[module])
                print(f"   ✅ Module {module}: {tasks_count} tâches")
            else:
                print(f"   ❌ Module {module} manquant")
                raise Exception(f"Module {module} non trouvé")
        
        # Vérifier les validateurs
        validator_count = len(pm.validators)
        print(f"   ✅ {validator_count} validateurs enregistrés")
        
        results["progress_manager"] = True
        print("   🎉 ProgressManager opérationnel\n")
        
    except Exception as e:
        print(f"   ❌ Erreur ProgressManager: {e}")
        print("   💡 Vérifiez la définition des modules et validateurs\n")
        return results
    
    # === TEST 3: DASHBOARD ===
    print("3️⃣  Test du Dashboard...")
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dashboard = HTMLCircularDashboard()
        
        # Vérifier les nouvelles méthodes
        required_methods = ['update_progress', 'segment_clicked']
        for method in required_methods:
            if hasattr(dashboard, method):
                print(f"   ✅ Méthode {method} présente")
            else:
                print(f"   ❌ Méthode {method} manquante")
                raise Exception(f"Méthode {method} non trouvée")
        
        results["dashboard"] = True
        print("   🎉 Dashboard fonctionnel\n")
        
    except Exception as e:
        print(f"   ❌ Erreur Dashboard: {e}")
        print("   💡 Vérifiez que html_dashboard_widget.py a été mis à jour\n")
        return results
    
    # === TEST 4: PAGE ACCUEIL ===
    print("4️⃣  Test de la Page d'Accueil...")
    try:
        home_page = HomePageWidget()
        
        # Vérifier les nouvelles méthodes
        new_methods = ['on_task_selected', 'on_progress_updated', 'on_module_completed']
        for method in new_methods:
            if hasattr(home_page, method):
                print(f"   ✅ Nouvelle méthode {method} présente")
            else:
                print(f"   ⚠️  Méthode {method} manquante - à ajouter")
        
        # Vérifier l'attribut progress_manager
        if hasattr(home_page, 'progress_manager'):
            if home_page.progress_manager is not None:
                print("   ✅ ProgressManager initialisé dans HomePageWidget")
            else:
                print("   ⚠️  ProgressManager non initialisé (mode compatibilité)")
        else:
            print("   ❌ Attribut progress_manager manquant")
            raise Exception("Attribut progress_manager non trouvé")
        
        results["page_accueil"] = True
        print("   🎉 Page d'accueil compatible\n")
        
    except Exception as e:
        print(f"   ❌ Erreur Page d'Accueil: {e}")
        print("   💡 Vérifiez que les modifications ont été appliquées\n")
        return results
    
    # === TEST 5: VALIDATEURS ===
    print("5️⃣  Test des Validateurs...")
    try:
        # Créer des données de test
        class TestAppData:
            def __init__(self):
                self.dimcon = {
                    'Bow': {'X': 1.0, 'Y': 2.0, 'Z': 3.0},
                    'Port': {'X': 4.0, 'Y': 5.0, 'Z': 6.0},
                    'Stb': {'X': 7.0, 'Y': 8.0, 'Z': 9.0}
                }
                self.gnss_data = {
                    'meridian_convergence': 0.5,
                    'scale_factor': 1.001,
                    'mobile_points': {
                        'mobile_1': {'data': [1, 2, 3]}
                    }
                }
                self.observation_data = {
                    'sensors': {'sensor1': [1, 2, 3]},
                    'calculations': {'calc1': {'statistics': {}}},
                    'sign_conventions': {'sensor1': {'pitch_sign': 1}}
                }
        
        test_data = TestAppData()
        pm = ProgressManager()
        
        # Tester chaque validateur
        validator_tests = [
            ('DimconCoordinatesValidator', 'DIMCON', 'coordinates'),
            ('GnssBaselineValidator', 'GNSS', 'baselines'),
            ('ObservationInstrumentsValidator', 'OBSERVATION', 'instruments')
        ]
        
        for validator_name, module, task_id in validator_tests:
            if validator_name in pm.validators:
                validator = pm.validators[validator_name]
                is_valid, progress, message = validator.validate(test_data)
                print(f"   ✅ {validator_name}: {progress:.1f}% - {message}")
            else:
                print(f"   ❌ Validateur {validator_name} manquant")
        
        # Test de calcul global
        all_progress = pm.calculate_all_progress(test_data)
        print(f"   ✅ Calcul global: {len(all_progress)} modules traités")
        
        results["validateurs"] = True
        print("   🎉 Validateurs opérationnels\n")
        
    except Exception as e:
        print(f"   ❌ Erreur Validateurs: {e}")
        print("   💡 Vérifiez la logique des validateurs\n")
        traceback.print_exc()
        return results
    
    # === TEST 6: COMPATIBILITÉ ===
    print("6️⃣  Test de Compatibilité...")
    try:
        # Simuler l'utilisation normale
        home_page = HomePageWidget()
        
        # Test du système de fallback
        if hasattr(home_page, 'progress_manager') and home_page.progress_manager:
            print("   ✅ Mode avancé activé")
        else:
            print("   ✅ Mode compatibilité activé")
        
        # Vérifier que les méthodes existantes fonctionnent toujours
        old_methods = ['refresh_all_data', 'calculate_progress', 'set_project_loaded']
        for method in old_methods:
            if hasattr(home_page, method):
                print(f"   ✅ Méthode existante {method} préservée")
            else:
                print(f"   ❌ Méthode existante {method} manquante")
                raise Exception(f"Méthode {method} supprimée par erreur")
        
        results["compatibility"] = True
        print("   🎉 Compatibilité assurée\n")
        
    except Exception as e:
        print(f"   ❌ Erreur Compatibilité: {e}")
        print("   💡 Vérifiez que le code existant n'a pas été cassé\n")
        return results
    
    # === RÉSUMÉ ===
    print("📊 === RÉSUMÉ DU CONTRÔLE ===")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASSÉ" if passed else "❌ ÉCHEC"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("🎉 INTÉGRATION RÉUSSIE ! Le système est prêt à être utilisé.")
        print("\n📝 Prochaines étapes:")
        print("   1. Testez l'application complète")
        print("   2. Vérifiez la navigation entre modules")
        print("   3. Testez les actions rapides")
        print("   4. Vérifiez la sauvegarde de projet")
    else:
        print("⚠️  INTÉGRATION PARTIELLE. Corrigez les erreurs avant de continuer.")
        print("\n🔧 Actions recommandées:")
        if not results["imports"]:
            print("   - Vérifiez l'emplacement des fichiers")
        if not results["progress_manager"]:
            print("   - Vérifiez progress_manager.py")
        if not results["dashboard"]:
            print("   - Vérifiez html_dashboard_widget.py")
        if not results["page_accueil"]:
            print("   - Appliquez les modifications à page_accueil.py")
        if not results["validateurs"]:
            print("   - Vérifiez la logique des validateurs")
        if not results["compatibility"]:
            print("   - Vérifiez que le code existant n'a pas été modifié")
    
    return results

def quick_demo():
    """Démonstration rapide du système"""
    print("\n🚀 === DÉMONSTRATION RAPIDE ===")
    
    try:
        from progress_manager import ProgressManager
        
        # Créer des données fictives
        class DemoData:
            def __init__(self):
                self.dimcon = {
                    'Bow': {'X': 1.0, 'Y': 2.0, 'Z': 3.0},
                    'Port': {'X': 4.0, 'Y': 5.0, 'Z': 6.0},
                    'Stb': {'X': 7.0, 'Y': 8.0, 'Z': 9.0}
                }
                self.gnss_data = {'mobile_points': {}, 'meridian_convergence': 0}
                self.observation_data = {'sensors': {}, 'calculations': {}}
        
        demo_data = DemoData()
        pm = ProgressManager()
        
        print("📊 Calcul de progression avec données fictives:")
        all_progress = pm.calculate_all_progress(demo_data)
        
        for module, data in all_progress.items():
            print(f"   {module}: {data['progress']:.1f}% ({data['completed_tasks']}/{data['total_tasks']} tâches)")
            for task in data['tasks']:
                print(f"      └─ {task['name']}: {task['progress']:.1f}%")
        
        print("\n✨ Le système fonctionne correctement !")
        
    except Exception as e:
        print(f"❌ Erreur démo: {e}")

if __name__ == "__main__":
    results = check_integration()
    
    if all(results.values()):
        quick_demo()
    
    print("\n" + "="*60)
    print("🏁 Contrôle terminé. Consultez les résultats ci-dessus.")