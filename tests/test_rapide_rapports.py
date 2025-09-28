# test_rapide_rapports.py
"""
Test rapide du système de rapports - Version autonome
"""

import sys
from pathlib import Path
import tempfile

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_import_modules():
    """Test d'import des modules"""
    print("📦 Test imports...")
    
    try:
        from core.reports.report_generator import ReportGenerator, ReportConfig, ReportData
        print("✅ report_generator")
    except ImportError as e:
        print(f"❌ report_generator: {e}")
        return False
    
    try:
        from core.logs.log_manager import ProjectLogManager, get_log_manager
        print("✅ log_manager")
    except ImportError as e:
        print(f"❌ log_manager: {e}")
        return False
    
    try:
        import reportlab
        print("✅ reportlab")
    except ImportError as e:
        print(f"❌ reportlab: {e}")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib")
    except ImportError as e:
        print(f"❌ matplotlib: {e}")
        return False
    
    return True

def test_report_generation():
    """Test de génération de rapport"""
    print("\n📄 Test génération rapport...")
    
    try:
        from core.reports.report_generator import ReportGenerator, ReportConfig, ReportData
        
        # Données de test
        test_project_data = {
            'metadata': {
                'vessel': 'Navire Test',
                'company': 'Société Test',
                'engineer': 'Ingénieur Test',
                'created': '2025-01-15T10:00:00Z',
                'last_modified': '2025-01-15T15:30:00Z',
                'description': 'Projet de test pour le système de rapports'
            },
            'workflow_status': {
                'dimcon': {'progress': 100, 'completed': True},
                'gnss': {'progress': 75, 'completed': False},
                'observation': {'progress': 50, 'completed': False},
                'qc': {'progress': 0, 'completed': False}
            },
            'qc_metrics': {
                'global_score': 62.5,
                'gnss_score': 85.0,
                'sensors_score': 40.0
            },
            'observation_sensors': [
                {'id': 'MRU_Test', 'type': 'MRU'},
                {'id': 'Compas_Test', 'type': 'Compas'}
            ]
        }
        
        # Préparer les données du rapport
        report_data = ReportData(
            project_metadata=test_project_data['metadata'],
            workflow_status=test_project_data['workflow_status'],
            qc_metrics=test_project_data['qc_metrics'],
            sensor_data=test_project_data['observation_sensors']
        )
        
        # Configuration
        config = ReportConfig(
            template_type="complete",
            include_charts=False,  # Désactiver pour éviter les dépendances matplotlib
            include_logs=False
        )
        
        # Générer le rapport
        generator = ReportGenerator(config)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            success = generator.generate_complete_report(report_data, tmp_file.name)
            
            if success:
                print(f"✅ Rapport généré: {tmp_file.name}")
                
                # Vérifier que le fichier existe et a une taille > 0
                tmp_path = Path(tmp_file.name)
                if tmp_path.exists() and tmp_path.stat().st_size > 0:
                    print(f"✅ Fichier valide: {tmp_path.stat().st_size} bytes")
                    return True
                else:
                    print("❌ Fichier invalide ou vide")
                    return False
            else:
                print("❌ Échec génération rapport")
                return False
    
    except Exception as e:
        print(f"❌ Erreur génération: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_log_system():
    """Test du système de logs"""
    print("\n📝 Test système de logs...")
    
    try:
        from core.logs.log_manager import ProjectLogManager, get_log_manager
        
        # Initialiser avec répertoire temporaire
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_manager = ProjectLogManager(tmp_dir)
            
            # Démarrer une session
            session_id = log_manager.start_project_session("test_project")
            print(f"✅ Session créée: {session_id}")
            
            # Ajouter des logs
            log_manager.log_info("Test message INFO")
            log_manager.log_warning("Test message WARNING")
            log_manager.log_user_action("Test action utilisateur", {"test": True})
            
            # Récupérer les logs
            recent_logs = log_manager.get_recent_logs(count=10)
            print(f"✅ Logs récupérés: {len(recent_logs)} entrées")
            
            # Statistiques
            stats = log_manager.get_log_statistics()
            print(f"✅ Statistiques: {stats.get('total_logs', 0)} logs")
            
            # Terminer la session
            log_manager.end_current_session()
            print("✅ Session terminée")
            
            return True
    
    except Exception as e:
        print(f"❌ Erreur logs: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🧪 TEST RAPIDE - SYSTÈME DE RAPPORTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports modules", test_import_modules()))
    
    # Test 2: Génération rapport
    results.append(("Génération rapport", test_report_generation()))
    
    # Test 3: Système logs
    results.append(("Système logs", test_log_system()))
    
    # Résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{len(results)} tests réussis")
    
    if passed == len(results):
        print("\n🎉 Tous les tests sont passés !")
        print("🚀 Le système de rapports est opérationnel !")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
