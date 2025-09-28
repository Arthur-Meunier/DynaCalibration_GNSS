# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 21:33:53 2025

@author: a.meunier
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D

class ConventionAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.ref_data = None
        self.target_data = None
        self.aligned_data = None
        
    def load_data(self):
        """Charge les données des fichiers CSV"""
        print("=== CHARGEMENT DES DONNÉES ===")
        
        # Capteur de référence - Heading
        ref_heading = pd.read_csv(f"{self.data_path}/Thialf-Octans_1-Heading.csv", 
                                 sep=';', parse_dates=['Time'])
        print(f"Heading ref: {len(ref_heading)} points")
        print("Colonnes heading:", ref_heading.columns.tolist())
        print("Exemple heading:", ref_heading.head(3))
        
        # Capteur de référence - Pitch/Roll  
        ref_pitchroll = pd.read_csv(f"{self.data_path}/Thialf-Octans_1-PitchRoll.csv", 
                                   sep=';', parse_dates=['Time'])
        print(f"\nPitch/Roll ref: {len(ref_pitchroll)} points")
        print("Colonnes pitch/roll:", ref_pitchroll.columns.tolist())
        print("Exemple pitch/roll:", ref_pitchroll.head(3))
        
        # Capteur cible
        target = pd.read_csv(f"{self.data_path}/Empire Wind Project_Hydrins1-ins.csv", 
                            sep=';')
        print(f"\nCapteur cible: {len(target)} points")
        print("Colonnes cible:", target.columns.tolist())
        print("Exemple cible:", target.head(3))
        
        # Merge des données de référence
        self.ref_data = pd.merge(ref_heading, ref_pitchroll, on='Time', suffixes=('_h', '_pr'))
        
        # Alignement des données
        min_length = min(len(self.ref_data), len(target))
        
        self.aligned_data = pd.DataFrame({
            'ref_heading': self.ref_data['Heading'][:min_length].values,
            'ref_pitch': self.ref_data['Pitch'][:min_length].values,
            'ref_roll': self.ref_data['Roll'][:min_length].values,
            'target_heading': target['heading'][:min_length].values,
            'target_pitch': target['pitch'][:min_length].values,
            'target_roll': target['roll'][:min_length].values
        }).dropna()
        
        print(f"\n=== RÉSUMÉ ===")
        print(f"Points alignés: {len(self.aligned_data)}")
        return self.aligned_data
    
    def analyze_raw_data(self):
        """Analyse des données brutes pour identifier les conventions"""
        print("\n=== ANALYSE DES DONNÉES BRUTES ===")
        
        for sensor in ['ref', 'target']:
            print(f"\n--- CAPTEUR {sensor.upper()} ---")
            
            for param in ['heading', 'pitch', 'roll']:
                col = f"{sensor}_{param}"
                data = self.aligned_data[col]
                
                print(f"{param.upper()}:")
                print(f"  Min: {data.min():.3f}°")
                print(f"  Max: {data.max():.3f}°") 
                print(f"  Mean: {data.mean():.3f}°")
                print(f"  Std: {data.std():.3f}°")
                print(f"  Range: {data.max() - data.min():.3f}°")
                
                # Détection des plages suspectes
                if param == 'heading':
                    if data.min() < 0:
                        print(f"  ⚠️  Heading négatif détecté (convention -180/+180)")
                    if data.max() > 360:
                        print(f"  ⚠️  Heading > 360° détecté")
                    if data.min() >= 0 and data.max() <= 360:
                        print(f"  ✅  Convention 0-360° probable")
                        
                elif param in ['pitch', 'roll']:
                    if abs(data.mean()) > 10:
                        print(f"  ⚠️  Moyenne élevée, possibleité de biais")
                    if data.std() < 0.1:
                        print(f"  ⚠️  Très peu de mouvement")
                        
    def plot_raw_data_analysis(self):
        """Visualise les données brutes pour identifier les patterns"""
        fig, axes = plt.subplots(3, 4, figsize=(20, 15))
        
        params = ['heading', 'pitch', 'roll']
        sensors = ['ref', 'target']
        
        for i, param in enumerate(params):
            # Séries temporelles
            ax = axes[i, 0]
            for sensor in sensors:
                col = f"{sensor}_{param}"
                ax.plot(self.aligned_data.index[:1000], self.aligned_data[col][:1000], 
                       label=f'{sensor}', alpha=0.8)
            ax.set_title(f'{param.upper()} - Série temporelle (1000 premiers points)')
            ax.set_ylabel(f'{param} (°)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Histogrammes 
            ax = axes[i, 1]
            for sensor in sensors:
                col = f"{sensor}_{param}"
                ax.hist(self.aligned_data[col], bins=50, alpha=0.7, label=f'{sensor}', density=True)
            ax.set_title(f'{param.upper()} - Distribution')
            ax.set_xlabel(f'{param} (°)')
            ax.set_ylabel('Densité')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Scatter plot
            ax = axes[i, 2]
            ax.scatter(self.aligned_data[f'ref_{param}'], self.aligned_data[f'target_{param}'], 
                      s=1, alpha=0.5)
            ax.plot([self.aligned_data[f'ref_{param}'].min(), self.aligned_data[f'ref_{param}'].max()],
                   [self.aligned_data[f'ref_{param}'].min(), self.aligned_data[f'ref_{param}'].max()],
                   'r--', alpha=0.8)
            ax.set_xlabel(f'Référence {param} (°)')
            ax.set_ylabel(f'Cible {param} (°)')
            ax.set_title(f'{param.upper()} - Correlation brute')
            ax.grid(True, alpha=0.3)
            
            # Différences
            ax = axes[i, 3]
            diff = self.aligned_data[f'target_{param}'] - self.aligned_data[f'ref_{param}']
            if param == 'heading':
                # Gestion des angles cycliques pour le heading
                diff = np.array([self.angle_wrap(d) for d in diff])
            ax.hist(diff, bins=50, alpha=0.7, density=True, color='orange')
            ax.set_title(f'{param.upper()} - Différences (Target - Ref)')
            ax.set_xlabel(f'Différence {param} (°)')
            ax.set_ylabel('Densité')
            ax.axvline(diff.mean(), color='red', linestyle='--', label=f'Mean: {diff.mean():.1f}°')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def angle_wrap(self, angle):
        """Wrappe un angle entre -180 et +180"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def test_euler_conventions(self):
        """Teste différentes conventions d'angles d'Euler"""
        print("\n=== TEST DES CONVENTIONS D'EULER ===")
        
        # Conventions courantes à tester
        conventions = [
            'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX',  # Intrinsic
            'xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx'   # Extrinsic
        ]
        
        # Prendre un échantillon pour le test
        sample_size = min(1000, len(self.aligned_data))
        sample_indices = np.random.choice(len(self.aligned_data), sample_size, replace=False)
        
        results = {}
        
        for conv in conventions:
            try:
                # Test avec les données de référence
                ref_angles = self.aligned_data.iloc[sample_indices][['ref_heading', 'ref_pitch', 'ref_roll']].values
                target_angles = self.aligned_data.iloc[sample_indices][['target_heading', 'target_pitch', 'target_roll']].values
                
                # Conversion en matrices de rotation
                R_ref = R.from_euler(conv, ref_angles, degrees=True)
                R_target = R.from_euler(conv, target_angles, degrees=True)
                
                # Test de la différence moyenne
                R_diff = R_ref.inv() * R_target
                angles_diff = R_diff.as_euler(conv, degrees=True)
                
                # Statistiques
                mean_diff = np.mean(np.abs(angles_diff), axis=0)
                std_diff = np.std(angles_diff, axis=0)
                
                results[conv] = {
                    'mean_abs_diff': mean_diff,
                    'std_diff': std_diff,
                    'score': np.sum(mean_diff) + np.sum(std_diff)  # Score de "qualité"
                }
                
                print(f"{conv}: Mean abs diff = [{mean_diff[0]:.2f}, {mean_diff[1]:.2f}, {mean_diff[2]:.2f}]°")
                
            except Exception as e:
                print(f"{conv}: ERREUR - {e}")
                
        # Trouve la meilleure convention
        best_conv = min(results.keys(), key=lambda x: results[x]['score'])
        print(f"\n🎯 MEILLEURE CONVENTION: {best_conv}")
        print(f"Score: {results[best_conv]['score']:.2f}")
        
        return results, best_conv
    
    def analyze_coordinate_systems(self):
        """Analyse les systèmes de coordonnées"""
        print("\n=== ANALYSE DES SYSTÈMES DE COORDONNÉES ===")
        
        # Vérifie les plages d'angles pour identifier les conventions
        print("HEADING:")
        ref_h_range = (self.aligned_data['ref_heading'].min(), self.aligned_data['ref_heading'].max())
        target_h_range = (self.aligned_data['target_heading'].min(), self.aligned_data['target_heading'].max())
        
        print(f"  Référence: [{ref_h_range[0]:.1f}, {ref_h_range[1]:.1f}]")
        print(f"  Cible: [{target_h_range[0]:.1f}, {target_h_range[1]:.1f}]")
        
        if ref_h_range[0] >= 0 and ref_h_range[1] <= 360:
            print("  ✅ Référence: Convention 0-360°")
        elif ref_h_range[0] >= -180 and ref_h_range[1] <= 180:
            print("  ✅ Référence: Convention -180/+180°")
        else:
            print("  ⚠️  Référence: Convention non standard")
            
        if target_h_range[0] >= 0 and target_h_range[1] <= 360:
            print("  ✅ Cible: Convention 0-360°")
        elif target_h_range[0] >= -180 and target_h_range[1] <= 180:
            print("  ✅ Cible: Convention -180/+180°")
        else:
            print("  ⚠️  Cible: Convention non standard")
    
    def correlation_analysis(self):
        """Analyse détaillée des corrélations"""
        print("\n=== ANALYSE DES CORRÉLATIONS ===")
        
        correlations = {}
        
        for param in ['heading', 'pitch', 'roll']:
            ref_col = f'ref_{param}'
            target_col = f'target_{param}'
            
            # Corrélation directe
            corr_direct = np.corrcoef(self.aligned_data[ref_col], self.aligned_data[target_col])[0, 1]
            
            # Pour le heading, teste aussi avec des offsets
            if param == 'heading':
                best_corr = corr_direct
                best_offset = 0
                
                # Teste des offsets de -180 à +180 par pas de 10°
                for offset in range(-180, 181, 10):
                    target_shifted = self.aligned_data[target_col] + offset
                    # Wrappe les angles
                    target_shifted = np.array([self.angle_wrap(angle) for angle in target_shifted])
                    ref_wrapped = np.array([self.angle_wrap(angle) for angle in self.aligned_data[ref_col]])
                    
                    corr = np.corrcoef(ref_wrapped, target_shifted)[0, 1]
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_offset = offset
                
                correlations[param] = {
                    'direct': corr_direct,
                    'best': best_corr,
                    'best_offset': best_offset
                }
                
                print(f"{param.upper()}:")
                print(f"  Corrélation directe: {corr_direct:.4f}")
                print(f"  Meilleure corrélation: {best_corr:.4f} (offset: {best_offset}°)")
                
            else:
                correlations[param] = {'direct': corr_direct}
                print(f"{param.upper()}: {corr_direct:.4f}")
        
        return correlations
    
    def run_full_analysis(self):
        """Exécute l'analyse complète des conventions"""
        self.load_data()
        self.analyze_raw_data()
        self.plot_raw_data_analysis()
        self.analyze_coordinate_systems()
        correlations = self.correlation_analysis()
        euler_results, best_convention = self.test_euler_conventions()
        
        print("\n" + "="*50)
        print("RÉSUMÉ DE L'ANALYSE")
        print("="*50)
        print(f"Meilleure convention d'Euler: {best_convention}")
        print("Corrélations trouvées:")
        for param, corr in correlations.items():
            if 'best' in corr:
                print(f"  {param}: {corr['best']:.4f} (offset: {corr['best_offset']}°)")
            else:
                print(f"  {param}: {corr['direct']:.4f}")
        
        return correlations, euler_results, best_convention

# Utilisation
if __name__ == "__main__":
    # Chemin vers les données
    data_path = r"C:\1-Data\01-Projet\ProjetPY\Thialf\Hy"
    
    # Création de l'analyseur
    analyzer = ConventionAnalyzer(data_path)
    
    # Exécution de l'analyse complète
    correlations, euler_results, best_convention = analyzer.run_full_analysis()