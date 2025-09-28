# test_simple_dashboard.py - Test simple et direct

import sys
from pathlib import Path

# Ajouter src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src" if (current_dir / "src").exists() else current_dir
sys.path.insert(0, str(src_dir))

print("🔍 TEST SIMPLE DASHBOARD HTML")
print("=" * 40)

def test_step_by_step():
    """Test étape par étape pour identifier le problème exact"""
    
    print("ÉTAPE 1: Test QtWebEngine...")
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtWebChannel import QWebChannel
        print("✅ QtWebEngine OK")
    except ImportError as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        print("💡 SOLUTION: pip install PyQtWebEngine")
        return False
    
    print("ÉTAPE 2: Test QApplication...")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        print("✅ QApplication OK")
    except Exception as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        return False
    
    print("ÉTAPE 3: Test import HTMLCircularDashboard...")
    try:
        from app.gui.html_dashboard_widget import HTMLCircularDashboard
        print("✅ Import OK")
    except Exception as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        print("💡 Vérifiez le fichier html_dashboard_widget.py")
        return False
    
    print("ÉTAPE 4: Test création instance...")
    try:
        dashboard = HTMLCircularDashboard()
        print("✅ Création OK")
    except Exception as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("ÉTAPE 5: Test affichage...")
    try:
        dashboard.show()
        dashboard.resize(400, 400)
        print("✅ Affichage OK")
        print("📋 Une fenêtre devrait apparaître")
    except Exception as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        return False
    
    print("ÉTAPE 6: Test méthode set_all_progress...")
    try:
        test_data = {
            'DIMCON': 50,
            'GNSS': 75,
            'OBSERVATION': 25, 
            'QC': 0
        }
        dashboard.set_all_progress(test_data)
        print("✅ Méthode OK")
    except Exception as e:
        print(f"❌ PROBLÈME TROUVÉ: {e}")
        return False
    
    print("\n🎉 TOUS LES TESTS PASSENT!")
    print("Le dashboard HTML fonctionne correctement.")
    input("Appuyez sur Entrée pour fermer...")
    
    dashboard.close()
    return True

if __name__ == "__main__":
    success = test_step_by_step()
    if not success:
        print("\n❌ TEST ÉCHOUÉ")
        print("Regardez l'erreur ci-dessus pour savoir quoi corriger.")