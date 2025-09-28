# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 02:22:00 2025

@author: a.meunier
"""

# debug_rinex_import.py - Script pour débugger l'import RINEX

import sys
import json
from pathlib import Path

# Ajouter le chemin vers vos modules (à adapter selon votre structure)
sys.path.append('src/core')
sys.path.append('.')

def test_import_simple_sp3():
    """Test 1: Vérifier que SimpleSP3Checker fonctionne"""
    print("🧪 TEST 1: SimpleSP3Checker")
    print("-" * 50)
    
    try:
        from core.importers.simple_sp3_checker import SimpleSP3Checker
        print("✅ SimpleSP3Checker importé avec succès")
        
        # Tester avec un fichier d'exemple (changez le chemin)
        test_file = r"C:\1-Data\01-Projet\ProjetPY\Thialf\2\Bow-9205.25o"
        
        if Path(test_file).exists():
            result = SimpleSP3Checker.check_sp3_clk_in_directory(test_file)
            print(f"   Résultat: {result['message']}")
            print(f"   SP3: {result['sp3_found']}, CLK: {result['clk_found']}")
        else:
            print(f"⚠️ Fichier test non trouvé: {test_file}")
            print("   Changez le chemin dans le script")
        
    except ImportError as e:
        print(f"❌ Erreur import SimpleSP3Checker: {e}")
        return False
    
    return True

def test_extract_approx_position():
    """Test 2: Extraction APPROX POSITION"""
    print("\n🧪 TEST 2: Extraction APPROX POSITION")
    print("-" * 50)
    
    try:
        from project_manager import ProjectManager
        
        pm = ProjectManager.instance()
        
        # Tester extraction coordonnées (changez le chemin)
        test_file = r"C:\1-Data\01-Projet\ProjetPY\Thialf\2\Bow-9205.25o"
        
        if Path(test_file).exists():
            coords = pm.extract_approx_position_xyz(test_file)
            print(f"✅ Coordonnées extraites:")
            print(f"   X: {coords['x']:12.3f}")
            print(f"   Y: {coords['y']:12.3f}")
            print(f"   Z: {coords['z']:12.3f}")
            
            # Vérifier si ce sont de vraies coordonnées
            if any(coords[k] != 0.0 for k in ['x', 'y', 'z']):
                print("✅ Coordonnées réelles extraites")
                return True
            else:
                print("⚠️ Coordonnées par défaut (0,0,0) - APPROX POSITION non trouvé")
                return False
        else:
            print(f"❌ Fichier test non trouvé: {test_file}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test extraction: {e}")
        return False

def test_validation_complete():
    """Test 3: Validation complète"""
    print("\n🧪 TEST 3: Validation complète")
    print("-" * 50)
    
    try:
        from project_manager import ProjectManager
        
        pm = ProjectManager.instance()
        
        # Créer un projet test
        print("📁 Création projet test...")
        success, message = pm.create_project(
            name="DEBUG_Test_RINEX",
            company="Debug",
            vessel="Test",
            engineer="Debug"
        )
        
        if not success:
            print(f"❌ Erreur création projet: {message}")
            return False
        
        print(f"✅ Projet créé: {Path(message).name}")
        
        # Vérifier structure initiale
        gnss_config = pm.current_project.get('gnss_config', {})
        print(f"📡 Structure gnss_config initiale:")
        print(f"   use_sp3: {gnss_config.get('use_sp3')}")
        print(f"   base_station: {gnss_config.get('base_station', {}).get('position_name')}")
        print(f"   rovers: {len(gnss_config.get('rovers', []))}")
        
        # Préparer fichiers test (CHANGEZ CES CHEMINS !)
        fichiers_test = {
            'bow_stern_obs': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\Bow-9205.25o',
            'bow_stern_nav': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\BRDC00IGS_R_20250290000_01D_MN.rnx',
            'port_obs': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\Port-9205.25o',
            'port_nav': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\BRDC00IGS_R_20250290000_01D_MN.rnx',
            'starboard_obs': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\Stb-9205.25o',
            'starboard_nav': r'C:\1-Data\01-Projet\ProjetPY\Thialf\2\BRDC00IGS_R_20250290000_01D_MN.rnx'
        }
        
        # Vérifier existence fichiers
        print("\n📁 Vérification fichiers:")
        files_exist = True
        for key, filepath in fichiers_test.items():
            exists = Path(filepath).exists()
            print(f"   {key}: {'✅' if exists else '❌'} {Path(filepath).name}")
            if not exists:
                files_exist = False
        
        if not files_exist:
            print("\n⚠️ MODIFIEZ LES CHEMINS DES FICHIERS DANS LE SCRIPT!")
            return False
        
        # APPELER LA VALIDATION
        print("\n🔍 Appel valider_import_rinex_dans_projet...")
        success, validation_message = pm.valider_import_rinex_dans_projet(fichiers_test)
        
        if success:
            print(f"✅ Validation réussie!")
            print(f"📝 Message:\n{validation_message}")
            
            # Vérifier le résultat
            gnss_config_updated = pm.current_project.get('gnss_config', {})
            print(f"\n📡 gnss_config après validation:")
            
            base_station = gnss_config_updated.get('base_station', {})
            print(f"   base_station.position_name: {base_station.get('position_name')}")
            
            coords = base_station.get('coordinates_xyz', {})
            print(f"   coordinates_xyz:")
            print(f"      X: {coords.get('x', 0):12.3f}")
            print(f"      Y: {coords.get('y', 0):12.3f}")
            print(f"      Z: {coords.get('z', 0):12.3f}")
            print(f"   coordinates_source: {base_station.get('coordinates_source')}")
            
            rovers = gnss_config_updated.get('rovers', [])
            print(f"   rovers: {len(rovers)} rover(s)")
            for i, rover in enumerate(rovers):
                print(f"      {i+1}. {rover.get('position_name')}: {Path(rover.get('obs_file', '')).name}")
            
            sp3_status = gnss_config_updated.get('sp3_clk_status', {})
            print(f"   sp3_clk_status: {sp3_status.get('message', 'N/A')}")
            
            print(f"   processing_ready: {gnss_config_updated.get('processing_ready')}")
            print(f"   sp3_processing_ready: {gnss_config_updated.get('sp3_processing_ready')}")
            
            # Sauvegarder le JSON pour inspection
            project_info = pm.get_project_info()
            debug_json = Path(project_info['path']).parent / "debug_gnss_config.json"
            with open(debug_json, 'w', encoding='utf-8') as f:
                json.dump(gnss_config_updated, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 JSON debug sauvegardé: {debug_json}")
            print(f"📄 Projet complet: {project_info['path']}")
            
            return True
        else:
            print(f"❌ Erreur validation: {validation_message}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Script principal de debug"""
    print("=" * 80)
    print("🐛 SCRIPT DEBUG IMPORT RINEX")
    print("=" * 80)
    
    # Test 1: SimpleSP3Checker
    if not test_import_simple_sp3():
        print("\n❌ Test SimpleSP3Checker échoué - vérifiez l'import")
        return
    
    # Test 2: Extraction coordonnées
    if not test_extract_approx_position():
        print("\n⚠️ Test extraction coordonnées - vérifiez le fichier RINEX")
    
    # Test 3: Validation complète
    if test_validation_complete():
        print("\n" + "=" * 80)
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("=" * 80)
        print("\nVotre import RINEX fonctionne correctement.")
        print("Vous pouvez maintenant l'utiliser dans votre interface.")
    else:
        print("\n❌ Test validation échoué")
        
    print("\n💡 CONSEILS:")
    print("1. Modifiez les chemins de fichiers dans le script")
    print("2. Vérifiez que simple_sp3_checker.py est accessible")
    print("3. Vérifiez les logs pour plus de détails")

if __name__ == "__main__":
    main()