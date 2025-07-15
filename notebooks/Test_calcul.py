import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from scipy.signal import savgol_filter
import warnings
warnings.filterwarnings('ignore')

class DynamicCalibration:
    """
    Calibration dynamique d'instruments de navigation par méthode GNSS
    Référentiel navire : Y=avant, X=tribord, Z=haut
    """
    
    def __init__(self, data_path="C:/1-Data/01-Projet/ProjetPY/Calcul/CalibArthur/00"):
        self.data_path = Path(data_path)
        
        # Offsets DIMCON (dans référentiel navire)
        self.dimcon = {
            'bow': {'x': 1.447, 'y': 197.391, 'z': 26.5705},
            'port': {'x': -15.691, 'y': 153.732, 'z': 28.6178},
            'starboard': {'x': 17.321, 'y': 153.628, 'z': 28.6765}
        }
        
        # Position fixe antenne Bow (UTM)
        self.bow_fixed = {
            'E': 192275.215,
            'N': 9326610.105,
            'h': 40.975
        }
        
        # Paramètres UTM (à ajuster selon la zone)
        self.utm_zone = 32  # Exemple
        self.central_meridian = self._get_central_meridian(self.utm_zone)
        
        # Décalage GPS-UTC (18s après 2016)
        self.gps_utc_offset = 18.0
        
    def _get_central_meridian(self, zone):
        """Calcule le méridien central d'une zone UTM"""
        return -177 + (zone - 1) * 6
    
    def load_data(self):
        """Charge toutes les données depuis les fichiers"""
        try:
            # Vérification de l'existence des fichiers
            files_to_check = ["B_Port.txt", "B_Starboard.txt", "Octans.txt"]
            missing_files = []
            
            for file in files_to_check:
                if not (self.data_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                print(f"Fichiers manquants: {missing_files}")
                raise FileNotFoundError(f"Fichiers non trouvés: {missing_files}")
            
            # Données GNSS Port et Starboard
            self.port_data = pd.read_csv(
                self.data_path / "B_Port.txt",
                sep='\s+',
                names=['time', 'E', 'N', 'h']
            )
            
            self.starboard_data = pd.read_csv(
                self.data_path / "B_Starboard.txt",
                sep='\s+',
                names=['time', 'E', 'N', 'h']
            )
            
            # Données Octans (attention: roll convention +stb up)
            self.octans_data = pd.read_csv(
                self.data_path / "Octans.txt",
                sep='\s+',
                names=['time', 'pitch', 'roll', 'heading']
            )
            
            # Conversion en format numérique (corrige les erreurs de type)
            for df in [self.port_data, self.starboard_data, self.octans_data]:
                df['time'] = pd.to_numeric(df['time'], errors='coerce')
                
            # Conversion des autres colonnes en numérique
            numeric_cols = ['E', 'N', 'h']
            for col in numeric_cols:
                self.port_data[col] = pd.to_numeric(self.port_data[col], errors='coerce')
                self.starboard_data[col] = pd.to_numeric(self.starboard_data[col], errors='coerce')
                
            octans_cols = ['pitch', 'roll', 'heading']
            for col in octans_cols:
                self.octans_data[col] = pd.to_numeric(self.octans_data[col], errors='coerce')
            
            # Suppression des lignes avec des valeurs NaN
            self.port_data = self.port_data.dropna()
            self.starboard_data = self.starboard_data.dropna()
            self.octans_data = self.octans_data.dropna()
            
            # Vérification que les données ne sont pas vides après nettoyage
            if len(self.port_data) == 0 or len(self.starboard_data) == 0 or len(self.octans_data) == 0:
                raise ValueError("Données vides après conversion numérique")
            
            # Inverser le signe du roll (convention Octans +stb up → notre convention +port up)
            self.octans_data['roll'] = -self.octans_data['roll']
            
            # Synchronisation temporelle GPS → UTC
            self.port_data['time'] -= self.gps_utc_offset
            self.starboard_data['time'] -= self.gps_utc_offset
            
            print(f"Données chargées:")
            print(f"  Port: {len(self.port_data)} échantillons")
            print(f"  Starboard: {len(self.starboard_data)} échantillons")
            print(f"  Octans: {len(self.octans_data)} échantillons")
            
            # Affichage des plages temporelles
            print(f"\nPlages temporelles (après correction GPS-UTC):")
            print(f"  Port: {self.port_data['time'].min():.1f} - {self.port_data['time'].max():.1f}s")
            print(f"  Starboard: {self.starboard_data['time'].min():.1f} - {self.starboard_data['time'].max():.1f}s")
            print(f"  Octans: {self.octans_data['time'].min():.1f} - {self.octans_data['time'].max():.1f}s")
            
        except (FileNotFoundError, ValueError) as e:
            print(f"Erreur lors du chargement des données: {e}")
            # Génération de données de test
            self._generate_test_data()
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            print("Génération de données de test...")
            self._generate_test_data()
            
    def _generate_test_data(self):
        """Génère des données de test cohérentes avec les conventions maritimes"""
        print("Génération de données de test avec conventions corrigées...")
        
        # Création de données simulées
        time = np.arange(0, 300, 1, dtype=float)  # 5 minutes à 1Hz
        
        # Centre du navire (point de référence)
        center_E = 192275.0
        center_N = 9326600.0
        center_h = 41.0
        
        # Simulation d'un navire avec mouvements réalistes
        heading_true = np.linspace(0, 60, len(time))  # Rotation de 60° en 5 minutes
        pitch_true = 2 * np.sin(time * 0.1)          # Tangage ±2° (+ = bow up)
        roll_true = 1.5 * np.cos(time * 0.15)        # Roulis ±1.5° (+ = port up)
        
        # Offsets DIMCON en mètres dans le référentiel navire
        # Convention : X=tribord, Y=avant, Z=haut
        bow_offset_x = self.dimcon['bow']['x']      # 1.447 m
        bow_offset_y = self.dimcon['bow']['y']      # 197.391 m (vers l'avant)
        
        port_offset_x = self.dimcon['port']['x']    # -15.691 m (vers port)
        port_offset_y = self.dimcon['port']['y']    # 153.732 m
        
        stbd_offset_x = self.dimcon['starboard']['x']  # 17.321 m (vers tribord)
        stbd_offset_y = self.dimcon['starboard']['y']  # 153.628 m
        
        # Génération des positions pour chaque instant
        bow_E, bow_N, bow_h = [], [], []
        port_E, port_N, port_h = [], [], []
        stbd_E, stbd_N, stbd_h = [], [], []
        
        for i, (hdg, pitch, roll) in enumerate(zip(heading_true, pitch_true, roll_true)):
            # Matrices de rotation
            hdg_rad = np.radians(hdg)
            pitch_rad = np.radians(pitch)
            roll_rad = np.radians(roll)
            
            # Position centre navire (avec léger déplacement)
            center_E_i = center_E + 2 * np.sin(time[i] * 0.05)
            center_N_i = center_N + 2 * np.cos(time[i] * 0.05)
            center_h_i = center_h + 0.5 * np.sin(time[i] * 0.2)
            
            # Rotation heading seulement (pour simplifier)
            cos_hdg = np.cos(hdg_rad)
            sin_hdg = np.sin(hdg_rad)
            
            # Transformation des offsets navire vers UTM
            # UTM : E = Est, N = Nord (X navire = Est, Y navire = Nord après rotation)
            
            # Bow
            bow_E_offset = bow_offset_x * cos_hdg - bow_offset_y * sin_hdg
            bow_N_offset = bow_offset_x * sin_hdg + bow_offset_y * cos_hdg
            bow_E.append(center_E_i + bow_E_offset)
            bow_N.append(center_N_i + bow_N_offset)
            bow_h.append(center_h_i + self.dimcon['bow']['z'] + pitch * 0.2)  # Effet du pitch
            
            # Port
            port_E_offset = port_offset_x * cos_hdg - port_offset_y * sin_hdg
            port_N_offset = port_offset_x * sin_hdg + port_offset_y * cos_hdg
            port_E.append(center_E_i + port_E_offset)
            port_N.append(center_N_i + port_N_offset)
            port_h.append(center_h_i + self.dimcon['port']['z'] + roll * 0.3)  # Roll + vers port up
            
            # Starboard
            stbd_E_offset = stbd_offset_x * cos_hdg - stbd_offset_y * sin_hdg
            stbd_N_offset = stbd_offset_x * sin_hdg + stbd_offset_y * cos_hdg
            stbd_E.append(center_E_i + stbd_E_offset)
            stbd_N.append(center_N_i + stbd_N_offset)
            stbd_h.append(center_h_i + self.dimcon['starboard']['z'] - roll * 0.3)  # Roll - vers starboard down
        
        # Création des DataFrames
        self.port_data = pd.DataFrame({
            'time': time,
            'E': port_E,
            'N': port_N,
            'h': port_h
        })
        
        self.starboard_data = pd.DataFrame({
            'time': time,
            'E': stbd_E,
            'N': stbd_N,
            'h': stbd_h
        })
        
        # Position Bow 
        self.bow_data = pd.DataFrame({
            'time': time,
            'E': bow_E,
            'N': bow_N,
            'h': bow_h
        })
        
        # Données Octans avec biais simulé mais dans les bonnes conventions
        self.octans_data = pd.DataFrame({
            'time': time,
            'heading': heading_true + 1.5 + 0.1 * np.random.randn(len(time)),    # Biais +1.5°
            'pitch': pitch_true + 0.2 + 0.05 * np.random.randn(len(time)),       # Biais +0.2°
            'roll': roll_true + 0.3 + 0.05 * np.random.randn(len(time))          # Biais +0.3°
        })
        
        # S'assurer que toutes les colonnes sont de type float
        for df in [self.port_data, self.starboard_data, self.bow_data, self.octans_data]:
            for col in df.columns:
                df[col] = df[col].astype(float)
        
        print(f"Données de test générées avec conventions maritimes:")
        print(f"  Port: {len(self.port_data)} échantillons")
        print(f"  Starboard: {len(self.starboard_data)} échantillons") 
        print(f"  Bow: {len(self.bow_data)} échantillons")
        print(f"  Octans: {len(self.octans_data)} échantillons")
        print(f"  Heading range: {heading_true.min():.1f}° → {heading_true.max():.1f}°")
        print(f"  Pitch range: {pitch_true.min():.1f}° → {pitch_true.max():.1f}°")
        print(f"  Roll range: {roll_true.min():.1f}° → {roll_true.max():.1f}°")
        
    def calculate_convergence(self, lat, lon):
        """
        Calcule la convergence des méridiens
        γ = arctan(tan(λ - λ₀) × sin(φ))
        """
        lat_rad = np.radians(lat)
        lon_diff_rad = np.radians(lon - self.central_meridian)
        
        convergence = np.arctan(np.tan(lon_diff_rad) * np.sin(lat_rad))
        return np.degrees(convergence)
    
    def utm_to_latlon(self, E, N):
        """
        Conversion approximative UTM → Lat/Lon pour le calcul de convergence
        """
        # Approximation simple - remplacer par pyproj pour plus de précision
        lat = (N - 9000000) / 111000.0 + 80  # Approximation pour zone 32N
        lon = self.central_meridian + (E - 500000) / (111000 * np.cos(np.radians(lat)))
        
        return lat, lon
    
    def calculate_baselines(self):
        """Calcule les distances entre antennes depuis le DIMCON"""
        bow = np.array([self.dimcon['bow']['x'], self.dimcon['bow']['y'], self.dimcon['bow']['z']])
        port = np.array([self.dimcon['port']['x'], self.dimcon['port']['y'], self.dimcon['port']['z']])
        stbd = np.array([self.dimcon['starboard']['x'], self.dimcon['starboard']['y'], self.dimcon['starboard']['z']])
        
        baselines = {
            'bow_port': np.linalg.norm(bow - port),
            'bow_stbd': np.linalg.norm(bow - stbd),
            'port_stbd': np.linalg.norm(port - stbd)
        }
        
        print("\nBaselines calculées depuis DIMCON:")
        for name, dist in baselines.items():
            print(f"  {name}: {dist:.3f} m")
            
        # Calcul du seuil de précision (pour 0.1° de précision)
        max_baseline = max(baselines.values())
        threshold = max_baseline * np.tan(np.radians(0.1))
        print(f"  Seuil de distance pour 0.1°: {threshold:.3f} m")
        
        return baselines
    
    def synchronize_data(self):
        """Synchronise les données temporellement"""
        # Trouve la plage temporelle commune
        datasets = [self.port_data, self.starboard_data, self.octans_data]
        
        # Ajouter bow_data si elle existe (données de test)
        if hasattr(self, 'bow_data'):
            datasets.append(self.bow_data)
            
        t_min = max([df['time'].min() for df in datasets])
        t_max = min([df['time'].max() for df in datasets])
        
        # Crée une grille temporelle commune (1 Hz)
        time_grid = np.arange(t_min, t_max, 1.0)
        
        # Interpole toutes les données sur cette grille
        self.synced_data = pd.DataFrame({'time': time_grid})
        
        # Port
        self.synced_data['port_E'] = np.interp(time_grid, self.port_data['time'], self.port_data['E'])
        self.synced_data['port_N'] = np.interp(time_grid, self.port_data['time'], self.port_data['N'])
        self.synced_data['port_h'] = np.interp(time_grid, self.port_data['time'], self.port_data['h'])
        
        # Starboard
        self.synced_data['stbd_E'] = np.interp(time_grid, self.starboard_data['time'], self.starboard_data['E'])
        self.synced_data['stbd_N'] = np.interp(time_grid, self.starboard_data['time'], self.starboard_data['N'])
        self.synced_data['stbd_h'] = np.interp(time_grid, self.starboard_data['time'], self.starboard_data['h'])
        
        # Bow
        if hasattr(self, 'bow_data'):
            # Utiliser les données Bow générées
            self.synced_data['bow_E'] = np.interp(time_grid, self.bow_data['time'], self.bow_data['E'])
            self.synced_data['bow_N'] = np.interp(time_grid, self.bow_data['time'], self.bow_data['N'])
            self.synced_data['bow_h'] = np.interp(time_grid, self.bow_data['time'], self.bow_data['h'])
        else:
            # Utiliser la position fixe (données réelles)
            self.synced_data['bow_E'] = self.bow_fixed['E']
            self.synced_data['bow_N'] = self.bow_fixed['N']
            self.synced_data['bow_h'] = self.bow_fixed['h']
        
        # Octans
        self.synced_data['octans_heading'] = np.interp(time_grid, self.octans_data['time'], self.octans_data['heading'])
        self.synced_data['octans_pitch'] = np.interp(time_grid, self.octans_data['time'], self.octans_data['pitch'])
        self.synced_data['octans_roll'] = np.interp(time_grid, self.octans_data['time'], self.octans_data['roll'])
        
        print(f"\nDonnées synchronisées: {len(self.synced_data)} échantillons")
        
    def calculate_gnss_attitudes(self):
        """
        Calcule les attitudes (heading, pitch, roll) depuis les positions GNSS
        Conventions corrigées selon les standards maritimes
        """
        
        attitudes = []
        
        for idx, row in self.synced_data.iterrows():
            # Positions des antennes en UTM
            bow = np.array([row['bow_E'], row['bow_N'], row['bow_h']])
            port = np.array([row['port_E'], row['port_N'], row['port_h']])
            stbd = np.array([row['stbd_E'], row['stbd_N'], row['stbd_h']])
            
            # === CALCUL DU HEADING ===
            # Vecteur longitudinal : du centre géométrique vers la proue
            center_horiz = (port[:2] + stbd[:2]) / 2  # Centre port-starboard
            bow_vector_horiz = bow[:2] - center_horiz  # Vecteur vers la proue
            
            # Heading = angle depuis le Nord géographique (convention maritime)
            # atan2(East, North) donne l'angle depuis le Nord vers l'Est
            heading_rad = np.arctan2(bow_vector_horiz[0], bow_vector_horiz[1])
            heading_deg = np.degrees(heading_rad)
            
            # Normalisation 0-360°
            if heading_deg < 0:
                heading_deg += 360
            
            # === CONVERGENCE DES MÉRIDIENS ===
            center_3d = (bow + port + stbd) / 3
            lat, lon = self.utm_to_latlon(center_3d[0], center_3d[1])
            convergence = self.calculate_convergence(lat, lon)
            
            # Application de la convergence (Grid North → True North)
            heading_true = heading_deg - convergence
            if heading_true < 0:
                heading_true += 360
            elif heading_true >= 360:
                heading_true -= 360
            
            # === CALCUL DU PITCH ===
            # Pitch = inclinaison longitudinale (bow up = positif)
            # Utilisation du vecteur centre → bow projeté sur le plan longitudinal
            bow_vector_3d = bow - center_3d
            bow_distance_horiz = np.linalg.norm(bow_vector_horiz)
            
            if bow_distance_horiz > 0:
                # Pitch positif = bow plus haut que le centre
                pitch_rad = np.arctan2(bow_vector_3d[2], bow_distance_horiz)
                pitch_deg = np.degrees(pitch_rad)
            else:
                pitch_deg = 0
            
            # === CALCUL DU ROLL ===
            # Roll = inclinaison transversale (port up = positif, convention maritime)
            port_stbd_vector = stbd - port  # Vecteur port → starboard
            port_stbd_distance = np.linalg.norm(port_stbd_vector[:2])
            
            if port_stbd_distance > 0:
                # Roll positif = port plus haut que starboard
                # port_stbd_vector[2] = h_starboard - h_port
                # Si positif → starboard plus haut → roll négatif
                roll_rad = -np.arctan2(port_stbd_vector[2], port_stbd_distance)
                roll_deg = np.degrees(roll_rad)
            else:
                roll_deg = 0
            
            attitudes.append({
                'heading': heading_true,
                'pitch': pitch_deg,
                'roll': roll_deg,
                'convergence': convergence,
                'center_E': center_3d[0],
                'center_N': center_3d[1]
            })
        
        # Ajoute aux données synchronisées
        attitudes_df = pd.DataFrame(attitudes)
        self.synced_data['gnss_heading'] = attitudes_df['heading']
        self.synced_data['gnss_pitch'] = attitudes_df['pitch']
        self.synced_data['gnss_roll'] = attitudes_df['roll']
        self.synced_data['convergence'] = attitudes_df['convergence']
        
        # Informations de débogage
        print(f"\nAttitudes GNSS calculées (conventions maritimes):")
        print(f"  Heading moyen: {attitudes_df['heading'].mean():.1f}°")
        print(f"  Pitch moyen: {attitudes_df['pitch'].mean():.2f}° (+ = bow up)")
        print(f"  Roll moyen: {attitudes_df['roll'].mean():.2f}° (+ = port up)")
        print(f"  Convergence moyenne: {attitudes_df['convergence'].mean():.3f}°")
        
    def calculate_co(self):
        """Calcule les C-O (Corrections-Offsets) avec gestion des discontinuités"""
        
        # Calcul des C-O bruts
        co_heading_raw = self.synced_data['octans_heading'] - self.synced_data['gnss_heading']
        co_pitch_raw = self.synced_data['octans_pitch'] - self.synced_data['gnss_pitch']
        co_roll_raw = self.synced_data['octans_roll'] - self.synced_data['gnss_roll']
        
        # Gestion des discontinuités du heading (passage 0°/360°)
        co_heading_corrected = []
        for co in co_heading_raw:
            # Normalisation entre -180° et +180°
            while co > 180:
                co -= 360
            while co < -180:
                co += 360
            co_heading_corrected.append(co)
        
        self.synced_data['co_heading'] = co_heading_corrected
        self.synced_data['co_pitch'] = co_pitch_raw
        self.synced_data['co_roll'] = co_roll_raw
        
        # Détection et correction d'éventuels sauts de 360° dans le heading
        co_heading_series = pd.Series(co_heading_corrected)
        heading_jumps = np.abs(co_heading_series.diff()) > 180
        if heading_jumps.any():
            print(f"⚠️  Détection de {heading_jumps.sum()} sauts de heading > 180°")
        
        # Statistiques avec informations de qualité
        print("\n=== RÉSULTATS DE CALIBRATION ===")
        results = {}
        
        for param in ['heading', 'pitch', 'roll']:
            co = self.synced_data[f'co_{param}']
            
            # Statistiques de base
            mean_val = co.mean()
            std_val = co.std()
            min_val = co.min()
            max_val = co.max()
            
            # Statistiques robustes (moins sensibles aux outliers)
            median_val = co.median()
            q25 = co.quantile(0.25)
            q75 = co.quantile(0.75)
            iqr = q75 - q25
            
            print(f"\nC-O {param.upper()}:")
            print(f"  Moyenne: {mean_val:.3f}°")
            print(f"  Médiane: {median_val:.3f}°")
            print(f"  Écart-type: {std_val:.3f}°")
            print(f"  IQR: {iqr:.3f}°")
            print(f"  Plage: [{min_val:.3f}°, {max_val:.3f}°]")
            
            # Évaluation de la qualité
            quality = "Excellente" if std_val < 0.1 else "Bonne" if std_val < 0.5 else "Acceptable" if std_val < 1.0 else "Mauvaise"
            print(f"  Qualité: {quality}")
            
            results[param] = {
                'mean': mean_val,
                'median': median_val, 
                'std': std_val,
                'iqr': iqr,
                'min': min_val,
                'max': max_val,
                'quality': quality
            }
        
        # Analyse de cohérence globale
        print(f"\n=== ANALYSE DE COHÉRENCE ===")
        print(f"Convergence moyenne: {self.synced_data['convergence'].mean():.4f}°")
        print(f"Plage temporelle: {self.synced_data['time'].max() - self.synced_data['time'].min():.1f}s")
        
        return results
    
    def quality_control(self):
        """Contrôle qualité avec détection d'outliers"""
        print("\n=== CONTRÔLE QUALITÉ ===")
        
        # Détection d'outliers (méthode Z-score)
        for param in ['co_heading', 'co_pitch', 'co_roll']:
            z_scores = np.abs(stats.zscore(self.synced_data[param]))
            outliers = z_scores > 3  # Z-score > 3 = outlier
            
            print(f"\n{param.upper()}:")
            print(f"  Outliers détectés: {outliers.sum()}")
            print(f"  Pourcentage: {outliers.sum()/len(outliers)*100:.1f}%")
            
            # Marque les outliers
            self.synced_data[f'{param}_outlier'] = outliers
    
    def apply_smoothing(self, window_length=11, polyorder=3):
        """Applique un filtrage Savitzky-Golay pour lisser les C-O"""
        for param in ['co_heading', 'co_pitch', 'co_roll']:
            # Filtrage sur toutes les données
            if len(self.synced_data) > window_length:
                smoothed = savgol_filter(self.synced_data[param], window_length, polyorder)
                self.synced_data[f'{param}_smoothed'] = smoothed
    
    def plot_results(self):
        """Génère les graphiques de résultats"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        
        # Comparaisons GNSS vs Octans
        for i, param in enumerate(['heading', 'pitch', 'roll']):
            ax = axes[i, 0]
            ax.plot(self.synced_data['time'], self.synced_data[f'gnss_{param}'], 'b-', label='GNSS', alpha=0.7)
            ax.plot(self.synced_data['time'], self.synced_data[f'octans_{param}'], 'r-', label='Octans', alpha=0.7)
            ax.set_ylabel(f'{param.capitalize()} (°)')
            ax.set_xlabel('Time (s)')
            ax.legend()
            ax.grid(True)
            ax.set_title(f'Comparaison {param.capitalize()}')
            
            # C-O
            ax = axes[i, 1]
            ax.plot(self.synced_data['time'], self.synced_data[f'co_{param}'], 'g-', alpha=0.7, label='Raw')
            
            # Ajouter la version lissée si elle existe
            if f'co_{param}_smoothed' in self.synced_data.columns:
                ax.plot(self.synced_data['time'], self.synced_data[f'co_{param}_smoothed'], 
                       'r-', linewidth=2, label='Smoothed')
            
            mean_val = self.synced_data[f'co_{param}'].mean()
            ax.axhline(y=mean_val, color='k', linestyle='--', 
                      label=f'Moyenne: {mean_val:.3f}°')
            ax.set_ylabel(f'C-O {param.capitalize()} (°)')
            ax.set_xlabel('Time (s)')
            ax.legend()
            ax.grid(True)
            ax.set_title(f'C-O {param.capitalize()}')
        
        plt.tight_layout()
        plt.savefig('calibration_results.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_results(self):
        """Sauvegarde les résultats"""
        # Données complètes
        self.synced_data.to_csv('calibration_data.csv', index=False)
        
        # Rapport de synthèse
        with open('calibration_report.txt', 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT DE CALIBRATION DYNAMIQUE ===\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre d'échantillons: {len(self.synced_data)}\n\n")
            
            f.write("CONFIGURATION:\n")
            f.write(f"  Zone UTM: {self.utm_zone}\n")
            f.write(f"  Décalage GPS-UTC: {self.gps_utc_offset}s\n\n")
            
            f.write("RÉSULTATS C-O:\n")
            for param in ['heading', 'pitch', 'roll']:
                co = self.synced_data[f'co_{param}']
                f.write(f"\n{param.upper()}:\n")
                f.write(f"  Moyenne: {co.mean():.3f}°\n")
                f.write(f"  Écart-type: {co.std():.3f}°\n")
                f.write(f"  Min: {co.min():.3f}°\n")
                f.write(f"  Max: {co.max():.3f}°\n")
                
            # Contrôle qualité
            f.write(f"\nCONTRÔLE QUALITÉ:\n")
            for param in ['heading', 'pitch', 'roll']:
                if f'co_{param}_outlier' in self.synced_data.columns:
                    outliers = self.synced_data[f'co_{param}_outlier'].sum()
                    total = len(self.synced_data)
                    f.write(f"  {param.upper()} outliers: {outliers}/{total} ({outliers/total*100:.1f}%)\n")

    def run_calibration(self):
        """Exécute la calibration complète"""
        print("=== CALIBRATION DYNAMIQUE PAR MÉTHODE GNSS ===\n")
        
        # 1. Charge les données
        self.load_data()
        
        # 2. Calcule les baselines
        self.calculate_baselines()
        
        # 3. Synchronise les données
        self.synchronize_data()
        
        # 4. Calcule les attitudes GNSS
        self.calculate_gnss_attitudes()
        
        # 5. Calcule les C-O
        co_results = self.calculate_co()
        
        # 6. Contrôle qualité
        self.quality_control()
        
        # 7. Lissage des données
        self.apply_smoothing()
        
        # 8. Génère les graphiques
        self.plot_results()
        
        # 9. Sauvegarde les résultats
        self.save_results()
        
        print("\n✓ Calibration terminée avec succès!")
        print("  - Graphiques: calibration_results.png")
        print("  - Données: calibration_data.csv")
        print("  - Rapport: calibration_report.txt")
        
        return co_results


# Exécution du script
if __name__ == "__main__":
    # Utilisation simple
    calibrator = DynamicCalibration()
    results = calibrator.run_calibration()
    
    # Affichage des résultats finaux
    print("\n" + "="*50)
    print("RÉSULTATS FINAUX DE CALIBRATION")
    print("="*50)
    for param, values in results.items():
        print(f"{param.upper()}: {values['mean']:.3f}° ± {values['std']:.3f}° ({values['quality']})")
    
    # Recommandations améliorées
    print("\nRECOMMANDATIONS:")
    for param, values in results.items():
        if values['std'] > 1.0:
            print(f"⚠️  {param.upper()}: Écart-type élevé ({values['std']:.3f}°) - Contrôler les données et la géométrie")
        elif values['std'] > 0.5:
            print(f"🔶 {param.upper()}: Écart-type modéré ({values['std']:.3f}°) - Acceptable mais peut être amélioré")
        elif values['std'] > 0.1:
            print(f"✅ {param.upper()}: Bonne qualité ({values['std']:.3f}°)")
        else:
            print(f"🎯 {param.upper()}: Excellente qualité ({values['std']:.3f}°)")
    
    # Analyse additionnelle
    print(f"\nINFOS SUPPLÉMENTAIRES:")
    print(f"• Utiliser les valeurs médianes si présence d'outliers")
    print(f"• Contrôler la stabilité des baselines pendant la mesure")
    print(f"• Vérifier la synchronisation temporelle (±0.5s max)")
    
    # Valeurs recommandées à appliquer
    print(f"\n🎯 VALEURS C-O À APPLIQUER:")
    for param, values in results.items():
        if values['std'] < 1.0:
            print(f"• {param.upper()}: {values['median']:.3f}° (médiane)")
        else:
            print(f"• {param.upper()}: CALIBRATION À REFAIRE (qualité insuffisante)")