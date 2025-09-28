# html_dashboard_widget.py
import sys
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt  # <- AJOUT DE Qt ICI
from PyQt5.QtGui import QPalette  # <- AJOUT pour les couleurs
from PyQt5.QtCore import QUrl
class DashboardBridge(QObject):
    """Pont de communication entre HTML et PyQt5. Inchangé."""
    module_clicked = pyqtSignal(str)
    
    @pyqtSlot(str)
    def moduleClicked(self, module_name):
        """Méthode appelée depuis JavaScript lorsque l'utilisateur clique sur un module."""
        print(f"📊 Module cliqué depuis HTML: {module_name}")
        self.module_clicked.emit(module_name)

class HTMLCircularDashboard(QWidget):
    """
    Widget PyQt5 intégrant le nouveau dashboard.
    Les animations sont désactivées par défaut et le fond est transparent.
    """
    
    # Signal pour la page d'accueil.
    segment_clicked = pyqtSignal(str) # Nom conservé pour minimiser les changements dans page_accueil.py
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)
        
        # Attribut pour stocker les données de progression
        self.current_progress_data = {}
        
        self.setup_ui()
        self.setup_bridge()
    
    def setup_ui(self):
        """Configure l'interface avec QWebEngineView."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        # Rendre le fond du widget web transparent
        self.web_view.setAttribute(Qt.WA_TranslucentBackground)
        # CORRECTION: Utiliser QColor au lieu de Qt.transparent
        from PyQt5.QtGui import QColor
        self.web_view.page().setBackgroundColor(QColor(0, 0, 0, 0))  # Transparent
        
        html_content = self.get_dashboard_html()
        self.web_view.setHtml(html_content, QUrl("qrc:/"))
        
        layout.addWidget(self.web_view)
    
    def setup_bridge(self):
        """Configure le pont de communication HTML ↔ PyQt5."""
        self.bridge = DashboardBridge()
        # Le signal interne 'module_clicked' est connecté à la méthode on_module_clicked
        self.bridge.module_clicked.connect(self.on_module_clicked)
        
        self.channel = QWebChannel()
        self.channel.registerObject('pyqt_bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)
    
    @pyqtSlot(str)
    def on_module_clicked(self, module_name):
        """Gère le clic reçu de JS et émet le signal `segment_clicked` pour la page d'accueil."""
        self.segment_clicked.emit(module_name)
    
    def set_all_progress(self, progress_data: dict):
        """
        Met à jour le dashboard. Le nom est conservé pour la compatibilité.
        Cette méthode prend les données riches de ProgressManager.
        """
        self.current_progress_data = progress_data
        
        progress_json = json.dumps(self.current_progress_data)
        
        # Appel de la fonction JS pour mettre à jour l'affichage
        js_code = f"window.dashboard.updateProgressFromPython({progress_json});"
        self.web_view.page().runJavaScript(js_code)
    
    def get_dashboard_html(self):
        """
        Retourne le code HTML complet du dashboard avec les modifications :
        1. Background du body transparent.
        2. 'animationEnabled' mis à 'false' par défaut en JavaScript.
        3. Les boutons de contrôle (simuler, etc.) sont retirés.
        """
        return '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Workflow</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        /* MODIFICATION : Fond transparent et anti-aliasing pour le texte */
        body { 
            font-family: 'Inter', 'Segoe UI', sans-serif; 
            background-color: transparent; 
            color: white; 
            min-height: 100vh; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            padding: 20px; 
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5rem; font-weight: 600; color: #ffffff; margin-bottom: 10px; background: linear-gradient(135deg, #00d4aa, #667eea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .header p { font-size: 1.1rem; color: #a0a0b0; font-weight: 300; }
        .dashboard-container { position: relative; width: 400px; height: 400px; margin: 20px 0; }
        .circle-svg { width: 100%; height: 100%; transform: rotate(-90deg); filter: drop-shadow(0 0 30px rgba(0, 212, 170, 0.3)); }
        .segment-background { fill: none; stroke: rgba(255, 255, 255, 0.08); stroke-width: 40; stroke-linecap: round; }
        .segment-progress { fill: none; stroke-width: 36; stroke-linecap: round; transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; transform-origin: center; }
        .segment-progress:hover { stroke-width: 42; filter: brightness(1.2) !important; }
        .segment-project-loaded { stroke: url(#gradientProjectLoaded); }
        .segment-dimcon-validated { stroke: url(#gradientDimconValidated); }
        .segment-gnss-finalized { stroke: url(#gradientGnssFinalized); }
        .segment-comparison-finished { stroke: url(#gradientComparisonFinished); }
        .center-circle { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 180px; height: 180px; background: radial-gradient(circle, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%); border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 2px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(20px); cursor: pointer; transition: all 0.4s ease; box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 212, 170, 0.1); }
        .center-circle:hover { transform: translate(-50%, -50%) scale(1.05); border-color: rgba(0, 212, 170, 0.4); box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5), 0 0 60px rgba(0, 212, 170, 0.3); }
        .global-percentage { font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, #00d4aa, #667eea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 8px; }
        .global-subtitle { font-size: 0.9rem; color: #b0b0c0; text-transform: uppercase; letter-spacing: 1px; text-align: center; line-height: 1.3; }
        .modules-info { font-size: 0.8rem; color: #80808f; margin-top: 8px; }
        .legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 40px; max-width: 800px; width: 100%; }
        .legend-item { display: flex; align-items: center; gap: 12px; padding: 15px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; transition: all 0.3s ease; cursor: pointer; backdrop-filter: blur(10px); }
        .legend-item:hover { background: rgba(255, 255, 255, 0.1); transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); }
        .legend-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: bold; }
        .legend-project-loaded .legend-icon { background: linear-gradient(135deg, #00d4aa, #00b894); }
        .legend-dimcon-validated .legend-icon { background: linear-gradient(135deg, #667eea, #764ba2); }
        .legend-gnss-finalized .legend-icon { background: linear-gradient(135deg, #764ba2, #f093fb); }
        .legend-comparison-finished .legend-icon { background: linear-gradient(135deg, #f093fb, #f8618d); }
        .legend-content { flex: 1; }
        .legend-title { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
        .legend-description { font-size: 0.85rem; color: #a0a0b0; line-height: 1.3; }
        .progress-indicator { font-size: 0.9rem; font-weight: 600; color: #888; }
    </style>
</head>
<body>
    <div class="header"><h1>Dashboard Workflow</h1><p>Suivi des 4 étapes de calibration</p></div>
    <div class="dashboard-container">
        <svg class="circle-svg" viewBox="0 0 400 400">
            <defs>
                <linearGradient id="gradientProjectLoaded" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#00d4aa;stop-opacity:1" /><stop offset="100%" style="stop-color:#00b894;stop-opacity:1" /></linearGradient>
                <linearGradient id="gradientDimconValidated" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#667eea;stop-opacity:1" /><stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" /></linearGradient>
                <linearGradient id="gradientGnssFinalized" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#764ba2;stop-opacity:1" /><stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" /></linearGradient>
                <linearGradient id="gradientComparisonFinished" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" /><stop offset="100%" style="stop-color:#f8618d;stop-opacity:1" /></linearGradient>
            </defs>
            <circle class="segment-background" cx="200" cy="200" r="140" stroke-dasharray="200 20" stroke-dashoffset="0"></circle>
            <circle class="segment-background" cx="200" cy="200" r="140" stroke-dasharray="200 20" stroke-dashoffset="-220"></circle>
            <circle class="segment-background" cx="200" cy="200" r="140" stroke-dasharray="200 20" stroke-dashoffset="-440"></circle>
            <circle class="segment-background" cx="200" cy="200" r="140" stroke-dasharray="200 20" stroke-dashoffset="-660"></circle>
            <circle class="segment-progress segment-project-loaded" cx="200" cy="200" r="140" stroke-dasharray="0 880" stroke-dashoffset="0" data-module="PROJECT_LOADED"></circle>
            <circle class="segment-progress segment-dimcon-validated" cx="200" cy="200" r="140" stroke-dasharray="0 880" stroke-dashoffset="-220" data-module="DIMCON_VALIDATED"></circle>
            <circle class="segment-progress segment-gnss-finalized" cx="200" cy="200" r="140" stroke-dasharray="0 880" stroke-dashoffset="-440" data-module="GNSS_FINALIZED"></circle>
            <circle class="segment-progress segment-comparison-finished" cx="200" cy="200" r="140" stroke-dasharray="0 880" stroke-dashoffset="-660" data-module="COMPARISON_FINISHED"></circle>
        </svg>
        <div class="center-circle" id="centerCircle">
            <div class="global-percentage" id="globalPercentage">0%</div>
            <div class="global-subtitle">Progression<br>Workflow</div>
            <div class="modules-info" id="modulesInfo">0/4 étapes terminées</div>
        </div>
    </div>
    
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        class CircularDashboard {
            constructor() {
                this.moduleProgress = { PROJECT_LOADED: 0, DIMCON_VALIDATED: 0, GNSS_FINALIZED: 0, COMPARISON_FINISHED: 0 };
                // MODIFICATION : Animations désactivées par défaut
                this.animationEnabled = false; 
                this.selectedModule = null;
                this.initializeEventListeners();
            }
            initializeEventListeners() {
                document.querySelectorAll('.segment-progress, .legend-item').forEach(el => {
                    el.addEventListener('click', (e) => this.selectModule(e.currentTarget.dataset.module));
                });
                document.getElementById('centerCircle').addEventListener('click', () => this.showGlobalView());
            }
            updateProgress(moduleData) {
                Object.keys(moduleData).forEach(module => {
                    const progress = moduleData[module].progress || 0;
                    this.moduleProgress[module] = progress;
                    this.animateSegment(module, progress);
                    this.updateLegendProgress(module, progress);
                });
                this.updateGlobalProgress();
            }
            animateSegment(module, targetProgress) {
                const segment = document.querySelector(`.segment-${module.toLowerCase().replace('_', '-')}`);
                if (!segment) return;
                const progressRatio = Math.min(targetProgress / 100, 1);
                const maxSegmentLength = 200;
                const progressLength = maxSegmentLength * progressRatio;
                // La logique d'animation reste mais ne sera exécutée que si animationEnabled est 'true'
                if (this.animationEnabled) {
                    this.animateValue(parseFloat(segment.style.strokeDasharray) || 0, progressLength, 1200, (v) => {
                        segment.style.strokeDasharray = `${v} 880`;
                    });
                } else {
                    segment.style.strokeDasharray = `${progressLength} 880`;
                }
            }
            updateLegendProgress(module, progress) {
                const el = document.getElementById(`progress-${module}`);
                if (el) {
                    el.textContent = Math.round(progress) + '%';
                    if (progress >= 100) el.style.color = '#00d4aa';
                    else if (progress >= 50) el.style.color = '#ffa500';
                    else el.style.color = '#a0a0b0';
                }
            }
            updateGlobalProgress() {
                const modules = Object.values(this.moduleProgress);
                const avgProgress = modules.length > 0 ? modules.reduce((a, b) => a + b, 0) / modules.length : 0;
                const completed = modules.filter(p => p >= 100).length;
                const globalEl = document.getElementById('globalPercentage');
                document.getElementById('modulesInfo').textContent = `${completed}/4 étapes terminées`;
                if (this.animationEnabled) {
                    this.animateValue(parseFloat(globalEl.textContent) || 0, avgProgress, 1500, (v) => {
                        globalEl.textContent = Math.round(v) + '%';
                    });
                } else {
                    globalEl.textContent = Math.round(avgProgress) + '%';
                }
            }
            selectModule(module) {
                this.selectedModule = module;
                document.querySelectorAll('.segment-progress').forEach(s => { s.style.opacity = '0.3'; s.style.filter = 'none'; });
                const selectedSegment = document.querySelector(`.segment-${module.toLowerCase().replace('_', '-')}`);
                if (selectedSegment) { selectedSegment.style.opacity = '1'; selectedSegment.style.filter = 'brightness(1.3) drop-shadow(0 0 20px currentColor)'; }
                
                document.querySelectorAll('.legend-item').forEach(item => { item.style.opacity = '0.5'; item.style.transform = 'none'; });
                const selectedLegend = document.querySelector(`.legend-${module.toLowerCase().replace('_', '-')}`);
                if (selectedLegend) { selectedLegend.style.opacity = '1'; selectedLegend.style.transform = 'translateY(-3px) scale(1.02)'; }
                
                if (window.pyqt_bridge) { window.pyqt_bridge.moduleClicked(module); }
            }
            showGlobalView() {
                this.selectedModule = null;
                document.querySelectorAll('.segment-progress, .legend-item').forEach(el => {
                    el.style.opacity = '1'; el.style.filter = 'none'; el.style.transform = 'none';
                });
            }
            animateValue(start, end, duration, callback) {
                const startTime = performance.now();
                const animate = (currentTime) => {
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const ease = 1 - Math.pow(1 - progress, 3);
                    callback(start + (end - start) * ease);
                    if (progress < 1) requestAnimationFrame(animate);
                };
                requestAnimationFrame(animate);
            }
            updateProgressFromPython(progressData) {
                this.updateProgress(progressData);
            }
        }
        window.dashboard = new CircularDashboard();
        if (typeof QWebChannel !== 'undefined') {
            new QWebChannel(qt.webChannelTransport, (channel) => {
                window.pyqt_bridge = channel.objects.pyqt_bridge;
            });
        }
    </script>
</body>
</html>
        '''