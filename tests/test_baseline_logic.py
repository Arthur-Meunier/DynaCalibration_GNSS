#!/usr/bin/env python3
"""
Test pour vérifier la logique de détection de fin de calcul
"""

def test_baseline_completion_logic():
    """Teste la logique de détection de fin de calcul"""
    
    # Simuler les résultats de baseline
    baseline_results = {
        0: {"status": "running", "progress": 0},
        1: {"status": "running", "progress": 0}
    }
    
    print("🔍 DEBUG: État initial des baselines:")
    for i, result in baseline_results.items():
        print(f"  Baseline {i}: {result}")
    
    # Simuler la fin de la première baseline
    print("\n🔍 DEBUG: Fin de la baseline 0")
    baseline_results[0]["status"] = "success"
    
    # Vérifier si toutes sont terminées
    all_finished = all(result["status"] in ["success", "error"] for result in baseline_results.values())
    print(f"🔍 DEBUG: Toutes terminées après baseline 0: {all_finished}")
    
    # Simuler la fin de la deuxième baseline
    print("\n🔍 DEBUG: Fin de la baseline 1")
    baseline_results[1]["status"] = "success"
    
    # Vérifier si toutes sont terminées
    all_finished = all(result["status"] in ["success", "error"] for result in baseline_results.values())
    print(f"🔍 DEBUG: Toutes terminées après baseline 1: {all_finished}")
    
    if all_finished:
        print("🔍 DEBUG: ✅ Toutes les baselines sont terminées - signal processing_completed devrait être émis")
    else:
        print("🔍 DEBUG: ❌ Pas toutes les baselines sont terminées")

if __name__ == "__main__":
    test_baseline_completion_logic()

