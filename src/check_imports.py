# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16 01:51:24 2025

@author: a.meunier
"""

#!/usr/bin/env python3
"""
Script de vérification des imports pour le projet de calibration.

Ce script teste que tous les modules peuvent être importés correctement
et affiche un rapport détaillé des erreurs éventuelles.

Usage:
    cd src
    python check_imports.py
"""

import sys
import os
from pathlib import Path

def setup_path():
    """Configure le PYTHONPATH pour les tests."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    print(f"📁 Test depuis: {current_dir}")
    print(f"📁 Projet racine: {project_root}")
    return current_dir

def test_basic_dependencies():
    """Teste les dépendances Python de base."""
    print("\n🔍 TEST DES DÉPENDANCES DE BASE")
    print("-" * 40)
    
    dependencies = [
        'PyQt5',
        'PyQt5.QtWidgets', 
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'numpy',
        'pandas', 
        'scipy',
        'scipy.spatial.transform',
        'matplotlib',
        'matplotlib.pyplot',
        'pyqtgraph'
    ]
    
    success = 0
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
            success += 1
        except ImportError as e:
            print(f"❌ {dep}: {e}")
        except Exception as e:
            print(f"⚠️ {dep}: {e}")
    
    print(f"\n📊 Dépendances: {success}/{len(dependencies)} OK")
    return success == len(dependencies)

def test_project_structure():
    """Vérifie la structure des fichiers du projet."""
    print("\n🔍 TEST DE LA STRUCTURE DU PROJET")
    print("-" * 40)
    
    required_files = [
        "app/__init__.py",
        "app/gui/__init__.py",
        "app/gui/app_data.py",
        "app/gui/menu_vertical.py",
        "app/gui/page_accueil.py",
        "app/gui/page_dimcon.py",
        "app/gui/page_gnss.py",
        "app/gui/page_observation.py",
        "app/core/__init__.py",
        "app/core/calculations/__init__.py",
        "app/core/calculations/calculs_observation.py",
        "app/core/importers/__init__.py",
        "app/core/importers/import_observation.py",
        "app/core/importers/import_gnss.py",
        "app/gui_app.py"
    ]
    
    current_dir = Path(__file__).parent
    success = 0
    
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
            success += 1
        else:
            print(f"❌ {file_path} - MANQUANT")
    
    print(f"\n📊 Structure: {success}/{len(required_files)} fichiers présents")
    return success == len(required_files)

def test_project_imports():
    """Teste les imports du projet."""
    print("\n🔍 TEST DES MODULES DU PROJET")
    print("-" * 40)
    
    modules_to_test = [
        # Modules GUI de base
        ("app.gui.app_data", "ApplicationData"),
        ("app.gui.menu_vertical", "VerticalMenu"),
        ("app.gui.page_accueil", "HomePageWidget"),
        
        # Modules GUI principaux
        ("app.gui.page_dimcon", "DimconWidget"),
        ("app.gui.page_gnss", "GnssWidget"),
        ("app.gui.page_observation", "ObservationWidget"),
        
        # Modules core - calculations
        ("app.core.calculations.calculs_observation", "ObservationCalculator"),
        
        # Modules core - importers
        ("app.core.importers.import_observation", "ObservationImportDialog"),
        ("app.core.importers.import_gnss", "GNSSImportDialog"),
        
        # Module principal
        ("app.gui_app", "MainWindow"),
    ]
    
    success = 0
    errors = []
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
            success += 1
        except ImportError as e:
            error_msg = f"❌ {module_name}.{class_name}: Import Error - {e}"
            print(error_msg)
            errors.append((module_name, "ImportError", str(e)))
        except AttributeError as e:
            error_msg = f"⚠️ {module_name}.{class_name}: Attribute Error - {e}"
            print(error_msg)
            errors.append((module_name, "AttributeError", str(e)))
        except Exception as e:
            error_msg = f"⚠️ {module_name}.{class_name}: {type(e).__name__} - {e}"
            print(error_msg)
            errors.append((module_name, type(e).__name__, str(e)))
    
    print(f"\n📊 Modules projet: {success}/{len(modules_to_test)} OK")
    
    # Affichage détaillé des erreurs
    if errors:
        print(f"\n🔍 ANALYSE DES ERREURS:")
        print("-" * 30)
        for module, error_type, error_msg in errors:
            print(f"Module: {module}")
            print(f"  Type: {error_type}")
            print(f"  Détail: {error_msg}")
            print()
    
    return success == len(modules_to_test)

def test_critical_instantiation():
    """Teste l'instanciation des classes critiques."""
    print("\n🔍 TEST D'INSTANCIATION DES CLASSES CRITIQUES")
    print("-" * 50)
    
    tests = []
    
    # Test ApplicationData
    try:
        from app.gui.app_data import ApplicationData
        app_data = ApplicationData()
        print("✅ ApplicationData() - Instanciation OK")
        
        # Test des méthodes de base
        if hasattr(app_data, 'dimcon'):
            print("✅ ApplicationData.dimcon - Attribut présent")
        if hasattr(app_data, 'gnss_data'):
            print("✅ ApplicationData.gnss_data - Attribut présent")
        
        tests.append(True)
    except Exception as e:
        print(f"❌ ApplicationData(): {e}")
        tests.append(False)
    
    # Test ObservationCalculator
    try:
        from app.core.calculations.calculs_observation import ObservationCalculator
        calc = ObservationCalculator()
        print("✅ ObservationCalculator() - Instanciation OK")
        
        # Test des méthodes principales
        if hasattr(calc, 'calculate_all_sensors'):
            print("✅ ObservationCalculator.calculate_all_sensors - Méthode présente")
        if hasattr(calc, 'set_data_model'):
            print("✅ ObservationCalculator.set_data_model - Méthode présente")
        
        tests.append(True)
    except Exception as e:
        print(f"❌ ObservationCalculator(): {e}")
        tests.append(False)
    
    # Test imports des dialogues (sans instancier car nécessite QApplication)
    try:
        from app.core.importers.import_observation import ObservationImportDialog
        print("✅ ObservationImportDialog (import) - OK")
        tests.append(True)
    except Exception as e:
        print(f"❌ ObservationImportDialog (import): {e}")
        tests.append(False)
    
    try:
        from app.core.importers.import_gnss import GNSSImportDialog
        print("✅ GNSSImportDialog (import) - OK")
        tests.append(True)
    except Exception as e:
        print(f"❌ GNSSImportDialog (import): {e}")
        tests.append(False)
    
    # Test GUI principal (import seulement)
    try:
        from app.gui_app import MainWindow
        print("✅ MainWindow (import) - OK")
        tests.append(True)
    except Exception as e:
        print(f"❌ MainWindow (import): {e}")
        tests.append(False)
    
    print(f"\n📊 Instanciations: {sum(tests)}/{len(tests)} OK")
    return all(tests)

def test_imports_fixes():
    """Vérifie que les imports relatifs sont correctement configurés."""
    print("\n🔍 TEST DES IMPORTS RELATIFS")
    print("-" * 40)
    
    import_tests = []
    
    # Test 1: Vérifier que page_observation importe correctement
    try:
        # Simuler l'import depuis page_observation
        import app.gui.page_observation as po_module
        
        # Vérifier que les classes attendues sont disponibles
        if hasattr(po_module, 'ObservationWidget'):
            print("✅ page_observation.ObservationWidget disponible")
            import_tests.append(True)
        else:
            print("❌ page_observation.ObservationWidget manquant")
            import_tests.append(False)
            
    except Exception as e:
        print(f"❌ Erreur import page_observation: {e}")
        import_tests.append(False)
    
    # Test 2: Vérifier que page_gnss importe correctement
    try:
        import app.gui.page_gnss as gnss_module
        
        if hasattr(gnss_module, 'GnssWidget'):
            print("✅ page_gnss.GnssWidget disponible")
            import_tests.append(True)
        else:
            print("❌ page_gnss.GnssWidget manquant")
            import_tests.append(False)
            
    except Exception as e:
        print(f"❌ Erreur import page_gnss: {e}")
        import_tests.append(False)
    
    # Test 3: Chaîne complète d'imports
    try:
        from app.gui.page_observation import ObservationWidget
        from app.core.calculations.calculs_observation import ObservationCalculator
        from app.core.importers.import_observation import ObservationImportDialog
        print("✅ Chaîne d'imports observation complète")
        import_tests.append(True)
    except Exception as e:
        print(f"❌ Chaîne d'imports observation: {e}")
        import_tests.append(False)
    
    print(f"\n📊 Imports relatifs: {sum(import_tests)}/{len(import_tests)} OK")
    return all(import_tests)

def generate_diagnostic_report():
    """Génère un rapport de diagnostic complet."""
    print("\n📋 GÉNÉRATION DU RAPPORT DE DIAGNOSTIC")
    print("=" * 50)
    
    # Tests complets
    structure_ok = test_project_structure()
    deps_ok = test_basic_dependencies()
    imports_ok = test_project_imports() 
    instance_ok = test_critical_instantiation()
    relatifs_ok = test_imports_fixes()
    
    # Résumé détaillé
    print(f"\n📊 RÉSUMÉ DÉTAILLÉ")
    print("=" * 30)
    print(f"Structure fichiers: {'✅' if structure_ok else '❌'}")
    print(f"Dépendances:        {'✅' if deps_ok else '❌'}")
    print(f"Imports modules:    {'✅' if imports_ok else '❌'}")
    print(f"Instanciations:     {'✅' if instance_ok else '❌'}")
    print(f"Imports relatifs:   {'✅' if relatifs_ok else '❌'}")
    
    overall_status = all([structure_ok, deps_ok, imports_ok, instance_ok, relatifs_ok])
    
    print(f"\n{'='*50}")
    if overall_status:
        print(f"🎉 STATUT GLOBAL: ✅ SUCCÈS COMPLET")
        print("   L'application devrait fonctionner parfaitement.")
        print("\n🚀 Prêt à lancer:")
        print("   python main.py")
    else:
        print(f"⚠️ STATUT GLOBAL: ❌ CORRECTIONS NÉCESSAIRES")
        print("   Des ajustements sont requis avant le lancement.")
        
        print(f"\n💡 ACTIONS RECOMMANDÉES:")
        
        if not structure_ok:
            print("   📁 Structure:")
            print("      - Créez les fichiers manquants listés ci-dessus")
            print("      - Vérifiez que tous les __init__.py sont présents")
        
        if not deps_ok:
            print("   📦 Dépendances:")
            print("      - pip install PyQt5 numpy pandas scipy matplotlib pyqtgraph")
        
        if not imports_ok:
            print("   📥 Imports modules:")
            print("      - Vérifiez le contenu des fichiers Python")
            print("      - Corrigez les erreurs de syntaxe")
            print("      - Assurez-vous que toutes les classes sont définies")
        
        if not instance_ok:
            print("   🏗️ Instanciations:")
            print("      - Corrigez les erreurs dans les constructeurs")
            print("      - Vérifiez les imports dans les modules")
        
        if not relatifs_ok:
            print("   🔗 Imports relatifs:")
            print("      - Corrigez les imports dans page_observation.py")
            print("      - Corrigez les imports dans page_gnss.py")
            print("      - Utilisez la syntaxe: from ..core.module import Class")
    
    print(f"{'='*50}")
    return overall_status

def show_help():
    """Affiche l'aide du script."""
    print("""
🔍 SCRIPT DE VÉRIFICATION DES IMPORTS

Ce script vérifie que votre projet de calibration est correctement configuré.

USAGE:
    cd src/
    python check_imports.py

TESTS EFFECTUÉS:
    ✓ Structure des fichiers et répertoires
    ✓ Dépendances Python (PyQt5, numpy, etc.)
    ✓ Imports des modules du projet
    ✓ Instanciation des classes critiques
    ✓ Imports relatifs entre modules

CODES DE SORTIE:
    0 = Succès (tout fonctionne)
    1 = Échec (corrections nécessaires)
    
AIDE:
    python check_imports.py --help
    """)

def main():
    """Fonction principale du script de vérification."""
    
    # Gestion des arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return
    
    print("🔍 VÉRIFICATION COMPLÈTE DES IMPORTS - PROJET CALIBRATION")
    print("=" * 65)
    
    # Configuration de l'environnement
    setup_path()
    
    # Exécution du diagnostic complet
    success = generate_diagnostic_report()
    
    # Affichage final
    print(f"\n⏱️ Vérification terminée.")
    
    if success:
        print("🎯 Résultat: Projet prêt à être lancé!")
    else:
        print("🔧 Résultat: Corrections nécessaires.")
    
    # Code de sortie pour scripts automatisés
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()