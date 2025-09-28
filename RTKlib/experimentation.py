import subprocess
import os
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import time
import threading
import re

class DualGNSSProcessor:
    def __init__(self):
        # Chemins principaux
        self.data_path = Path(r"C:\1-Data\01-Projet\ProjetPY\Thialf\2")
        self.rtklib_path = Path(r"C:\1-Data\01-Projet\ProjetPY\DynaCalibration_GNSS\RTKlib")
        self.config_path = self.rtklib_path / "configs" / "conf.conf"
        self.export_path = self.data_path / "export"
        
        # Chercher l'exécutable RTKLIB
        possible_exes = ["rtkpos.exe", "rnx2rtkp.exe"]
        self.exe_path = None
        self.exe_name = None
        
        for exe_name in possible_exes:
            exe_path = self.rtklib_path / exe_name
            if exe_path.exists():
                self.exe_path = exe_path
                self.exe_name = exe_name
                break
        
        # Fichiers communs (base + corrections)
        self.common_files = {
            'base_obs': self.data_path / "Bow-9205.25O",                               # Base observation  
            'base_glo': self.data_path / "Bow-9205.25g",                               # Base GLONASS
            'orbit': self.data_path / "COD0MGXFIN_20250090000_01D_05M_ORB.SP3",       # Orbites précises
            'clock': self.data_path / "COD0OPSRAP_20250090000_01D_30S_CLK.CLK",       # Corrections horloge
            'base_nav': self.data_path / "Bow-9205.25n",                               # Base navigation
            'antenna': self.data_path / "igs20.atx"                                    # Fichier antenne
        }
        
        # Rovers à traiter
        self.rovers = {
            'Port': {
                'obs_file': self.data_path / "Port-9205.25O",
                'name': "Port (Bâbord)",
                'output_suffix': "Port"
            },
            'Stbd': {
                'obs_file': self.data_path / "Stbd-9205.25O", 
                'name': "Stbd (Tribord)",
                'output_suffix': "Stbd"
            }
        }
    
    def check_files(self):
        """Vérifie que tous les fichiers nécessaires existent"""
        print("=== Vérification des fichiers ===")
        print("Configuration Dual RTK:")
        print("  🏠 Base (fixe): Bow (.O, .n, .g)")
        print("  📍 Rover 1: Port (.O) - Bâbord")
        print("  📍 Rover 2: Stbd (.O) - Tribord") 
        print("  🛰️ Corrections: SP3, CLK, ATX (partagées)")
        print()
        
        missing_files = []
        
        # Vérifier RTKLIB
        if self.exe_path is None:
            missing_files.append("RTKLIB: aucun exécutable trouvé (rtkpos.exe ou rnx2rtkp.exe)")
        else:
            print(f"✅ RTKLIB trouvé: {self.exe_name}")
        
        # Vérifier le fichier de configuration
        if not self.config_path.exists():
            missing_files.append(f"Config: {self.config_path}")
        else:
            print(f"✅ Configuration trouvée: {self.config_path}")
        
        # Vérifier les fichiers communs
        print("\n📁 Fichiers communs:")
        for name, path in self.common_files.items():
            if not path.exists():
                missing_files.append(f"{name}: {path}")
            else:
                size = path.stat().st_size
                print(f"  ✅ {name}: {path.name} ({size:,} bytes)")
        
        # Vérifier les fichiers rovers
        print("\n📍 Fichiers rovers:")
        for rover_id, rover_info in self.rovers.items():
            obs_file = rover_info['obs_file']
            if not obs_file.exists():
                missing_files.append(f"{rover_id}: {obs_file}")
            else:
                size = obs_file.stat().st_size
                print(f"  ✅ {rover_info['name']}: {obs_file.name} ({size:,} bytes)")
        
        if missing_files:
            print("\n❌ Fichiers manquants:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        print("\n✅ Tous les fichiers sont présents!")
        return True
    
    def get_rinex_time_span(self, obs_file):
        """Extrait la période de temps d'un fichier RINEX"""
        try:
            with open(obs_file, 'r') as f:
                lines = f.readlines()
            
            start_time = None
            end_time = None
            interval = 1.0
            
            for line in lines:
                if 'TIME OF FIRST OBS' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        year, month, day, hour, minute = map(int, parts[:5])
                        second = int(float(parts[5]))
                        start_time = datetime(year, month, day, hour, minute, second)
                
                elif 'TIME OF LAST OBS' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        year, month, day, hour, minute = map(int, parts[:5])
                        second = int(float(parts[5]))
                        end_time = datetime(year, month, day, hour, minute, second)
                
                elif 'INTERVAL' in line:
                    match = re.search(r'(\d+\.?\d*)', line)
                    if match:
                        interval = float(match.group(1))
                
                elif 'END OF HEADER' in line:
                    break
            
            if start_time and end_time:
                total_duration = (end_time - start_time).total_seconds()
                expected_solutions = int(total_duration / interval) + 1
                return start_time, end_time, interval, expected_solutions
            
        except Exception as e:
            print(f"⚠️ Erreur analyse {obs_file.name}: {e}")
        
        return None, None, 1.0, 0
    
    def monitor_single_process(self, rover_id, rover_name, output_file, expected_solutions, process):
        """Monitoring d'un seul processus RTKLIB"""
        
        estimated_duration = 120  # secondes
        start_time = time.time()
        milestones = [25, 50, 75, 100]
        milestone_times = [estimated_duration * m / 100 for m in milestones]
        milestones_shown = set()
        
        print(f"\n📊 {rover_name}: Traitement en cours...")
        print(f"   🎯 Estimation: ~{estimated_duration}s pour {expected_solutions:,} solutions")
        
        while process.poll() is None:
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Vérifier les étapes importantes
                for i, milestone_time in enumerate(milestone_times):
                    milestone_percent = milestones[i]
                    
                    if elapsed >= milestone_time and milestone_percent not in milestones_shown:
                        if milestone_percent == 25:
                            message = f"{rover_name}: Initialisation terminée"
                        elif milestone_percent == 50:
                            message = f"{rover_name}: Calculs GNSS en cours"
                        elif milestone_percent == 75:
                            message = f"{rover_name}: Finalisation proche"
                        elif milestone_percent == 100:
                            message = f"{rover_name}: Phase finale"
                        
                        print(f"   🔄 {message} ({elapsed:.0f}s)")
                        milestones_shown.add(milestone_percent)
                
                time.sleep(2.0)  # Vérifier toutes les 2 secondes
                
            except Exception as e:
                print(f"⚠️ Erreur monitoring {rover_name}: {e}")
                break
        
        # Processus terminé
        final_elapsed = time.time() - start_time
        print(f"   ✅ {rover_name}: Terminé ! ({final_elapsed:.1f}s)")
        
        return final_elapsed
    
    def process_single_rover(self, rover_id, rover_info):
        """Lance le traitement pour un seul rover"""
        
        # Analyser la période des données
        start_time, end_time, interval, expected_solutions = self.get_rinex_time_span(rover_info['obs_file'])
        
        # Nom du fichier de sortie avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.export_path / f"Thialf_RTK_{rover_info['output_suffix']}_{timestamp}.pos"
        
        # Construction de la commande RTKLIB
        cmd = [
            str(self.exe_path),
            "-k", str(self.config_path),  # Fichier de configuration
            "-o", str(output_file),       # Fichier de sortie
            # Ordre spécifique des fichiers d'entrée :
            str(rover_info['obs_file']),         # Rover observation
            str(self.common_files['base_obs']),  # Base observation
            str(self.common_files['base_glo']),  # Base GLONASS
            str(self.common_files['orbit']),     # Orbites précises
            str(self.common_files['clock']),     # Corrections horloge
            str(self.common_files['base_nav']),  # Base navigation
        ]
        
        # Ajouter le fichier antenne s'il existe
        if self.common_files['antenna'].exists():
            cmd.extend(["-a", str(self.common_files['antenna'])])
        
        try:
            # Lancer RTKLIB en arrière-plan
            process = subprocess.Popen(
                cmd,
                cwd=self.rtklib_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Lancer le monitoring dans un thread
            monitor_thread = threading.Thread(
                target=self.monitor_single_process,
                args=(rover_id, rover_info['name'], output_file, expected_solutions, process),
                daemon=True
            )
            monitor_thread.start()
            
            # Attendre la fin du processus
            stdout, stderr = process.communicate(timeout=600)  # 10 minutes max
            
            # Attendre que le monitoring se termine
            monitor_thread.join(timeout=3)
            
            # Analyser le résultat
            if process.returncode == 0:
                time.sleep(1)  # Attendre finalisation
                
                if output_file.exists():
                    # Compter les solutions finales
                    try:
                        with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        final_solutions = sum(1 for line in lines if not line.startswith('%') and line.strip())
                        file_size = output_file.stat().st_size
                        
                        return {
                            'success': True,
                            'output_file': output_file,
                            'solutions': final_solutions,
                            'size': file_size,
                            'rover_name': rover_info['name']
                        }
                    except Exception as e:
                        print(f"⚠️ Erreur lecture résultats {rover_info['name']}: {e}")
                
                return {'success': False, 'error': 'Fichier de sortie introuvable', 'rover_name': rover_info['name']}
            else:
                return {'success': False, 'error': f'Code erreur {process.returncode}', 'rover_name': rover_info['name']}
                
        except subprocess.TimeoutExpired:
            process.kill()
            return {'success': False, 'error': 'Timeout', 'rover_name': rover_info['name']}
        except Exception as e:
            return {'success': False, 'error': str(e), 'rover_name': rover_info['name']}
    
    def create_export_directory(self):
        """Crée le dossier d'export s'il n'existe pas"""
        if not self.export_path.exists():
            self.export_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Dossier d'export créé: {self.export_path}")
        else:
            print(f"✅ Dossier d'export existe: {self.export_path}")
    
    def run_dual_processing(self):
        """Lance le traitement dual en parallèle"""
        print("🚀 Début du traitement GNSS Dual")
        print("=" * 60)
        
        # Étape 1: Vérification des fichiers
        if not self.check_files():
            print("❌ Impossible de continuer - fichiers manquants")
            return False
        
        # Étape 2: Création du dossier d'export
        self.create_export_directory()
        
        # Étape 3: Affichage période des données
        print("\n=== Analyse des périodes de données ===")
        for rover_id, rover_info in self.rovers.items():
            start_time, end_time, interval, expected = self.get_rinex_time_span(rover_info['obs_file'])
            if start_time and end_time:
                duration = (end_time - start_time).total_seconds()
                print(f"{rover_info['name']}: {start_time.strftime('%H:%M:%S')} → {end_time.strftime('%H:%M:%S')} ({duration/3600:.1f}h, {expected:,} solutions)")
        
        # Étape 4: Lancement dual
        print(f"\n=== Traitement RTK Dual ===")
        print(f"Exécutable utilisé: {self.exe_name}")
        print("🚀 Lancement des deux traitements en parallèle...")
        
        start_dual_time = time.time()
        
        # Créer les threads pour traiter les deux rovers
        results = {}
        threads = {}
        
        for rover_id, rover_info in self.rovers.items():
            thread = threading.Thread(
                target=lambda r_id=rover_id, r_info=rover_info: results.update({r_id: self.process_single_rover(r_id, r_info)}),
                daemon=False
            )
            threads[rover_id] = thread
            thread.start()
        
        # Attendre que les deux threads se terminent
        for rover_id, thread in threads.items():
            thread.join()
        
        total_dual_time = time.time() - start_dual_time
        
        # Étape 5: Analyse des résultats
        print(f"\n=== Résultats du traitement dual ===")
        print(f"⏱️ Temps total dual: {total_dual_time:.1f}s")
        print()
        
        success_count = 0
        for rover_id, result in results.items():
            if result['success']:
                success_count += 1
                print(f"✅ {result['rover_name']}: {result['solutions']:,} solutions")
                print(f"   📄 Fichier: {result['output_file'].name} ({result['size']:,} bytes)")
            else:
                print(f"❌ {result['rover_name']}: Échec - {result['error']}")
        
        if success_count == 2:
            print(f"\n🎉 Traitement dual terminé avec succès!")
            print(f"📁 Résultats disponibles dans: {self.export_path}")
            estimated_single_time = total_dual_time * 2
            time_saved = estimated_single_time - total_dual_time
            print(f"⚡ Temps économisé vs séquentiel: ~{time_saved:.0f}s ({time_saved/60:.1f}min)")
            return True
        else:
            print(f"\n⚠️ Traitement dual partiellement réussi ({success_count}/2)")
            return False

def main():
    """Fonction principale"""
    print("🛰️ Traitement GNSS Thialf - Mode Dual (Port + Stbd)")
    print("===================================================")
    print("Configuration RTK Dual:")
    print("  🏠 Base commune: Bow (.O, .n, .g)")
    print("  📍 Rover 1: Port (.O) - Bâbord") 
    print("  📍 Rover 2: Stbd (.O) - Tribord")
    print("  🛰️ Corrections: SP3, CLK, ATX (partagées)")
    print("  ⚡ Mode: Traitement parallèle simultané")
    print("  ⏱️ Estimation: ~120s (au lieu de 240s séquentiel)")
    print()
    
    processor = DualGNSSProcessor()
    success = processor.run_dual_processing()
    
    if success:
        print("\n💡 Prochaines étapes:")
        print("   1. Vérifiez les 2 fichiers .pos dans export/")
        print("   2. Comparez les positions Port vs Stbd")
        print("   3. Analysez la précision relative entre les rovers")
    else:
        print("\n🔧 En cas de problème:")
        print("   1. Vérifiez que Stbd-9205.25O existe bien")
        print("   2. Consultez les messages d'erreur ci-dessus") 
        print("   3. Essayez le mode simple si dual pose problème")

if __name__ == "__main__":
    main()