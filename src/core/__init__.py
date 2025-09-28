def __init__(self):
    super().__init__()
    
    # ❌ SUPPRIMER CETTE LIGNE PROBLÉMATIQUE :
    # if ProjectManager._instance is not None:
    #     raise Exception("Cette classe est un singleton ! Utilisez ProjectManager.instance()")
    
    # ✅ NOUVELLE LOGIQUE :
    if ProjectManager._instance is not None:
        # Si une instance existe déjà, ne pas réinitialiser
        return
    
    # Initialisation normale
    self.current_project = None
    self.project_path = None
    self.auto_save_enabled = True
    self.auto_save_interval = 300  # 5 minutes
    self.backup_versions = 5
    
    # Timer pour auto-sauvegarde
    self.auto_save_timer = QTimer()
    self.auto_save_timer.timeout.connect(self._auto_save)
    
    logger.info("✓ ProjectManager initialisé")