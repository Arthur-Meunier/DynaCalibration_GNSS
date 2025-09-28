#!/usr/bin/env python3
"""
Script de test pour la page GNSS Post-Calcul
Teste la lecture des statistiques RTKLIB et l'affichage des résultats
"""

import sys
from pathlib import Path

# Configuration du path
try:
    current_dir = Path(__file__).parent.resolve()
    src_dir = next(p for p in current_dir.parents if p.name == 'src')
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    print(f"✅ Répertoire src trouvé: {src_dir}")
except (StopIteration, FileNotFoundError):
    print("❌ Erreur critique: Impossible de trouver le dossier 'src'.")
    sys.exit(1)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# Import des modules
try:
    from core.app_data import ApplicationData
    from core.project_manager import ProjectManager
    from app.gui.page_GNSSpostcalc import GNSSPostCalcWidget, GNSSStatsReader
    print("✅ Modules importés avec succès")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    sys.exit(1)


class TestMainWindow(QMainWindow):
    """Fenêtre de test pour la page GNSS Post-Calcul"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Test Page GNSS Post-Calcul")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialisation des composants
        self.app_data = ApplicationData()
        self.project_manager = ProjectManager()
        
        # Configuration d'un projet de test
        self.setup_test_project()
        
        # Création de la page post-calcul
        self.postcalc_widget = GNSSPostCalcWidget(
            app_data=self.app_data,
            project_manager=self.project_manager,
            parent=self
        )
        
        # Connexion des signaux
        self.postcalc_widget.reset_requested.connect(self.on_reset_requested)
        self.postcalc_widget.recalculate_requested.connect(self.on_recalculate_requested)
        
        # Interface
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.postcalc_widget)
        self.setCentralWidget(central_widget)
        
        print("✅ Interface de test créée")
    
    def setup_test_project(self):
        """Configure un projet de test avec des données simulées"""
        try:
            # Créer un projet de test
            test_project_path = Path("test_gnss_project")
            test_project_path.mkdir(exist_ok=True)
            
            # Créer la structure de dossiers
            processed_dir = test_project_path / "data" / "processed" / "gnss"
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Créer des fichiers de test simulés
            self.create_test_pos_file(processed_dir / "port_bow.pos")
            self.create_test_pos_file(processed_dir / "port_stbd.pos")
            self.create_test_stat_file(processed_dir / "port_bow.stat")
            self.create_test_stat_file(processed_dir / "port_stbd.stat")
            
            # Configurer le project manager
            self.project_manager.current_project = str(test_project_path)
            
            print(f"✅ Projet de test configuré: {test_project_path}")
            
        except Exception as e:
            print(f"❌ Erreur configuration projet test: {e}")
    
    def create_test_pos_file(self, file_path: Path):
        """Crée un fichier .pos de test simulé"""
        try:
            with open(file_path, 'w') as f:
                f.write("%  GPST                  latitude(deg) longitude(deg)  height(m)   Q  ns   sdn(m)   sde(m)   sdu(m)  sdne(m)  sdeu(m)  sdun(m) age(s)  ratio\n")
                
                # Simuler des données avec différentes qualités
                import random
                from datetime import datetime, timedelta
                
                base_time = datetime(2025, 8, 2, 0, 0, 0)
                
                for i in range(1000):  # 1000 époques
                    current_time = base_time + timedelta(seconds=i*30)  # Toutes les 30 secondes
                    time_str = current_time.strftime("%Y/%m/%d %H:%M:%S")
                    
                    # Coordonnées simulées
                    lat = 48.8566 + random.uniform(-0.001, 0.001)
                    lon = 2.3522 + random.uniform(-0.001, 0.001)
                    height = 100.0 + random.uniform(-5, 5)
                    
                    # Qualité simulée (plus de fix que de float)
                    quality = random.choices(['1', '2', '3', '4', '5'], weights=[60, 25, 10, 3, 2])[0]
                    
                    # Précision simulée
                    sdn = random.uniform(0.01, 0.05)
                    sde = random.uniform(0.01, 0.05)
                    sdu = random.uniform(0.02, 0.08)
                    
                    f.write(f"{time_str} {lat:.6f} {lon:.6f} {height:.3f} {quality} 8 {sdn:.3f} {sde:.3f} {sdu:.3f} 0.000 0.000 0.000 0.0 100.0\n")
            
            print(f"✅ Fichier POS de test créé: {file_path}")
            
        except Exception as e:
            print(f"❌ Erreur création fichier POS: {e}")
    
    def create_test_stat_file(self, file_path: Path):
        """Crée un fichier .stat de test simulé"""
        try:
            with open(file_path, 'w') as f:
                f.write("# RTKLIB Statistics File\n")
                f.write("# Generated by test script\n\n")
                f.write("RMS position: 0.025 m\n")
                f.write("RMS velocity: 0.012 m/s\n")
                f.write("Processing time: 45.2 s\n")
                f.write("Solution rate: 85.3%\n")
                f.write("Fix rate: 60.1%\n")
                f.write("Float rate: 25.2%\n")
            
            print(f"✅ Fichier STAT de test créé: {file_path}")
            
        except Exception as e:
            print(f"❌ Erreur création fichier STAT: {e}")
    
    def on_reset_requested(self):
        """Gestionnaire pour la réinitialisation"""
        print("🔄 Réinitialisation demandée depuis la page post-calcul")
        # Dans un vrai scénario, cela supprimerait les fichiers et naviguerait vers la page de calcul
    
    def on_recalculate_requested(self):
        """Gestionnaire pour le recalcul"""
        print("⚡ Recalcul demandé depuis la page post-calcul")
        # Dans un vrai scénario, cela naviguerait vers la page de calcul et relancerait les calculs


def test_stats_reader():
    """Test indépendant du lecteur de statistiques"""
    print("\n🧪 === TEST LECTEUR DE STATISTIQUES ===")
    
    try:
        # Créer un projet de test
        test_project = Path("test_stats_project")
        test_project.mkdir(exist_ok=True)
        
        # Créer la structure
        processed_dir = test_project / "data" / "processed" / "gnss"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer des fichiers de test
        pos_file = processed_dir / "port_bow.pos"
        with open(pos_file, 'w') as f:
            f.write("% Test file\n")
            f.write("2025/08/02 00:00:00 48.856600 2.352200 100.000 1 8 0.025 0.030 0.050 0.000 0.000 0.000 0.0 100.0\n")
            f.write("2025/08/02 00:00:30 48.856601 2.352201 100.001 2 8 0.035 0.040 0.060 0.000 0.000 0.000 0.0 100.0\n")
            f.write("2025/08/02 00:01:00 48.856602 2.352202 100.002 1 8 0.020 0.025 0.045 0.000 0.000 0.000 0.0 100.0\n")
        
        stat_file = processed_dir / "port_bow.stat"
        with open(stat_file, 'w') as f:
            f.write("RMS position: 0.025 m\n")
            f.write("Processing time: 45.2 s\n")
        
        # Tester le lecteur
        reader = GNSSStatsReader(test_project)
        stats = reader.read_baseline_stats("Port→Bow")
        
        print(f"📊 Statistiques lues:")
        print(f"  - Baseline: {stats['baseline_name']}")
        print(f"  - Époques totales: {stats['total_epochs']}")
        print(f"  - Qualités: {stats['quality_counts']}")
        print(f"  - Taux de solution: {stats['solution_rate']:.1f}%")
        print(f"  - RMS position: {stats['position_accuracy'].get('rms', 'N/A')}")
        print(f"  - Temps de traitement: {stats['processing_time']}s")
        
        print("✅ Test lecteur de statistiques réussi")
        
    except Exception as e:
        print(f"❌ Erreur test lecteur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale de test"""
    print("🚀 Démarrage du test de la page GNSS Post-Calcul")
    
    # Test du lecteur de statistiques
    test_stats_reader()
    
    # Test de l'interface
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne
    
    # Configuration du thème sombre
    app.setStyleSheet("""
        QApplication {
            background-color: #2E3440;
            color: #ECEFF4;
        }
    """)
    
    window = TestMainWindow()
    window.show()
    
    print("✅ Interface de test affichée")
    print("📋 Instructions:")
    print("  1. Vérifiez que les statistiques s'affichent correctement")
    print("  2. Testez les différents onglets")
    print("  3. Testez les boutons de réinitialisation et recalcul")
    print("  4. Fermez la fenêtre pour terminer le test")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

