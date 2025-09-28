# -*- coding: utf-8 -*-
"""
Created on Mon Aug  4 02:53:51 2025

@author: a.meunier
"""

# test_debug_simple.py - Test ultra-simple pour identifier le problème

import sys
from pathlib import Path

# Ajouter src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src" if (current_dir / "src").exists() else current_dir
sys.path.insert(0, str(src_dir))

print("🔍 TEST DEBUG SIMPLE - DASHBOARD HTML")
print("=" * 50)

def test_imports_only():
    """Test juste les imports"""
    print("ÉTAPE 1: Test des imports...")
    
    try:
        print("  1.1 PyQt5...")
        from PyQt5.QtWidgets import QApplication, QWidget
        print("  ✅ PyQt5 OK")
        
        print("  1.2 QtWebEngine...")
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        print("  ✅ QtWebEngine OK")
        
        print("  1.3 HTMLCircularDashboard...")
        from app.gui.html_dashboard_widget import HTMLCircularDashboard
        print("  ✅ HTMLCircularDashboard OK")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ERREUR: {e}")
        return False

def test_creation_only():
    """Test juste la création sans affichage"""
    print("\nÉTAPE 2: Test création...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.html_dashboard_widget import HTMLCircularDashboard
        
        print("  2.1 QApplication...")
        app = QApplication.instance() or QApplication([])
        print("  ✅ QApplication OK")
        
        print("  2.2 HTMLCircularDashboard...")
        dashboard = HTMLCircularDashboard()  # <-- ICI ÇA VA PLANTER SI PROBLÈME
        print("  ✅ HTMLCircularDashboard OK")
        
        print(f"  2.3 Type créé: {type(dashboard).__name__}")
        
        # Vérifier les attributs
        if hasattr(dashboard, 'web_view'):
            print("  ✅ web_view présent")
        else:
            print("  ❌ web_view absent")
            
        return dashboard
        
    except Exception as e:
        print(f"  ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_homepagebwidget():
    """Test création HomePageWidget"""
    print("\nÉTAPE 3: Test HomePageWidget...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from app.gui.page_accueil import HomePageWidget
        from core.app_data import ApplicationData
        from PyQt5.QtCore import QSettings
        
        print("  3.1 Création dépendances...")
        app = QApplication.instance() or QApplication([])
        app_data = ApplicationData()
        settings = QSettings("Test", "Test")
        print("  ✅ Dépendances OK")
        
        print("  3.2 Création HomePageWidget...")
        home_page = HomePageWidget(app_data=app_data, settings=settings)  # <-- ICI ÇA PEUT PLANTER
        print("  ✅ HomePageWidget OK")
        
        print(f"  3.3 Dashboard dans HomePageWidget: {type(home_page.dashboard).__name__}")
        
        return home_page
        
    except Exception as e:
        print(f"  ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Lance les tests étape par étape"""
    
    # Test 1: Imports
    if not test_imports_only():
        print("\n❌ ARRÊT - Problème d'imports")
        return
    
    # Test 2: Création dashboard isolé
    dashboard = test_creation_only()
    if not dashboard:
        print("\n❌ ARRÊT - Problème création dashboard")
        return
    
    # Test 3: Création dans HomePageWidget
    home_page = test_homepagebwidget()
    if not home_page:
        print("\n❌ ARRÊT - Problème dans HomePageWidget")
        return
    
    print("\n🎉 TOUS LES TESTS PASSENT !")
    print("Le dashboard HTML fonctionne correctement.")
    print("Le problème vient d'ailleurs...")
    
    # Garder les widgets en vie quelques secondes
    import time
    time.sleep(2)

if __name__ == "__main__":
    main()