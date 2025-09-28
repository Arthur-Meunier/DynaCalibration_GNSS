# integration_rapports_main.py
"""
Code d'intégration du système de rapports avec l'application principale
À ajouter dans main.py
"""

def integrate_reports_system():
    """Intègre le système de rapports dans l'application"""
    
    # 1. Initialiser le système de logs
    from core.logs.log_manager import init_log_manager
    
    # Initialiser avec le répertoire de logs du projet
    log_manager = init_log_manager("logs")
    print("[OK] Système de logs initialisé")
    
    # 2. Intégrer avec la Page Accueil Enhanced
    def enhance_home_page(home_widget, project_manager):
        """Améliore la page d'accueil avec les fonctionnalités de rapports"""
        from app.gui.reports_integration import add_reports_section_to_home, setup_logging_for_project
        
        # Ajouter les fonctionnalités de rapports
        add_reports_section_to_home(home_widget)
        
        # Configurer les logs pour le projet
        setup_logging_for_project(project_manager)
        
        print("[OK] Page d'accueil améliorée avec système de rapports")
    
    return enhance_home_page

# Exemple d'utilisation dans MainWindow.__init__()
def exemple_integration_main_window():
    """
    Exemple d'intégration dans la classe MainWindow
    """
    
    # Dans MainWindow.__init__(), après la création de la page d'accueil :
    
    # Intégrer le système de rapports
    enhance_home_page = integrate_reports_system()
    
    # Améliorer la page d'accueil
    enhance_home_page(self.page_home, self.project_manager)
    
    # Démarrer une session de logs pour l'application
    from core.logs.log_manager import get_log_manager, log_info
    
    log_manager = get_log_manager()
    log_manager.start_project_session("application_session")
    log_info("Application démarrée", module="main", user_action=True)

# Code à ajouter dans MainWindow.closeEvent()
def exemple_fermeture_application():
    """Code à ajouter lors de la fermeture de l'application"""
    
    from core.logs.log_manager import get_log_manager, log_info
    
    log_manager = get_log_manager()
    if log_manager:
        log_info("Fermeture application", module="main", user_action=True)
        log_manager.end_current_session()
