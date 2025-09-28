# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 02:22:51 2025

@author: a.meunier
"""

# test_simple_validation.py - Test minimal pour identifier le problème

import sys
from pathlib import Path

# Adapter le chemin selon votre structure
sys.path.append('src/core')
sys.path.append('.')

def test_minimal():
    """Test minimal pour identifier le problème"""
    
    print("🔧 TEST MINIMAL")
    print("-" * 40)
    
    # 1. Test import project_manager
    try:
        from project_manager import ProjectManager
        print("✅ ProjectManager importé")
    except Exception as e:
        print(f"❌ Erreur import ProjectManager: {e}")
        return
    
    # 2. Test création instance
    try:
        pm = ProjectManager.instance()
        print("✅ Instance ProjectManager créée")
    except Exception as e:
        print(f"❌ Erreur création instance: {e}")
        return
    
    # 3. Test si projet existe déjà
    if pm.current_project:
        print(f"✅ Projet déjà chargé: {pm.get_project_info()['name']}")
    else:
        print("ℹ️ Aucun projet chargé")
        
        # Créer un projet minimal
        success, message = pm.create_project(
            name="Test_Minimal",
            company="Test",
            vessel="Test",
            engineer="Test"
        )
        
        if success:
            print(f"✅ Projet test créé: {Path(message).name}")
        else:
            print(f"❌ Erreur création projet: {message}")
            return
    
    # 4. Test méthode extract_approx_position_xyz
    print("\n🧪 Test extraction coordonnées...")
    
    # CHANGEZ CE CHEMIN avec votre fichier RINEX Bow/Stern !
    test_file = r"C:\1-Data\01-Projet\ProjetPY\Thialf\2\Bow-9205.25o"
    
    if not Path(test_file).exists():
        print(f"❌ Fichier test non trouvé: {test_file}")
        print("   MODIFIEZ le chemin dans le script !")
        return
    
    try:
        coords = pm.extract_approx_position_xyz(test_file)
        print(f"✅ Extraction réussie:")
        print(f"   X: {coords['x']:15.3f}")
        print(f"   Y: {coords['y']:15.3f}")
        print(f"   Z: {coords['z']:15.3f}")
        
        if any(coords[k] != 0.0 for k in ['x', 'y', 'z']):
            print("✅ Coordonnées réelles trouvées")
        else:
            print("⚠️ Coordonnées par défaut - APPROX POSITION non trouvé dans le fichier")
            
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
        return
    
    # 5. Test simple SP3 checker
    print("\n🧪 Test SP3/CLK checker...")
    
    try:
        from simple_sp3_checker import SimpleSP3Checker
        sp3_result = SimpleSP3Checker.check_sp3_clk_in_directory(test_file)
        print(f"✅ SP3/CLK check: {sp3_result['message']}")
    except Exception as e:
        print(f"⚠️ SimpleSP3Checker non disponible: {e}")
    
    # 6. Test méthode update_gnss_files_and_coordinates DIRECTEMENT
    print("\n🧪 Test update_gnss_files_and_coordinates...")
    
    test_data = {
        'bow_stern': {
            'obs_file': test_file,
            'nav_file': test_file.replace('.25o', '_nav.rnx'),  # Approximation
            'approx_xyz': coords
        },
        'port': {
            'obs_file': test_file.replace('Bow', 'Port'),
            'nav_file': test_file.replace('.25o', '_nav.rnx')
        },
        'starboard': {
            'obs_file': test_file.replace('Bow', 'Stb'),
            'nav_file': test_file.replace('.25o', '_nav.rnx')
        },
        'sp3_clk_status': {
            'sp3_available': False,
            'clk_available': False,
            'message': 'Test'
        }
    }
    
    try:
        success = pm.update_gnss_files_and_coordinates(test_data)
        
        if success:
            print("✅ update_gnss_files_and_coordinates réussie")
            
            # Vérifier le résultat
            gnss_config = pm.current_project.get('gnss_config', {})
            base_station = gnss_config.get('base_station', {})
            
            print(f"📡 Résultat dans gnss_config:")
            print(f"   base_station.position_name: '{base_station.get('position_name')}'")
            print(f"   base_station.obs_file: '{Path(base_station.get('obs_file', '')).name}'")
            print(f"   coordinates_xyz.x: {base_station.get('coordinates_xyz', {}).get('x', 0)}")
            print(f"   rovers count: {len(gnss_config.get('rovers', []))}")
            print(f"   processing_ready: {gnss_config.get('processing_ready')}")
            
            if base_station.get('position_name') == 'Bow/Stern':
                print("✅ Les données ont été correctement sauvegardées !")
                
                # Afficher le chemin du fichier JSON
                project_info = pm.get_project_info()
                print(f"\n📄 Fichier JSON du projet: {project_info['path']}")
                
                return True
            else:
                print("❌ Les données n'ont pas été sauvegardées correctement")
                
        else:
            print("❌ update_gnss_files_and_coordinates a échoué")
            
    except Exception as e:
        print(f"❌ Erreur update_gnss_files_and_coordinates: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    success = test_minimal()
    
    if success:
        print(f"\n🎉 TEST RÉUSSI!")
        print("Votre configuration fonctionne correctement.")
    else:
        print(f"\n❌ TEST ÉCHOUÉ")
        print("Vérifiez les erreurs ci-dessus.")
    
    print(f"\n💡 N'oubliez pas de modifier le chemin du fichier RINEX dans le script!")