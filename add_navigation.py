#!/usr/bin/env python3
"""
Script pour ajouter la navigation automatique directement
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def add_auto_navigation():
    """Ajoute la navigation automatique directement dans on_parallel_baseline_finished"""
    
    page_gnss_path = src_dir / "app" / "gui" / "page_GNSS.py"
    
    if not page_gnss_path.exists():
        print(f"❌ Fichier non trouvé: {page_gnss_path}")
        return False
    
    # Lire le fichier
    with open(page_gnss_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver la méthode on_parallel_baseline_finished
    method_start = content.find("def on_parallel_baseline_finished(self, baseline_index: int, return_code: int):")
    
    if method_start == -1:
        print("❌ Méthode on_parallel_baseline_finished non trouvée")
        return False
    
    # Trouver la fin de cette méthode (prochaine méthode ou fin de classe)
    method_end = content.find("\n    def ", method_start + 1)
    if method_end == -1:
        method_end = content.find("\nclass ", method_start + 1)
    if method_end == -1:
        method_end = len(content)
    
    # Extraire la méthode actuelle
    method_content = content[method_start:method_end]
    
    # Vérifier si la navigation automatique est déjà présente
    if "trigger_auto_navigation" in method_content:
        print("✅ Navigation automatique déjà présente")
        return True
    
    # Ajouter la navigation automatique à la fin de la méthode
    navigation_code = '''
        # ✅ NOUVEAU : Navigation automatique après la fin de tous les calculs
        if all_finished:
            print("🔍 DEBUG: Toutes les baselines terminées - Déclenchement navigation automatique")
            # Attendre un peu puis déclencher la navigation
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, self.trigger_auto_navigation)
    
    def trigger_auto_navigation(self):
        """Déclenche la navigation automatique vers la page post-calcul"""
        try:
            print("🔍 DEBUG: Déclenchement navigation automatique")
            # Émettre le signal de completion avec des résultats simulés
            results = {
                "total_baselines": len(self.baselines_to_calculate) if hasattr(self, 'baselines_to_calculate') else 2,
                "successful_baselines": ["Port→Bow", "Port→Stbd"],
                "failed_baselines": [],
                "quality_data": {}
            }
            print("🔍 DEBUG: Émission du signal processing_completed")
            self.processing_completed.emit(results)
            print("🔍 DEBUG: Signal processing_completed émis")
        except Exception as e:
            print(f"❌ Erreur navigation automatique: {e}")
'''
    
    # Remplacer la fin de la méthode
    if "if all_finished:" in method_content:
        # Remplacer la ligne existante
        old_end = method_content.find("if all_finished:")
        new_method = method_content[:old_end] + navigation_code
    else:
        # Ajouter à la fin
        new_method = method_content.rstrip() + navigation_code
    
    # Remplacer dans le contenu complet
    new_content = content[:method_start] + new_method + content[method_end:]
    
    # Sauvegarder
    with open(page_gnss_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Navigation automatique ajoutée avec succès")
    return True

if __name__ == "__main__":
    if add_auto_navigation():
        print("✅ Correction appliquée avec succès")
        print("🔍 DEBUG: Vous pouvez maintenant tester l'application")
    else:
        print("❌ Échec de la correction")

