# -*- coding: utf-8 -*-
"""
Created on Mon Jul 28 04:40:38 2025

@author: a.meunier
"""

# quick_test_interactive.py - Tests rapides et interactifs

import sys
import os
from pathlib import Path

# Configuration du path
current_dir = Path(__file__).parent
if (current_dir / "src").exists():
    sys.path.insert(0, str(current_dir / "src"))
else:
    # Si exécuté depuis un sous-dossier
    for parent in current_dir.parents:
        if (parent / "src").exists():
            sys.path.insert(0, str(parent / "src"))
            break

def wait_for_user(message="Appuyez sur Entrée pour continuer..."):
    """Attend que l'utilisateur appuie sur Entrée"""
    input(f"\n{message}")

def test_dashboard_display():
    """Test interactif du dashboard"""
    print("\n🏠 TEST DASHBOARD - Page Accueil Enhanced")
    print("=" * 50)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import EnhancedHomePageWidget
        
        app = QApplication.instance() or QApplication([])
        
        print("✓ Création de la page d'accueil enhanced...")
        home_widget = EnhancedHomePageWidget()
        
        print("✓ Affichage de la fenêtre...")
        home_widget.show()
        home_widget.resize(1000, 700)
        
        print("\n📋 VÉRIFICATIONS VISUELLES:")
        print("1. Vous devriez voir le titre '🏠 Tableau de Bord'")
        print("2. Section 'Projet Actuel' avec 'Aucun projet chargé'")
        print("3. Progression du workflow avec barres Dimcon/GNSS/Observation/QC")
        print("4. Métriques de qualité avec 4 cartes")
        print("5. Actions rapides avec 4 boutons")
        print("6. Activité récente avec l'heure")
        
        wait_for_user("Le dashboard s'affiche-t-il correctement ? (Entrée)")
        
        return home_widget, app
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return None, None

def test_project_creation_dialog():
    """Test du dialogue de création de projet"""
    print("\n🆕 TEST CRÉATION PROJET")
    print("=" * 30)
    
    try:
        from app.gui.page_accueil import ProjectCreationDialog
        
        print("✓ Ouverture du dialogue de création...")
        dialog = ProjectCreationDialog()
        dialog.show()
        
        print("\n📋 VÉRIFICATIONS:")
        print("1. Formulaire avec champs Nom*, Compagnie*, Navire*, Ingénieur*")
        print("2. Zone description (optionnelle)")
        print("3. Sélecteur de répertoire")
        print("4. Boutons Annuler/Créer")
        
        wait_for_user("Le dialogue s'affiche-t-il correctement ? (Entrée)")
        
        dialog.close()
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def test_project_integration():
    """Test de l'intégration avec un projet réel"""
    print("\n🔗 TEST INTÉGRATION PROJET")
    print("=" * 35)
    
    try:
        from core.project_manager import ProjectManager
        import tempfile
        
        print("✓ Création d'un projet de test...")
        pm = ProjectManager.instance()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = pm.create_project(
                name="Test_Dashboard",
                company="Société Test",
                vessel="Navire Test",
                engineer="Ingénieur Test",
                description="Test d'intégration dashboard",
                base_path=str(Path(temp_dir) / "test_project")
            )
            
            if not success:
                print(f"❌ Échec création projet: {result}")
                return False
            
            print(f"✓ Projet créé: {result}")
            
            # Maintenant tester l'affichage
            from app.gui.page_accueil import EnhancedHomePageWidget
            from PyQt5.QtWidgets import QApplication
            
            app = QApplication.instance() or QApplication([])
            
            print("✓ Création page d'accueil avec projet...")
            home_widget = EnhancedHomePageWidget()
            home_widget.show()
            
            # Charger le projet
            home_widget.load_current_project()
            
            print("\n📋 VÉRIFICATIONS:")
            print("1. Le nom du projet devrait être affiché (Navire Test - Société Test)")
            print("2. Détails: Ingénieur Test, dates de création")
            print("3. Workflow à 0% sur toutes les étapes")
            print("4. Métriques à 0")
            
            wait_for_user("Les données du projet s'affichent-elles ? (Entrée)")
            
            return home_widget, app
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_workflow_simulation():
    """Test de simulation du workflow"""
    print("\n🔄 TEST SIMULATION WORKFLOW")
    print("=" * 35)
    
    try:
        from app.gui.page_accueil import EnhancedHomePageWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        
        print("✓ Création page avec données simulées...")
        home_widget = EnhancedHomePageWidget()
        
        # Simuler un projet avec progression
        mock_project = {
            'metadata': {
                'vessel': 'Navire Simulé',
                'company': 'Société Simulée', 
                'engineer': 'Ingénieur Simulé',
                'created': '2025-01-15T10:00:00Z',
                'last_modified': '2025-01-15T15:30:00Z',
                'description': 'Projet de simulation pour test workflow'
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
                {'id': 'MRU_01', 'type': 'MRU'},
                {'id': 'COMPAS_01', 'type': 'Compas'},
                {'id': 'OCTANS_01', 'type': 'Octans'}
            ]
        }
        
        print("✓ Application des données simulées...")
        home_widget.update_project_display(mock_project)
        home_widget.show()
        
        print("\n📋 VÉRIFICATIONS:")
        print("1. Nom: 'Navire Simulé - Société Simulée'")
        print("2. Workflow: Dimcon 100%✅, GNSS 75%⏳, Observation 25%⏳, QC 0%⏳")
        print("3. Score global: 50.0%")
        print("4. Score GNSS: 75.0%")
        print("5. Capteurs: 3")
        
        wait_for_user("Le workflow et les métriques s'affichent-ils correctement ? (Entrée)")
        
        return home_widget, app
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return None, None

def test_buttons_functionality():
    """Test des boutons et interactions"""
    print("\n🖱️ TEST BOUTONS ET INTERACTIONS")
    print("=" * 40)
    
    try:
        from app.gui.page_accueil import EnhancedHomePageWidget
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication([])
        home_widget = EnhancedHomePageWidget()
        home_widget.show()
        
        print("✓ Page d'accueil affichée")
        print("\n🔧 TESTS D'INTERACTION:")
        print("1. Cliquez sur 'Nouveau Projet' - le dialogue doit s'ouvrir")
        print("2. Cliquez sur 'Ouvrir Projet' - sélecteur de fichier")
        print("3. Cliquez sur 'Sauvegarder' - message d'info")
        print("4. Cliquez sur 'Continuer le Travail' - message d'info")
        print("5. Vérifiez que l'heure se met à jour toutes les 5 secondes")
        
        wait_for_user("Testez les boutons... Appuyez sur Entrée quand c'est fait")
        
        return home_widget, app
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return None, None

def run_interactive_tests():
    """Lance tous les tests interactifs"""
    print("🧪 TESTS INTERACTIFS - PAGE ACCUEIL ENHANCED")
    print("=" * 60)
    print("Ces tests vont ouvrir des fenêtres pour validation visuelle")
    print()
    
    widgets_to_close = []
    
    try:
        # Test 1: Dashboard de base
        print("🔄 Lancement Test 1...")
        result1 = test_dashboard_display()
        if result1[0]:
            widgets_to_close.append(result1[0])
        
        # Test 2: Dialogue création
        print("\n🔄 Lancement Test 2...")
        test_project_creation_dialog()
        
        # Test 3: Intégration projet
        print("\n🔄 Lancement Test 3...")
        result3 = test_project_integration()
        if result3 and result3[0]:
            widgets_to_close.append(result3[0])
        
        # Test 4: Simulation workflow  
        print("\n🔄 Lancement Test 4...")
        result4 = test_workflow_simulation()
        if result4 and result4[0]:
            widgets_to_close.append(result4[0])
        
        # Test 5: Boutons
        print("\n🔄 Lancement Test 5...")
        result5 = test_buttons_functionality()
        if result5 and result5[0]:
            widgets_to_close.append(result5[0])
        
        print("\n" + "=" * 60)
        print("🎉 TESTS TERMINÉS !")
        print()
        print("✅ Si tous les éléments s'affichaient correctement:")
        print("   → Votre Page Accueil Enhanced fonctionne parfaitement !")
        print()
        print("❌ Si des problèmes sont apparus:")
        print("   → Vérifiez les erreurs dans la console")
        print("   → Assurez-vous que tous les imports fonctionnent")
        
        wait_for_user("Appuyez sur Entrée pour fermer toutes les fenêtres...")
        
    finally:
        # Fermer toutes les fenêtres ouvertes
        for widget in widgets_to_close:
            try:
                widget.close()
            except:
                pass

def quick_smoke_test():
    """Test rapide de fumée - juste vérifier que tout se charge"""
    print("💨 TEST DE FUMÉE RAPIDE")
    print("=" * 30)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import de base
    total_tests += 1
    try:
        from app.gui.page_accueil import EnhancedHomePageWidget
        print("✅ Import EnhancedHomePageWidget")
        success_count += 1
    except Exception as e:
        print(f"❌ Import EnhancedHomePageWidget: {e}")
    
    # Test 2: Création instance
    total_tests += 1
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        widget = EnhancedHomePageWidget()
        print("✅ Création instance")
        success_count += 1
    except Exception as e:
        print(f"❌ Création instance: {e}")
    
    # Test 3: ProjectManager
    total_tests += 1
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager.instance()
        print("✅ ProjectManager accessible")
        success_count += 1
    except Exception as e:
        print(f"❌ ProjectManager: {e}")
    
    # Test 4: Dialogue création
    total_tests += 1
    try:
        from app.gui.page_accueil import ProjectCreationDialog
        dialog = ProjectCreationDialog()
        print("✅ Dialogue création")
        success_count += 1
    except Exception as e:
        print(f"❌ Dialogue création: {e}")
    
    print(f"\n📊 RÉSULTAT: {success_count}/{total_tests} tests passés")
    
    if success_count == total_tests:
        print("🎉 Tous les composants se chargent correctement !")
        return True
    else:
        print("⚠️ Certains composants ont des problèmes")
        return False

def main():
    """Menu principal"""
    print("🧪 TESTEUR PAGE ACCUEIL ENHANCED")
    print("=" * 40)
    print()
    print("Choisissez le type de test :")
    print("1. Test de fumée rapide (30 sec)")
    print("2. Tests interactifs complets (5 min)")
    print("3. Quitter")
    print()
    
    while True:
        choice = input("Votre choix (1-3): ").strip()
        
        if choice == "1":
            quick_smoke_test()
            break
        elif choice == "2":
            run_interactive_tests()
            break
        elif choice == "3":
            print("Au revoir !")
            break
        else:
            print("❌ Choix invalide, tapez 1, 2 ou 3")

if __name__ == "__main__":
    main()