# -*- coding: utf-8 -*-
"""
Created on Wed Aug  6 23:00:58 2025

@author: a.meunier
"""

# run_gnss_tests.py - Script de lancement simplifié

"""
Script de lancement pour tester les nouvelles fonctionnalités GNSS SP3/CLK

Usage:
    python run_gnss_tests.py [option]
    
Options:
    --full      : Test complet (tous composants)
    --quick     : Tests rapides seulement  
    --rinex     : Test parser RINEX uniquement
    --sp3       : Test validateur SP3/CLK uniquement
    --components: Diagnostic composants disponibles
    --help      : Afficher cette aide
"""

import sys
import argparse
from pathlib import Path

def setup_python_path():
    """Configure le path Python pour trouver les modules"""
    current_dir = Path(__file__).parent
    
    # Chemins possibles vers le code source
    possible_paths = [
        current_dir / "src",
        current_dir.parent / "src", 
        current_dir / ".." / "src",
        current_dir
    ]
    
    for path in possible_paths:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
            print(f"📁 Path ajouté: {path}")

def run_quick_tests():
    """Lance les tests rapides"""
    print("⚡ TESTS RAPIDES GNSS SP3/CLK")
    print("=" * 40)
    
    from test_gnss_sp3_complete import test_only_rinex_parser, test_only_sp3_validator
    
    tests = [
        ("Parser RINEX", test_only_rinex_parser),
        ("Validateur SP3/CLK", test_only_sp3_validator)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            success = test_func()
            results[test_name] = success
            print(f"{'✅ RÉUSSI' if success else '❌ ÉCHOUÉ'}")
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            results[test_name] = False
    
    # Bilan
    passed = sum(results.values())
    total = len(results)
    print(f"\n📊 Bilan: {passed}/{total} tests réussis")
    
    return all(results.values())

def run_full_tests():
    """Lance la suite complète de tests"""
    print("🔬 SUITE COMPLÈTE DE TESTS GNSS SP3/CLK")
    print("=" * 50)
    
    from test_gnss_sp3_complete import run_comprehensive_gnss_test
    
    exit_code, temp_dir = run_comprehensive_gnss_test()
    
    print(f"\n📁 Fichiers de test disponibles dans: {temp_dir}")
    print("💡 Examinez ce répertoire pour débugger si nécessaire")
    
    return exit_code == 0

def run_component_diagnostic():
    """Diagnostic des composants disponibles"""
    print("🔍 DIAGNOSTIC COMPOSANTS GNSS")
    print("=" * 35)
    
    from test_gnss_sp3_complete import test_component_availability
    test_component_availability()

def main():
    """Point d'entrée principal"""
    setup_python_path()
    
    parser = argparse.ArgumentParser(
        description="Tests pour les fonctionnalités GNSS SP3/CLK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
    python run_gnss_tests.py --full          # Suite complète 
    python run_gnss_tests.py --quick         # Tests rapides
    python run_gnss_tests.py --rinex         # Parser RINEX seulement
    python run_gnss_tests.py --components    # Diagnostic composants
        """
    )
    
    parser.add_argument('--full', action='store_true', 
                      help='Lance la suite complète de tests')
    parser.add_argument('--quick', action='store_true',
                      help='Lance les tests rapides seulement')
    parser.add_argument('--rinex', action='store_true',
                      help='Teste uniquement le parser RINEX') 
    parser.add_argument('--sp3', action='store_true',
                      help='Teste uniquement le validateur SP3/CLK')
    parser.add_argument('--components', action='store_true',
                      help='Diagnostic des composants disponibles')
    
    args = parser.parse_args()
    
    # Si aucun argument, mode interactif
    if not any(vars(args).values()):
        print("🧪 MODE INTERACTIF")
        from test_gnss_sp3_complete import main as interactive_main
        interactive_main()
        return
    
    # Exécuter le test demandé
    success = True
    
    try:
        if args.components:
            run_component_diagnostic()
        
        elif args.rinex:
            from test_gnss_sp3_complete import test_only_rinex_parser
            success = test_only_rinex_parser()
        
        elif args.sp3:
            from test_gnss_sp3_complete import test_only_sp3_validator  
            success = test_only_sp3_validator()
        
        elif args.quick:
            success = run_quick_tests()
        
        elif args.full:
            success = run_full_tests()
        
        # Résultat final
        if success:
            print("\n🎉 Tests terminés avec succès!")
            sys.exit(0)
        else:
            print("\n❌ Échecs détectés dans les tests")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏸️ Tests interrompus")
        sys.exit(2)
    except ImportError as e:
        print(f"\n❌ Composants manquants: {e}")
        print("💡 Vérifiez que tous les modules sont disponibles")
        sys.exit(3)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        sys.exit(4)

if __name__ == "__main__":
    main()