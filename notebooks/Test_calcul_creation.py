import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from scipy.spatial.transform import Rotation as R

class BoatCalibrationSimulator:
    """
    Simulation complète du processus de calibration avec convention GNSS :
    - Z vers le haut (ENU - East North Up)
    - Roll + = Port Up (gîte bâbord)
    - Pitch + = Bow Up (proue vers le haut)
    """
    
    def __init__(self):
        # Points de référence du bateau (coordonnées dans le repère bateau ENU)
        # Z positif vers le haut (convention GNSS)
        self.reference_points = {
            "Bow": np.array([-0.269318, -64.232461, 10.88835]),
            "Port": np.array([-9.34689, -27.956415, 13.491246]),
            "Stb": np.array([9.39156, -27.827088, 13.505628])
        }
        
        # Paramètres de la simulation
        self.dt = 0.1  # Pas de temps en secondes
        self.delay_time = 1.0  # Décalage en secondes
        self.delay_steps = int(self.delay_time / self.dt)
        self.window_size = 100
        
        # Niveau de bruit sur les coordonnées (en mètres)
        self.coordinate_noise = 0.01  # 1cm de bruit GPS
        
        # Paramètres du mouvement
        self.base_heading = 150.0
        self.heading_amplitude = 3.0
        self.pitch_amplitude = 0.5  # + = Bow Up
        self.roll_amplitude = 0.5   # + = Port Up
        
        # Données pour l'affichage
        self.time_data = deque(maxlen=self.window_size)
        self.heading_theoretical = deque(maxlen=self.window_size)
        self.heading_calculated = deque(maxlen=self.window_size)
        self.pitch_theoretical = deque(maxlen=self.window_size)
        self.pitch_calculated = deque(maxlen=self.window_size)
        self.roll_theoretical = deque(maxlen=self.window_size)
        self.roll_calculated = deque(maxlen=self.window_size)
        
        # Buffers pour le décalage (stockent les coordonnées, pas les angles)
        self.coordinates_buffer = deque(maxlen=self.delay_steps)
        
        # Temps de simulation
        self.current_time = 0.0
        
        # Configuration du graphique
        self.setup_plot()
    
    def setup_plot(self):
        """Configure les graphiques"""
        self.fig, self.axes = plt.subplots(3, 1, figsize=(12, 10))
        self.fig.suptitle('Simulation GNSS - Convention ENU (Z↑, Roll+=Port Up, Pitch+=Bow Up)', fontsize=14)
        
        axis_configs = [
            {'title': 'Cap (Heading) - Rotation Z', 'ylabel': 'Degrés (°)', 'color': 'blue'},
            {'title': 'Tangage (Pitch) - Bow Up (+)', 'ylabel': 'Degrés (°)', 'color': 'red'},
            {'title': 'Roulis (Roll) - Port Up (+)', 'ylabel': 'Degrés (°)', 'color': 'green'}
        ]
        
        self.lines_theoretical = []
        self.lines_calculated = []
        
        for i, config in enumerate(axis_configs):
            ax = self.axes[i]
            ax.set_title(config['title'])
            ax.set_ylabel(config['ylabel'])
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, self.window_size * self.dt)
            
            line_theo, = ax.plot([], [], '-', color=config['color'], 
                               linewidth=2, label='Théorique', alpha=0.8)
            line_calc, = ax.plot([], [], '--', color='orange', 
                               linewidth=2, label='Calculé (coordonnées GNSS)', alpha=0.8)
            
            self.lines_theoretical.append(line_theo)
            self.lines_calculated.append(line_calc)
            
            ax.legend(loc='upper right')
            
            if i == 2:
                ax.set_xlabel('Temps (s)')
        
        plt.tight_layout()
    
    def generate_theoretical_angles(self, t):
        """Génère les angles théoriques pour un temps donné"""
        # Cap avec variation lente
        heading = self.base_heading + self.heading_amplitude * np.sin(0.1 * t) + \
                 0.5 * np.sin(0.3 * t)
        
        # Tangage avec oscillation (+ = Bow Up)
        pitch = self.pitch_amplitude * np.sin(0.2 * t + np.pi/4) + \
               0.1 * np.sin(0.8 * t)
        
        # Roulis avec oscillation différente (+ = Port Up)
        roll = self.roll_amplitude * np.sin(0.15 * t + np.pi/2) + \
              0.2 * np.sin(0.6 * t)
        
        return heading, pitch, roll
    
    def angles_to_rotation_matrix(self, heading, pitch, roll):
        """
        Convertit les angles en matrice de rotation (convention GNSS ENU)
        - Z vers le haut
        - Roll + = Port Up  
        - Pitch + = Bow Up
        """
        # Convention ENU pour GNSS avec les bonnes orientations
        # L'ordre reste ZYX mais avec les bonnes orientations de rotation
        r = R.from_euler('ZYX', [heading, pitch, roll], degrees=True)
        return r.as_matrix()
    
    def compute_antenna_coordinates(self, heading, pitch, roll, fixed_point='Bow'):
        """Calcule les coordonnées des antennes pour des angles donnés"""
        # Matrice de rotation
        R_matrix = self.angles_to_rotation_matrix(heading, pitch, roll)
        
        # Position du point fixe (origine)
        fixed_pos = self.reference_points[fixed_point]
        
        # Calculer les positions de tous les points
        coordinates = {}
        for point_name, ref_pos in self.reference_points.items():
            if point_name == fixed_point:
                # Point fixe reste à sa position
                coordinates[point_name] = fixed_pos.copy()
            else:
                # Position relative par rapport au point fixe
                relative_pos = ref_pos - fixed_pos
                # Appliquer la rotation
                rotated_pos = R_matrix @ relative_pos
                # Position absolue
                coordinates[point_name] = fixed_pos + rotated_pos
        
        return coordinates
    
    def add_coordinate_noise(self, coordinates):
        """Ajoute du bruit aux coordonnées (simulation GPS)"""
        noisy_coordinates = {}
        for point_name, coords in coordinates.items():
            noise = np.random.normal(0, self.coordinate_noise, 3)
            noisy_coordinates[point_name] = coords + noise
        return noisy_coordinates
    
    def estimate_angles_from_coordinates(self, coordinates, fixed_point='Bow'):
        """
        Estime les angles à partir des coordonnées (algorithme de calibration)
        Convention GNSS : Z↑, Roll+=Port Up, Pitch+=Bow Up
        """
        try:
            # Préparer les points de référence et mesurés
            ref_points = []
            measured_points = []
            
            for point_name in ['Bow', 'Port', 'Stb']:  # Ordre fixe
                if point_name in coordinates:
                    ref_points.append(self.reference_points[point_name])
                    measured_points.append(coordinates[point_name])
            
            if len(ref_points) < 3:
                return None, None, None
            
            ref_points = np.array(ref_points)
            measured_points = np.array(measured_points)
            
            # Centrer par rapport au point fixe
            fixed_idx = ['Bow', 'Port', 'Stb'].index(fixed_point)
            ref_centered = ref_points - ref_points[fixed_idx]
            measured_centered = measured_points - measured_points[fixed_idx]
            
            # Utiliser SVD pour estimer la rotation (algorithme Kabsch)
            H = ref_centered.T @ measured_centered
            U, _, Vt = np.linalg.svd(H)
            R_estimated = Vt.T @ U.T
            
            # Assurer que c'est une rotation propre
            if np.linalg.det(R_estimated) < 0:
                Vt[-1, :] *= -1
                R_estimated = Vt.T @ U.T
            
            # Convertir en angles d'Euler (même convention que la génération)
            r = R.from_matrix(R_estimated)
            euler_angles = r.as_euler('ZYX', degrees=True)
            
            return euler_angles[0], euler_angles[1], euler_angles[2]  # heading, pitch, roll
            
        except Exception as e:
            print(f"Erreur dans l'estimation: {e}")
            return None, None, None
    
    def update_buffers(self, coordinates):
        """Met à jour les buffers de décalage"""
        self.coordinates_buffer.append(coordinates)
    
    def get_calculated_angles(self):
        """Récupère les angles calculés (avec décalage)"""
        if len(self.coordinates_buffer) >= self.delay_steps:
            # Prendre les coordonnées avec le décalage
            delayed_coordinates = self.coordinates_buffer[0]
            # Recalculer les angles
            return self.estimate_angles_from_coordinates(delayed_coordinates)
        else:
            return None, None, None
    
    def update_plot_data(self):
        """Met à jour les données pour l'affichage"""
        # 1. Générer les angles théoriques
        heading_theo, pitch_theo, roll_theo = self.generate_theoretical_angles(self.current_time)
        
        # 2. Convertir en coordonnées d'antennes
        coordinates_theo = self.compute_antenna_coordinates(heading_theo, pitch_theo, roll_theo)
        
        # 3. Ajouter du bruit aux coordonnées
        coordinates_noisy = self.add_coordinate_noise(coordinates_theo)
        
        # 4. Mettre à jour les buffers pour le décalage
        self.update_buffers(coordinates_noisy)
        
        # 5. Recalculer les angles à partir des coordonnées bruitées (avec décalage)
        heading_calc, pitch_calc, roll_calc = self.get_calculated_angles()
        
        # 6. Ajouter aux données d'affichage
        self.time_data.append(self.current_time)
        self.heading_theoretical.append(heading_theo)
        self.pitch_theoretical.append(pitch_theo)
        self.roll_theoretical.append(roll_theo)
        
        if heading_calc is not None:
            self.heading_calculated.append(heading_calc)
            self.pitch_calculated.append(pitch_calc)
            self.roll_calculated.append(roll_calc)
        else:
            # Phase d'initialisation
            if len(self.heading_calculated) > 0:
                self.heading_calculated.append(self.heading_calculated[-1])
                self.pitch_calculated.append(self.pitch_calculated[-1])
                self.roll_calculated.append(self.roll_calculated[-1])
            else:
                self.heading_calculated.append(heading_theo)
                self.pitch_calculated.append(pitch_theo)
                self.roll_calculated.append(roll_theo)
    
    def animate(self, frame):
        """Fonction d'animation"""
        self.current_time += self.dt
        self.update_plot_data()
        
        if len(self.time_data) > 1:
            time_array = np.array(self.time_data)
            
            time_window = self.window_size * self.dt
            x_min = max(0, self.current_time - time_window)
            x_max = self.current_time + 2
            
            theo_data = [
                np.array(self.heading_theoretical),
                np.array(self.pitch_theoretical), 
                np.array(self.roll_theoretical)
            ]
            
            calc_data = [
                np.array(self.heading_calculated),
                np.array(self.pitch_calculated),
                np.array(self.roll_calculated)
            ]
            
            for i in range(3):
                ax = self.axes[i]
                
                self.lines_theoretical[i].set_data(time_array, theo_data[i])
                self.lines_calculated[i].set_data(time_array, calc_data[i])
                
                if len(theo_data[i]) > 0 and len(calc_data[i]) > 0:
                    all_values = np.concatenate([theo_data[i], calc_data[i]])
                    y_margin = 0.1 * (np.max(all_values) - np.min(all_values))
                    if y_margin > 0:
                        ax.set_ylim(np.min(all_values) - y_margin, 
                                   np.max(all_values) + y_margin)
                
                ax.set_xlim(x_min, x_max)
        
        return self.lines_theoretical + self.lines_calculated
    
    def run_animation(self):
        """Lance l'animation"""
        print("Démarrage de la simulation GNSS (convention ENU)...")
        print("- Courbes pleines : Angles théoriques")
        print("- Courbes pointillées : Angles recalculés depuis coordonnées GNSS")
        print(f"- Bruit sur coordonnées : {self.coordinate_noise*1000:.1f}mm")
        print(f"- Décalage temporel : {self.delay_time}s")
        print("- Convention : Z↑, Roll+=Port Up, Pitch+=Bow Up")
        
        self.ani = animation.FuncAnimation(
            self.fig, self.animate, interval=int(self.dt * 1000), 
            blit=False, cache_frame_data=False
        )
        
        plt.show()

class StaticBoatDemo:
    """Version statique pour tests rapides - Convention GNSS"""
    
    def __init__(self, delay_time=1.0, coordinate_noise=0.01):
        self.delay_time = delay_time
        self.coordinate_noise = coordinate_noise
        self.time_max = 30
        self.dt = 0.1
        
        # Points de référence (convention ENU - Z vers le haut)
        self.reference_points = {
            "Bow": np.array([-0.269318, -64.232461, 10.88835]),
            "Port": np.array([-9.34689, -27.956415, 13.491246]),
            "Stb": np.array([9.39156, -27.827088, 13.505628])
        }
    
    def test_rotation_cycle(self):
        """Test pour valider le cycle angles → coordonnées → angles (convention GNSS)"""
        print("\n=== TEST CYCLE ROTATION (Convention GNSS ENU) ===")
        print("Z↑, Roll+=Port Up, Pitch+=Bow Up")
        
        simulator = BoatCalibrationSimulator()
        
        # Angles de test avec les bonnes conventions
        test_cases = [
            (0, 0, 0),         # Cas neutre
            (150, 0, 0),       # Cap seul
            (0, 0.5, 0),       # Tangage seul (+ = Bow Up)
            (0, 0, 0.5),       # Roulis seul (+ = Port Up)
            (150, 0.5, 0.3),   # Cas mixte (Bow Up + Port Up)
            (150, -0.5, -0.3), # Cas mixte inverse (Bow Down + Stb Up)
        ]
        
        print("\nTest sans bruit:")
        print("Entrée (h,p,r) → Sortie (h,p,r) → Erreur")
        print("(h=heading, p=pitch+BowUp, r=roll+PortUp)")
        
        for h_in, p_in, r_in in test_cases:
            # 1. Angles → Coordonnées
            coords = simulator.compute_antenna_coordinates(h_in, p_in, r_in)
            
            # 2. Coordonnées → Angles (sans bruit)
            h_out, p_out, r_out = simulator.estimate_angles_from_coordinates(coords)
            
            if h_out is not None:
                # Calculer erreurs
                h_err = self.angle_difference(h_out, h_in)
                p_err = p_out - p_in
                r_err = r_out - r_in
                
                print(f"({h_in:6.1f},{p_in:5.1f},{r_in:5.1f}) → ({h_out:6.1f},{p_out:5.1f},{r_out:5.1f}) → ({h_err:6.3f},{p_err:6.3f},{r_err:6.3f})")
            else:
                print(f"({h_in:6.1f},{p_in:5.1f},{r_in:5.1f}) → ERREUR DE CALCUL")
        
        print("\nTest avec bruit 1mm:")
        for h_in, p_in, r_in in test_cases[:3]:  # Quelques cas seulement
            coords = simulator.compute_antenna_coordinates(h_in, p_in, r_in)
            # Ajouter très peu de bruit pour voir l'effet
            coords_noisy = {}
            for name, pos in coords.items():
                noise = np.random.normal(0, 0.001, 3)  # 1mm
                coords_noisy[name] = pos + noise
            
            h_out, p_out, r_out = simulator.estimate_angles_from_coordinates(coords_noisy)
            
            if h_out is not None:
                h_err = self.angle_difference(h_out, h_in)
                p_err = p_out - p_in
                r_err = r_out - r_in
                print(f"({h_in:6.1f},{p_in:5.1f},{r_in:5.1f}) → ({h_out:6.1f},{p_out:5.1f},{r_out:5.1f}) → ({h_err:6.3f},{p_err:6.3f},{r_err:6.3f})")
    
    def generate_demo_data(self):
        """Génère des données de démonstration avec simulation complète"""
        t = np.arange(0, self.time_max, self.dt)
        
        # Angles théoriques (convention GNSS)
        heading_theo = 150 + 3 * np.sin(0.1 * t) + 0.5 * np.sin(0.3 * t)
        pitch_theo = 0.5 * np.sin(0.2 * t + np.pi/4) + 0.1 * np.sin(0.8 * t)  # + = Bow Up
        roll_theo = 0.5 * np.sin(0.15 * t + np.pi/2) + 0.2 * np.sin(0.6 * t)  # + = Port Up
        
        # Simuler le processus complet pour chaque instant
        heading_calc = []
        pitch_calc = []
        roll_calc = []
        
        delay_steps = int(self.delay_time / self.dt)
        coordinates_buffer = []
        
        simulator = BoatCalibrationSimulator()
        
        for i, time_val in enumerate(t):
            # 1. Angles → Coordonnées
            coords = simulator.compute_antenna_coordinates(
                heading_theo[i], pitch_theo[i], roll_theo[i]
            )
            
            # 2. Ajouter du bruit
            coords_noisy = simulator.add_coordinate_noise(coords)
            
            # 3. Buffer pour délai
            coordinates_buffer.append(coords_noisy)
            
            # 4. Recalculer les angles (avec délai)
            if i >= delay_steps:
                delayed_coords = coordinates_buffer[i - delay_steps]
                h_calc, p_calc, r_calc = simulator.estimate_angles_from_coordinates(delayed_coords)
                
                if h_calc is not None:
                    heading_calc.append(h_calc)
                    pitch_calc.append(p_calc)
                    roll_calc.append(r_calc)
                else:
                    heading_calc.append(heading_theo[i])
                    pitch_calc.append(pitch_theo[i])
                    roll_calc.append(roll_theo[i])
            else:
                heading_calc.append(heading_theo[i])
                pitch_calc.append(pitch_theo[i])
                roll_calc.append(roll_theo[i])
        
        return {
            'time': t,
            'heading_theo': heading_theo,
            'pitch_theo': pitch_theo,
            'roll_theo': roll_theo,
            'heading_calc': np.array(heading_calc),
            'pitch_calc': np.array(pitch_calc),
            'roll_calc': np.array(roll_calc)
        }
    
    def plot_static_comparison(self):
        """Affiche une comparaison statique"""
        data = self.generate_demo_data()
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle(f'Convention GNSS ENU - Bruit:{self.coordinate_noise*1000:.1f}mm, Délai:{self.delay_time}s', fontsize=14)
        
        comparisons = [
            ('Cap (Heading) - Rotation Z', data['heading_theo'], data['heading_calc'], 'blue'),
            ('Tangage (Pitch) - Bow Up (+)', data['pitch_theo'], data['pitch_calc'], 'red'),
            ('Roulis (Roll) - Port Up (+)', data['roll_theo'], data['roll_calc'], 'green')
        ]
        
        for i, (title, theo, calc, color) in enumerate(comparisons):
            ax = axes[i]
            ax.plot(data['time'], theo, '-', color=color, linewidth=2, 
                   label='Théorique', alpha=0.8)
            ax.plot(data['time'], calc, '--', color='orange', linewidth=2, 
                   label='Calculé (GNSS)', alpha=0.8)
            
            ax.set_title(title)
            ax.set_ylabel('Degrés (°)')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            if i == 2:
                ax.set_xlabel('Temps (s)')
        
        plt.tight_layout()
        plt.show()
        
        # Statistiques avec alignement temporel correct
        print(f"\n=== STATISTIQUES GNSS (Bruit:{self.coordinate_noise*1000:.1f}mm, Délai:{self.delay_time}s) ===")
        delay_steps = int(self.delay_time / self.dt)
        
        for name, theo, calc in [('Cap', data['heading_theo'], data['heading_calc']),
                                ('Tangage (Bow Up)', data['pitch_theo'], data['pitch_calc']),
                                ('Roulis (Port Up)', data['roll_theo'], data['roll_calc'])]:
            if len(theo) > delay_steps:
                # Aligner temporellement pour calculer l'erreur due au bruit seul
                aligned_theo = theo[delay_steps:]
                aligned_calc = calc[delay_steps:]
                
                error = aligned_calc - aligned_theo
                # Gérer les discontinuités angulaires pour le cap
                if name == 'Cap':
                    error = np.array([self.angle_difference(c, t) for c, t in zip(aligned_calc, aligned_theo)])
                
                rms_error = np.sqrt(np.mean(error**2))
                max_error = np.max(np.abs(error))
                mean_error = np.mean(error)
                
                print(f"{name:15}: RMS={rms_error:.3f}°, Max={max_error:.3f}°, Bias={mean_error:.3f}°")
    
    def angle_difference(self, angle1, angle2):
        """Calcule la différence entre deux angles en gérant la périodicité"""
        diff = angle1 - angle2
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return diff

# Utilisation
if __name__ == "__main__":
    print("=== SIMULATION CALIBRATION GNSS (Convention ENU) ===")
    print("Convention : Z↑, Roll+=Port Up, Pitch+=Bow Up")
    print("Processus: Angles théoriques → Coordonnées → Bruit → Recalcul angles")
    print("\nChoisissez le mode:")
    print("1. Animation temps réel")
    print("2. Test statique avec délai = 0s")
    print("3. Test statique avec délai = 1s")
    print("4. Comparaison différents niveaux de bruit")
    print("5. TEST DIAGNOSTIC - Cycle rotation (DEBUG)")
    
    choice = input("Votre choix (1-5): ").strip()
    
    if choice == "1":
        simulator = BoatCalibrationSimulator()
        simulator.coordinate_noise = 0.01  # 1cm
        simulator.delay_time = 1.0
        simulator.delay_steps = int(simulator.delay_time / simulator.dt)
        simulator.run_animation()
    
    elif choice == "2":
        demo = StaticBoatDemo(delay_time=0.0, coordinate_noise=0.01)
        demo.plot_static_comparison()
    
    elif choice == "3":
        demo = StaticBoatDemo(delay_time=1.0, coordinate_noise=0.01)
        demo.plot_static_comparison()
    
    elif choice == "4":
        print("\nComparaison des niveaux de bruit (convention GNSS):")
        for noise_mm in [0.5, 1.0, 2.0, 5.0]:
            noise_m = noise_mm / 1000
            demo = StaticBoatDemo(delay_time=0.0, coordinate_noise=noise_m)
            data = demo.generate_demo_data()
            
            # Calculer RMS pour le cap seulement
            error = np.array([demo.angle_difference(c, t) for c, t in 
                            zip(data['heading_calc'], data['heading_theo'])])
            rms = np.sqrt(np.mean(error**2))
            print(f"Bruit {noise_mm:3.1f}mm → RMS Cap = {rms:.3f}°")
    
    elif choice == "5":
        # Test diagnostic
        demo = StaticBoatDemo()
        demo.test_rotation_cycle()
    
    else:
        print("Mode par défaut: test diagnostic")
        demo = StaticBoatDemo()
        demo.test_rotation_cycle()