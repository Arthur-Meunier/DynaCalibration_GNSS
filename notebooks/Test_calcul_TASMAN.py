import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import os

class TasmanSimple:
    """
    Version simplifiée pour corriger les problèmes :
    - Utilise les BASELINES GNSS directement (pas les positions absolues)
    - Évite l'estimation de position AFT
    - Synchronisation simple
    - Focus sur la comparaison Octans vs GNSS
    """
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        
        # Géométrie TASMAN - Positions relatives des antennes (coordonnées exactes en mètres)
        # Convention ENU : X=Est→Tribord, Y=Nord→Avant, Z=Up→Haut
        self.antenna_positions = {
            'AFT': np.array([0.0, 0.0, 0.0]),  # Origine (référence)
            'PORT': np.array([-9.34689, 36.276046, 2.603]), 
            'STB': np.array([9.39156, 36.405373, 2.617372])
        }
        
        print("=== GÉOMÉTRIE TASMAN ===")
        for name, pos in self.antenna_positions.items():
            print(f"{name:4}: X={pos[0]:+8.3f}, Y={pos[1]:+8.3f}, Z={pos[2]:+8.3f}")
        
        # Baselines théoriques
        self.baseline_port_stb = self.antenna_positions['STB'] - self.antenna_positions['PORT']
        baseline_length = np.linalg.norm(self.baseline_port_stb)
        print(f"\nBaseline PORT-STB: {baseline_length:.3f}m")
        print(f"Vecteur: X={self.baseline_port_stb[0]:+8.3f}, Y={self.baseline_port_stb[1]:+8.3f}, Z={self.baseline_port_stb[2]:+8.3f}")

    def load_file(self, filename):
        """Charge un fichier de données avec gestion des erreurs"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ Fichier manquant: {filename}")
            return None
        
        try:
            # Essayer plusieurs délimiteurs
            for delim in [',', ';', '\t']:
                try:
                    data = np.loadtxt(filepath, delimiter=delim, skiprows=1)
                    if data.shape[1] >= 4:  # Au moins 4 colonnes
                        print(f"✅ {filename}: {data.shape[0]} lignes, délimiteur '{delim}'")
                        return data
                except:
                    continue
            
            # Si échec, essayer de lire manuellement
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                print(f"❌ {filename}: fichier vide")
                return None
            
            # Détecter le délimiteur de la première ligne de données
            data_line = lines[1].strip()
            if ';' in data_line:
                delim = ';'
            elif ',' in data_line:
                delim = ','
            else:
                delim = ' '
            
            # Parser manuellement
            data_rows = []
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(delim)
                if len(parts) >= 4:
                    try:
                        # Convertir en float en remplaçant les virgules par des points
                        row = [float(p.replace(',', '.')) for p in parts[:4]]
                        data_rows.append(row)
                    except:
                        continue
            
            if data_rows:
                data = np.array(data_rows)
                print(f"✅ {filename}: {len(data_rows)} lignes (parsing manuel)")
                return data
            else:
                print(f"❌ {filename}: aucune donnée valide")
                return None
                
        except Exception as e:
            print(f"❌ {filename}: erreur {e}")
            return None

    def load_all_data(self):
        """Charge toutes les données"""
        print("\n=== CHARGEMENT DES DONNÉES ===")
        
        # Charger les fichiers
        self.octans = self.load_file("Octans.txt")
        self.port_gnss = self.load_file("Port_AftFixe.csv") 
        self.stb_gnss = self.load_file("Stb_AftFixe.csv")
        
        # Vérifier que tous les fichiers sont chargés
        if self.octans is None or self.port_gnss is None or self.stb_gnss is None:
            print("❌ Échec du chargement")
            return False
        
        # Afficher les plages temporelles
        print(f"\n=== PLAGES TEMPORELLES ===")
        print(f"Octans: {self.octans[0,0]:.1f} → {self.octans[-1,0]:.1f}s")
        print(f"Port:   {self.port_gnss[0,0]:.1f} → {self.port_gnss[-1,0]:.1f}s") 
        print(f"Stb:    {self.stb_gnss[0,0]:.1f} → {self.stb_gnss[-1,0]:.1f}s")
        
        # Trouver la plage commune
        t_start = max(self.octans[0,0], self.port_gnss[0,0], self.stb_gnss[0,0])
        t_end = min(self.octans[-1,0], self.port_gnss[-1,0], self.stb_gnss[-1,0])
        
        if t_end > t_start:
            print(f"✅ Chevauchement: {t_start:.1f} → {t_end:.1f}s ({t_end-t_start:.1f}s)")
            self.time_range = (t_start, t_end)
            return True
        else:
            print(f"❌ Pas de chevauchement temporel")
            return False

    def synchronize_data(self, n_points=50):
        """Synchronisation simple par interpolation"""
        print(f"\n=== SYNCHRONISATION ({n_points} points) ===")
        
        t_start, t_end = self.time_range
        time_grid = np.linspace(t_start, t_end, n_points)
        
        # Interpoler chaque dataset
        self.sync_time = time_grid
        
        # Octans: interpoler heading, pitch, roll
        self.sync_octans = np.zeros((n_points, 3))
        for i in range(3):
            self.sync_octans[:, i] = np.interp(time_grid, self.octans[:, 0], self.octans[:, i+1])
        
        # GNSS Port: interpoler E, N, h
        self.sync_port = np.zeros((n_points, 3))
        for i in range(3):
            self.sync_port[:, i] = np.interp(time_grid, self.port_gnss[:, 0], self.port_gnss[:, i+1])
        
        # GNSS Stb: interpoler E, N, h  
        self.sync_stb = np.zeros((n_points, 3))
        for i in range(3):
            self.sync_stb[:, i] = np.interp(time_grid, self.stb_gnss[:, 0], self.stb_gnss[:, i+1])
        
        print("✅ Synchronisation terminée")
        return True

    def compute_gnss_attitude(self):
        """Calcule l'attitude à partir des baselines GNSS observées"""
        print("\n=== CALCUL ATTITUDE GNSS ===")
        
        n_points = len(self.sync_time)
        self.gnss_attitude = np.zeros((n_points, 3))  # heading, pitch, roll
        
        errors = 0
        for i in range(n_points):
            try:
                # Baseline observée GNSS (STB - PORT)
                baseline_obs = self.sync_stb[i] - self.sync_port[i]  # [ΔE, ΔN, Δh]
                
                # Longueur de la baseline (vérification)
                length_obs = np.linalg.norm(baseline_obs)
                length_theo = np.linalg.norm(self.baseline_port_stb)
                
                # Vérifier la cohérence des longueurs
                if abs(length_obs - length_theo) > 1.0:  # Plus de 1m d'écart
                    raise ValueError(f"Baseline incohérente: {length_obs:.3f}m vs {length_theo:.3f}m")
                
                # Méthode simplifiée : calcul direct des angles
                # Cap depuis la baseline horizontale
                heading = np.arctan2(baseline_obs[1], baseline_obs[0]) * 180/np.pi  # E→N
                
                # Ajustement pour correspondre à la géométrie TASMAN
                # La baseline TASMAN a un cap théorique
                baseline_theo_heading = np.arctan2(self.baseline_port_stb[1], self.baseline_port_stb[0]) * 180/np.pi
                
                # Le cap du navire est le cap observé moins le cap théorique de la baseline
                heading_navire = heading - baseline_theo_heading
                
                # Normaliser l'angle
                while heading_navire > 180:
                    heading_navire -= 360
                while heading_navire < -180:
                    heading_navire += 360
                
                # Tangage et roulis depuis les composantes verticales (approximation)
                # Pour une approximation simple, utiliser les différences de hauteur
                dh = baseline_obs[2]  # Différence de hauteur STB-PORT
                dx = baseline_obs[0]  # Différence Est (≈ tribord-bâbord)
                
                # Roll: si STB plus haut que PORT → roulis tribord (négatif en convention ENU)
                roll = -np.arctan2(dh, abs(dx)) * 180/np.pi
                
                # Pitch: plus complexe, utiliser une approximation
                dy = baseline_obs[1]  # Différence Nord (≈ avant-arrière)
                pitch = 0.0  # Approximation pour l'instant
                
                self.gnss_attitude[i] = [heading_navire, pitch, roll]
                
            except Exception as e:
                if errors < 5:
                    print(f"Erreur point {i}: {e}")
                self.gnss_attitude[i] = [np.nan, np.nan, np.nan]
                errors += 1
        
        # Compter les points valides
        valid_mask = ~np.isnan(self.gnss_attitude[:, 0])
        n_valid = np.sum(valid_mask)
        
        print(f"✅ {n_valid}/{n_points} estimations réussies ({errors} erreurs)")
        
        if n_valid < n_points * 0.5:
            print("⚠️ Beaucoup d'erreurs - Vérifier les données")
            return False
        
        return True

    def analyze_results(self):
        """Analyse les résultats"""
        print("\n=== ANALYSE DES RÉSULTATS ===")
        
        # Masque pour les données valides
        valid_mask = ~np.isnan(self.gnss_attitude[:, 0])
        
        if np.sum(valid_mask) == 0:
            print("❌ Aucune donnée valide")
            return False
        
        # Données valides seulement
        octans_valid = self.sync_octans[valid_mask]
        gnss_valid = self.gnss_attitude[valid_mask]
        
        # Calculer les erreurs
        def angle_diff(a1, a2):
            """Différence angulaire avec gestion de la circularité"""
            diff = a1 - a2
            return np.where(diff > 180, diff - 360, np.where(diff < -180, diff + 360, diff))
        
        errors = np.zeros_like(gnss_valid)
        errors[:, 0] = angle_diff(gnss_valid[:, 0], octans_valid[:, 0])  # Heading
        errors[:, 1] = gnss_valid[:, 1] - octans_valid[:, 1]  # Pitch
        errors[:, 2] = gnss_valid[:, 2] - octans_valid[:, 2]  # Roll
        
        # Statistiques
        angle_names = ['Heading', 'Pitch', 'Roll']
        print(f"\n{'Angle':<8} {'RMS':<8} {'Moyenne':<10} {'Std':<8} {'Max':<8}")
        print("-" * 45)
        
        self.stats = {}
        for i, name in enumerate(angle_names):
            rms = np.sqrt(np.mean(errors[:, i]**2))
            mean = np.mean(errors[:, i])
            std = np.std(errors[:, i])
            max_err = np.max(np.abs(errors[:, i]))
            
            self.stats[name.lower()] = {'rms': rms, 'mean': mean, 'std': std, 'max': max_err}
            print(f"{name:<8} {rms:7.3f}° {mean:+9.3f}° {std:7.3f}° {max_err:7.3f}°")
        
        # Stockage pour graphiques
        self.results = {
            'time': self.sync_time[valid_mask],
            'octans': octans_valid,
            'gnss': gnss_valid,
            'errors': errors
        }
        
        return True

    def plot_results(self):
        """Affiche les graphiques de comparaison"""
        if not hasattr(self, 'results'):
            print("❌ Pas de résultats à afficher")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('TASMAN - Comparaison Octans vs GNSS', fontsize=14)
        
        time_data = self.results['time']
        octans = self.results['octans']
        gnss = self.results['gnss']
        errors = self.results['errors']
        
        angle_names = ['Heading (Cap)', 'Pitch (Tangage)', 'Roll (Roulis)']
        colors = ['blue', 'red', 'green']
        
        for i in range(3):
            # Comparaison
            ax1 = axes[0, i]
            ax1.plot(time_data, octans[:, i], color=colors[i], label='Octans', linewidth=2)
            ax1.plot(time_data, gnss[:, i], color='orange', linestyle='--', 
                    label='GNSS', linewidth=2, alpha=0.8)
            ax1.set_title(angle_names[i])
            ax1.set_ylabel('Angle (°)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Erreur
            ax2 = axes[1, i]
            ax2.plot(time_data, errors[:, i], color='red', linewidth=1)
            rms = self.stats[['heading', 'pitch', 'roll'][i]]['rms']
            ax2.set_title(f'Erreur - RMS: {rms:.3f}°')
            ax2.set_ylabel('Erreur (°)')
            ax2.set_xlabel('Temps (s)')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Évaluation finale
        print(f"\n🎯 ÉVALUATION:")
        rms_heading = self.stats['heading']['rms']
        rms_pitch = self.stats['pitch']['rms']
        rms_roll = self.stats['roll']['rms']
        
        if rms_heading < 2.0 and rms_roll < 2.0:
            print("✅ Résultats acceptables")
        else:
            print("⚠️ Résultats à améliorer")
            
            # Diagnostic
            print("\n🔍 DIAGNOSTIC:")
            if rms_heading > 10.0:
                print("- Cap: Erreur massive → Problème de référentiel Nord/Est")
            if rms_roll > 10.0:
                print("- Roulis: Erreur massive → Convention Port/Starboard")
            
            # Afficher quelques valeurs pour debug
            print("\nExemples de valeurs:")
            print("Octans → GNSS (3 premiers points)")
            for i in range(min(3, len(octans))):
                print(f"H:{octans[i,0]:6.1f}°→{gnss[i,0]:6.1f}° "
                      f"P:{octans[i,1]:+5.2f}°→{gnss[i,1]:+5.2f}° "
                      f"R:{octans[i,2]:+5.2f}°→{gnss[i,2]:+5.2f}°")

    def run_analysis(self):
        """Lance l'analyse complète"""
        print("=== ANALYSE TASMAN SIMPLIFIÉE ===")
        
        if not self.load_all_data():
            return False
        
        if not self.synchronize_data():
            return False
        
        if not self.compute_gnss_attitude():
            return False
        
        if not self.analyze_results():
            return False
        
        self.plot_results()
        return True

# Script principal
if __name__ == "__main__":
    # Chemin vers les données
    data_path = input("Entrez le chemin vers les données TASMAN (ou Entrée pour défaut): ").strip()
    
    if not data_path:
        data_path = r"C:\1-Data\01-Projet\ProjetPY\Calcul\CalibArthur\DonneeTASMAN\CalculCinematique03"
    
    print(f"Répertoire: {data_path}")
    
    if not os.path.exists(data_path):
        print(f"❌ Répertoire non trouvé: {data_path}")
        input("Appuyez sur Entrée...")
        exit(1)
    
    try:
        analyzer = TasmanSimple(data_path)
        analyzer.run_analysis()
        
        print("\n✅ ANALYSE TERMINÉE")
        
    except Exception as e:
        print(f"💥 ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour fermer...")