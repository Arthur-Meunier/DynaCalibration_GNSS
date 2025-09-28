print("🚀 Test simple démarré")

import os
import sys
from pathlib import Path

print("✅ Imports OK")

try:
    conf_path = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS\conf.conf")
    work_dir = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\DC-250802\GNSS")
    project_root = Path(__file__).resolve().parents[0]
    exe_path = project_root / 'RTKlib' / 'rnx2rtkp.exe'
    
    print(f"conf_path: {conf_path}")
    print(f"work_dir: {work_dir}")
    print(f"exe_path: {exe_path}")
    
    print(f"conf_path exists: {conf_path.exists()}")
    print(f"work_dir exists: {work_dir.exists()}")
    print(f"exe_path exists: {exe_path.exists()}")
    
    if work_dir.exists():
        files = list(work_dir.glob('*'))
        print(f"Fichiers dans work_dir: {len(files)}")
        for f in files[:5]:  # Affiche les 5 premiers
            print(f"  {f.name}")
    
    print("🏁 Test simple terminé")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()



