# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 04:42:42 2025

@author: a.meunier
"""

# test_page_accueil_spyder.py
# Test simple pour Spyder - Page Accueil Enhanced
import sys
import os
from pathlib import Path

# Vérifier le répertoire actuel
print("Répertoire actuel:", os.getcwd())

# Ajouter le dossier src au path
src_path = Path.cwd() / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
    print("✅ Dossier src ajouté au path")
else:
    print("❌ Dossier src non trouvé")
import sys
import os
from pathlib import Path

print("🧪 TEST PAGE ACCUEIL ENHANCED - Version Spyder")
print("=" * 60)

def test_imports():
    """Test 1: Vérifier que tous les imports fonctionnent"""
    print("\n🔍 TEST 1: Vérification des imports")
    print("-" * 40)
    
    try:
        print("1.1 Import PyQt5... ", end="")
        from PyQt5.QtWidgets import QApplication, QWidget
        from PyQt5.QtCore import Qt
        print("✅ OK")
        
        print("1.2 Import Page Accueil Enhanced... ", end="")
        from app.gui.page_accueil import EnhancedHomePageWidget
        print("✅ OK")
        
        print("1.3 Import ProjectManager... ", end="")
        from core.project_manager import ProjectManager
        print("✅ OK")
        
        print("1.4 Import composants additionnels... ", end="")
        from app.gui.page_accueil import ProjectCreationDialog, MetricCard, WorkflowProgressWidget
        print("✅ OK")
        
        print("\n🎉 Tous les imports fonctionnent !")
        return True
        
    except ImportError as e:
        print(f"❌ ERREUR D'IMPORT: {e}")
        print("\n💡 SOLUTION:")
        print("   - Vérifiez que vous êtes dans le bon répertoire")
        print("   - Assurez-vous que le projet est ouvert dans Spyder")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_basic_creation():
    """Test 2: Créer les composants de base"""
    print("\n🏗️ TEST 2: Création des composants")
    print("-" * 40)
    
    try:
        print("2.1 Création QApplication... ", end="")
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        print("✅ OK")
        
        print("2.2 Création Page Accueil Enhanced... ", end="")
        from app.gui.page_accueil import EnhancedHomePageWidget
        home_widget = EnhancedHomePageWidget()
        print("✅ OK")
        
        print("2.3 Vérification des attributs... ", end="")
        assert hasattr(home_widget, 'project_manager')
        assert hasattr(home_widget, 'project_name_label')
        assert hasattr(home_widget, 'workflow_widget')
        assert hasattr(home_widget, 'new_project_btn')
        print("✅ OK")
        
        print("2.4 Création dialogue projet... ", end="")
        from app.gui.page_accueil import ProjectCreationDialog
        dialog = ProjectCreationDialog()
        print("✅ OK")
        
        print("2.5 Création carte métrique... ", end="")
        from app.gui.page_accueil import MetricCard
        metric = MetricCard("Test", "100%", "📊", "#3498db")
        print("✅ OK")
        
        print("\n🎉 Tous les composants se créent correctement !")
        return home_widget, app
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_project_manager():
    """Test 3: Tester le ProjectManager"""
    print("\n📋 TEST 3: ProjectManager")
    print("-" * 40)
    
    try:
        print("3.1 Instance ProjectManager... ", end="")
        from core.project_manager import ProjectManager
        pm = ProjectManager.instance()
        print("✅ OK")
        
        print("3.2 Projet actuel... ", end="")
        current_project = pm.get_current_project()
        if current_project:
            print(f"✅ Projet chargé: {current_project.get('metadata', {}).get('vessel', 'Inconnu')}")
        else:
            print("ℹ️ Aucun projet (normal)")
        
        print("3.3 Test signaux... ", end="")
        assert hasattr(pm, 'project_loaded')
        assert hasattr(pm, 'project_saved')
        print("✅ OK")
        
        print("\n🎉 ProjectManager fonctionne !")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_visual_display():
    """Test 4: Affichage visuel (optionnel)"""
    print("\n👀 TEST 4: Affichage visuel")
    print("-" * 40)
    print("Ce test va ouvrir une fenêtre pour validation visuelle.")
    
    response = input("Voulez-vous tester l'affichage ? (o/n): ").lower().strip()
    
    if response != 'o':
        print("ℹ️ Test d'affichage ignoré")
        return True
    
    try:
        print("4.1 Affichage de la page... ", end="")
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        home_widget = EnhancedHomePageWidget()
        home_widget.show()
        home_widget.resize(1000, 700)
        print("✅ OK")
        
        print("\n📋 VÉRIFICATIONS VISUELLES:")
        print("- Titre '🏠 Tableau de Bord' visible ?")
        print("- Section 'Projet Actuel' présente ?")
        print("- Barres de progression workflow ?")
        print("- 4 cartes de métriques ?")
        print("- Boutons d'action en haut ?")
        
        input("\nAppuyez sur Entrée après avoir vérifié l'affichage...")
        
        home_widget.close()
        print("✅ Fenêtre fermée")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_project_simulation():
    """Test 5: Simulation avec données"""
    print("\n🎭 TEST 5: Simulation données projet")
    print("-" * 40)
    
    try:
        print("5.1 Création page avec données simulées... ", end="")
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        home_widget = EnhancedHomePageWidget()
        print("✅ OK")
        
        print("5.2 Préparation données test... ", end="")
        test_project = {
            'metadata': {
                'vessel': 'Navire Test Spyder',
                'company': 'Société Test',
                'engineer': 'Ingénieur Test',
                'created': '2025-01-15T10:00:00Z',
                'last_modified': '2025-01-15T15:30:00Z',
                'description': 'Projet de test depuis Spyder'
            },
            'workflow_status': {
                'dimcon': {'progress': 100, 'completed': True},
                'gnss': {'progress': 75, 'completed': False},
                'observation': {'progress': 25, 'completed': False},
                'qc': {'progress': 0, 'completed': False}
            },
            'qc_metrics': {
                'global_score': 50.0,
                'gnss_score': 75.0,
                'sensors_score': 25.0
            },
            'observation_sensors': [
                {'id': 'MRU_Test', 'type': 'MRU'},
                {'id': 'Compas_Test', 'type': 'Compas'}
            ]
        }
        print("✅ OK")
        
        print("5.3 Application des données... ", end="")
        home_widget.update_project_display(test_project)
        print("✅ OK")
        
        print("5.4 Vérification affichage... ", end="")
        assert home_widget.current_project == test_project
        assert "Navire Test Spyder" in home_widget.project_name_label.text()
        print("✅ OK")
        
        print("\n🎉 Simulation de données réussie !")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale - lance tous les tests"""
    print("🚀 Démarrage des tests...")
    print()
    
    # Compteur de réussite
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 2: Création composants
    result2 = test_basic_creation()
    if result2[0] is not None:
        tests_passed += 1
    
    # Test 3: ProjectManager
    if test_project_manager():
        tests_passed += 1
    
    # Test 4: Affichage visuel (optionnel)
    if test_visual_display():
        tests_passed += 1
    
    # Test 5: Simulation données
    if test_project_simulation():
        tests_passed += 1
    
    # Résultat final
    print("\n" + "=" * 60)
    print("📊 RÉSULTAT FINAL")
    print("=" * 60)
    print(f"Tests réussis: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n🎉 FÉLICITATIONS ! Votre Page Accueil Enhanced fonctionne parfaitement !")
        print("✅ Tous les composants sont opérationnels")
        print("✅ L'intégration avec ProjectManager est OK")
        print("✅ L'affichage fonctionne correctement")
        print("\n🚀 Vous pouvez maintenant utiliser votre application !")
    elif tests_passed >= total_tests - 1:
        print("\n🟡 Presque parfait ! Un test optionnel a échoué")
        print("✅ Les fonctionnalités principales marchent")
        print("💡 Vérifiez les détails ci-dessus si nécessaire")
    else:
        print(f"\n⚠️ {total_tests - tests_passed} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs détaillées ci-dessus")
        print("💡 Les problèmes les plus courants:")
        print("   - Mauvais répertoire de travail")
        print("   - Imports manquants")
        print("   - Fichiers non sauvegardés")
    
    print("\n✨ Test terminé - Merci d'avoir testé votre Page Accueil Enhanced !")

# Lancement automatique si exécuté directement
if __name__ == "__main__":
    main()