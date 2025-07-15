from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QGroupBox, QFormLayout, QHeaderView, QSplitter,
                            QSpinBox, QDoubleSpinBox, QMessageBox)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from functools import partial

class DimconWidget(QWidget):
    """
    Page pour la définition des dimensions des points de référence du navire
    Implémente l'interface standard attendue par le gestionnaire d'application
    """
    # Signal pour informer qu'un point a été mis à jour
    point_updated = pyqtSignal(str, dict)
    
    def __init__(self, app_data=None):
        super().__init__()
        self.setObjectName("DimconWidget")
        
        # Stocker la référence au modèle de données central
        self.app_data = app_data
        
        # Initialisation des données avec les points spécifiques
        P1xyz = np.array([-0.269318, -64.232461, 10.88835])  # Bow
        P2xyz = np.array([-9.34689, -27.956415, 13.491246])  # Port
        P3xyz = np.array([9.39156, -27.827088, 13.505628])   # STB
        
        # Structure des données adaptée pour être compatible avec app_data
        self.points_data = {
            "Bow": {"X": P1xyz[0], "Y": P1xyz[1], "Z": P1xyz[2]},
            "Port": {"X": P2xyz[0], "Y": P2xyz[1], "Z": P2xyz[2]},
            "Stb": {"X": P3xyz[0], "Y": P3xyz[1], "Z": P3xyz[2]}
        }

        # Configuration de l'UI
        self.setupUI()
        
        # Mise à jour initiale de l'affichage 3D
        self.update_3d_view()
    def set_data_model(self, app_data):
        """Méthode pour définir le modèle de données central après l'initialisation"""
        self.app_data = app_data
        
        # Synchroniser avec le modèle existant
        self.sync_with_model()
        
        # Définir comment mettre à jour les données en fonction des méthodes disponibles
        if hasattr(self.app_data, 'update_dimcon_points'):
            # Si la méthode existe, l'utiliser directement
            self.point_updated.connect(self.update_app_data)
        else:
            # Sinon, créer une méthode temporaire qui accède directement aux attributs
            def update_dimcon_direct(point_id, point_data):
                """Met à jour directement les données dimcon dans app_data"""
                if hasattr(self.app_data, 'dimcon_points'):
                    coords = [point_data["X"], point_data["Y"], point_data["Z"]]
                    self.app_data.dimcon_points[point_id] = coords
            
            # Connecter notre signal à cette méthode temporaire
            self.point_updated.connect(update_dimcon_direct)
    
    def on_point_changed(self, point_id, coordinate, value):
        """Appelée quand une valeur de point est modifiée dans l'interface"""
        # Mettre à jour la structure de données locale
        self.points_data[point_id][coordinate] = value
        
        # Mettre à jour la vue 3D
        self.update_3d_view()
        
        # Émettre le signal de mise à jour pour le modèle central
        self.point_updated.emit(point_id, self.points_data[point_id])


    def update_app_data_point(self, point_id, point_data):
        """Met à jour les points dans le modèle de données central"""
        if self.app_data and hasattr(self.app_data, 'dimcon'):
            # Initialiser le dictionnaire si nécessaire
            if self.app_data.dimcon is None:
                self.app_data.dimcon = {}
                
            # Mettre à jour le point spécifique
            self.app_data.dimcon[point_id] = point_data
            
            # Émettre un signal pour informer les autres widgets
            self.app_data.data_changed.emit("dimcon")

    def setupUI(self):
        # Layout principal avec splitter
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # ---- Partie gauche (tableau) ----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre
        title_label = QLabel("Configuration des points DIMCON")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        left_layout.addWidget(title_label)
        
        # Tableau
        self.data_table = QTableWidget(3, 4)  # 3 lignes, 4 colonnes
        self.data_table.setHorizontalHeaderLabels(["ID_pts", "X", "Y", "Z"])
        self.data_table.setVerticalHeaderLabels(["", "", ""])
        
        # Configuration du style du tableau
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #8e44ad;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
                padding: 5px;
                border: 1px solid #555555;
            }
        """)
        
        # ID de points fixes
        point_ids = ["Bow", "Port", "Stb"]
        
        # Créer un QTableWidgetItem pour chaque cellule
        for row, point_id in enumerate(point_ids):
            # Colonne ID (non éditable)
            id_item = QTableWidgetItem(point_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            id_item.setBackground(QColor("#444444"))
            self.data_table.setItem(row, 0, id_item)
            
            # Colonnes X, Y, Z - utilisons des spin boxes pour l'édition
            for col, coord in enumerate(["X", "Y", "Z"], 1):
                self.data_table.setCellWidget(row, col, self.create_double_spin_box(point_id, coord))
        
        # Ajuster la taille des colonnes
        header = self.data_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        left_layout.addWidget(self.data_table)
        
        # Bouton d'aide
        help_button = QPushButton("?")
        help_button.setFixedSize(25, 25)
        help_button.clicked.connect(self.show_help)
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        
        # Bouton de mise à jour
        update_button = QPushButton("Mettre à jour l'affichage 3D")
        update_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9b59b6;
            }
        """)
        update_button.clicked.connect(self.update_3d_view)
        
        # Layout pour les boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(help_button)
        buttons_layout.addWidget(update_button)
        left_layout.addLayout(buttons_layout)
        
        splitter.addWidget(left_widget)
        
        # ---- Partie droite (visualisation 3D) ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre
        view_title = QLabel("Visualisation 3D")
        view_title.setFont(QFont("Arial", 12, QFont.Bold))
        view_title.setStyleSheet("color: white; margin-bottom: 10px;")
        right_layout.addWidget(view_title)
        
        # Description de l'orientation
        orientation_desc = QLabel("Orientation: X (rouge) - bâbord/tribord, Y (vert) - avant, Z (bleu) - altitude")
        orientation_desc.setStyleSheet("color: #bbbbbb; margin-bottom: 10px;")
        right_layout.addWidget(orientation_desc)
        
        # Initialiser PyQtGraph
        pg.setConfigOption('background', '#2a2a2a')
        pg.setConfigOption('foreground', 'w')
        
        # Widget 3D
        self.gl_widget = gl.GLViewWidget()
        # Ajuster la position de la caméra pour avoir Z vertical et Y vers l'avant
        self.gl_widget.setCameraPosition(distance=70, elevation=30, azimuth=-45)
        self.gl_widget.opts['fov'] = 45
        right_layout.addWidget(self.gl_widget)
        self.gl_widget.setMinimumHeight(600)
        
        # Grille - sur le plan XY (Z=0)
        self.grid = gl.GLGridItem()
        self.grid.setSize(200, 200, 0)  # Profondeur 0 pour la grille
        self.grid.setSpacing(20, 20, 0)   # Espacement
        self.gl_widget.addItem(self.grid)
        
        # Axes 3D
        self.axis_x = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [30, 0, 0]]), color=(1, 0, 0, 1), width=2)
        self.axis_y = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 30, 0]]), color=(0, 1, 0, 1), width=2)
        self.axis_z = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 0, 30]]), color=(0, 0, 1, 1), width=2)
        
        self.gl_widget.addItem(self.axis_x)
        self.gl_widget.addItem(self.axis_y)
        self.gl_widget.addItem(self.axis_z)
        
        # Contrôles de caméra
        camera_controls = QGroupBox("Contrôles Caméra")
        camera_controls.setStyleSheet("""
            QGroupBox {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
        """)
        
        controls_layout = QVBoxLayout(camera_controls)
        
        # Boutons de vue
        view_layout = QHBoxLayout()
        
        top_view_btn = QPushButton("Vue du dessus")
        top_view_btn.clicked.connect(lambda: self.set_camera_view('top'))
        
        front_view_btn = QPushButton("Vue de face")
        front_view_btn.clicked.connect(lambda: self.set_camera_view('front'))
        
        side_view_btn = QPushButton("Vue de côté")
        side_view_btn.clicked.connect(lambda: self.set_camera_view('side'))
        
        reset_view_btn = QPushButton("Vue par défaut")
        reset_view_btn.clicked.connect(lambda: self.set_camera_view('default'))
        
        for btn in [top_view_btn, front_view_btn, side_view_btn, reset_view_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #666666;
                }
            """)
            view_layout.addWidget(btn)
        
        controls_layout.addLayout(view_layout)
        right_layout.addWidget(camera_controls)
        
        splitter.addWidget(right_widget)
        
        # Ajuster la taille du splitter
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)

    def create_double_spin_box(self, point_id, coord):
        """Crée un QDoubleSpinBox pour l'édition des coordonnées"""
        spin_box = QDoubleSpinBox()
        spin_box.setRange(-100.0, 100.0)
        spin_box.setDecimals(3)
        spin_box.setSingleStep(0.1)
        spin_box.setValue(self.points_data[point_id][coord])
        spin_box.valueChanged.connect(partial(self.on_value_changed, point_id, coord))
        spin_box.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #555555;
                width: 16px;
                border: none;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #666666;
            }
        """)
        return spin_box
    def on_point_changed(self, point_id, coordinate, value):
        """Appelée quand une valeur de point est modifiée dans l'interface"""
        # Mettre à jour la structure de données locale
        self.points_data[point_id][coordinate] = value
        
        # Mettre à jour la vue 3D
        self.update_3d_view()
        
        # Émettre le signal de mise à jour pour le modèle central
        if self.app_data:
            self.point_updated.emit(point_id, self.points_data[point_id])
    def on_value_changed(self, point_id, coord, value):
        """Gère le changement de valeur dans un QDoubleSpinBox"""
        self.points_data[point_id][coord] = value
        
        # Émettre le signal si le modèle de données est disponible
        if self.app_data:
            # Créer un dictionnaire avec les valeurs actuelles
            point_data = self.points_data[point_id].copy()
            # Émettre le signal
            self.point_updated.emit(point_id, point_data)

    def update_3d_view(self):
        """Met à jour l'affichage 3D en fonction des données du tableau"""
        # Supprimer les anciens éléments
        for item in self.gl_widget.items[:]:
            if isinstance(item, (gl.GLMeshItem, gl.GLScatterPlotItem, gl.GLLinePlotItem)) and item not in [self.axis_x, self.axis_y, self.axis_z, self.grid]:
                self.gl_widget.removeItem(item)
        
        # Créer une forme de bateau plus sophistiquée
        bow_y = self.points_data["Bow"]["Y"]  # Coordonnée Y de la proue
        port_x = self.points_data["Port"]["X"]  # Coordonnée X bâbord
        stb_x = self.points_data["Stb"]["X"]  # Coordonnée X tribord
        
        # Forme de bateau avec plus de points pour une silhouette plus détaillée
        vertices_green = np.array([
            [0, abs(bow_y) * 1.3, 0.0],                 # P0 - Proue (avant pointu)
            [port_x * 0.9, abs(bow_y) * 0.8, 0.0],      # P1 - Avant gauche
            [port_x * 1.2, 0, 0.0],                     # P2 - Milieu gauche (plus large)
            [port_x * 1.2, -abs(bow_y) * 1.2, 0.0],     # P3 - Arrière gauche
            [0, -abs(bow_y) * 1.2, 0.0],                # P4 - Poupe (arrière)
            [stb_x * 1.2, -abs(bow_y) * 1.2, 0.0],      # P5 - Arrière droit
            [stb_x * 1.2, 0, 0.0],                      # P6 - Milieu droit (plus large)
            [stb_x * 0.9, abs(bow_y) * 0.8, 0.0],       # P7 - Avant droit
        ])
        
        # Définition des faces - le bateau est formé de triangles adjacents
        faces_green = np.array([
            [0, 1, 2],  # Avant-gauche
            [0, 2, 6],  # Avant-milieu
            [0, 6, 7],  # Avant-droit
            [2, 3, 4],  # Arrière-gauche
            [2, 4, 6],  # Arrière-milieu
            [4, 5, 6],  # Arrière-droit
        ])
        
        green_mesh = gl.GLMeshItem(
            vertexes=vertices_green, 
            faces=faces_green, 
            smooth=False, 
            drawEdges=True,
            edgeColor=(0, 0.8, 0, 1),
            color=(0, 0.8, 0, 0.5)
        )
        self.gl_widget.addItem(green_mesh)
        
        # Plan des points (rouge) - forme triangle
        vertices_red = np.array([
            [self.points_data["Bow"]["X"], self.points_data["Bow"]["Y"], self.points_data["Bow"]["Z"]],
            [self.points_data["Port"]["X"], self.points_data["Port"]["Y"], self.points_data["Port"]["Z"]],
            [self.points_data["Stb"]["X"], self.points_data["Stb"]["Y"], self.points_data["Stb"]["Z"]]
        ])
        
        faces_red = np.array([[0, 1, 2]])
        
        red_mesh = gl.GLMeshItem(
            vertexes=vertices_red, 
            faces=faces_red, 
            smooth=False, 
            drawEdges=True,
            edgeColor=(0.8, 0, 0, 1),
            color=(0.8, 0, 0, 0.5)
        )
        self.gl_widget.addItem(red_mesh)
        
        # Couleurs pour les points
        point_colors = {
            "Bow": (1.0, 0.0, 1.0, 1.0),   # Magenta
            "Port": (1.0, 0.5, 0.0, 1.0),  # Orange
            "Stb": (0.0, 1.0, 1.0, 1.0)    # Cyan
        }
        
        # Dessiner des marqueurs pour les points
        for point_id, coords in self.points_data.items():
            # Dessiner un marqueur en croix pour chaque point
            size = 2.0  # Taille de la croix
            
            # Croix horizontale (plan XY)
            x_line = np.array([
                [coords["X"]-size, coords["Y"], coords["Z"]],
                [coords["X"]+size, coords["Y"], coords["Z"]]
            ])
            y_line = np.array([
                [coords["X"], coords["Y"]-size, coords["Z"]],
                [coords["X"], coords["Y"]+size, coords["Z"]]
            ])
            
            # Croix verticale (axe Z)
            z_line = np.array([
                [coords["X"], coords["Y"], coords["Z"]-size],
                [coords["X"], coords["Y"], coords["Z"]+size]
            ])
            
            # Ajouter les lignes de la croix
            for line_pos in [x_line, y_line, z_line]:
                cross_line = gl.GLLinePlotItem(
                    pos=line_pos,
                    color=point_colors[point_id],
                    width=3,
                    mode='lines',
                    antialias=True
                )
                self.gl_widget.addItem(cross_line)
            
            # Ajouter des lignes de projection sur le plan XY (z=0)
            if abs(coords["Z"]) > 0.001:  # Utiliser une petite tolérance pour éviter des problèmes de précision
                projected = [coords["X"], coords["Y"], 0]
                line_pos = np.array([[coords["X"], coords["Y"], coords["Z"]], projected])
                projection_line = gl.GLLinePlotItem(
                    pos=line_pos,
                    color=(0.8, 0.8, 0.8, 0.5),
                    width=1.5,
                    mode='lines',
                    antialias=True
                )
                self.gl_widget.addItem(projection_line)
                
                # Ajouter un marqueur en croix à la projection (comme pour le point)
                px_line = np.array([
                    [projected[0]-size/2, projected[1], 0],
                    [projected[0]+size/2, projected[1], 0]
                ])
                py_line = np.array([
                    [projected[0], projected[1]-size/2, 0],
                    [projected[0], projected[1]+size/2, 0]
                ])
                
                for proj_line_pos in [px_line, py_line]:
                    proj_cross_line = gl.GLLinePlotItem(
                        pos=proj_line_pos,
                        color=(0.7, 0.7, 0.7, 0.7),
                        width=2,
                        mode='lines',
                        antialias=True
                    )
                    self.gl_widget.addItem(proj_cross_line)

    def set_camera_view(self, view_type):
        """Change la position de la caméra pour différentes vues prédéfinies"""
        if view_type == 'top':
            # Vue du dessus (Z vers le haut)
            self.gl_widget.setCameraPosition(distance=70, elevation=90, azimuth=0)
        elif view_type == 'front':
            # Vue de face (Y vers l'avant) - Y est négatif pour les points fournis
            self.gl_widget.setCameraPosition(distance=70, elevation=0, azimuth=0)
        elif view_type == 'side':
            # Vue de côté (X vers le côté)
            self.gl_widget.setCameraPosition(distance=70, elevation=0, azimuth=90)
        else:  # default
            # Vue par défaut (diagonale)
            self.gl_widget.setCameraPosition(distance=70, elevation=30, azimuth=-45)

    def show_help(self):
        """Affiche une aide sur les points clés"""
        help_text = """
        <b>Points clés du navire:</b><br>
        <ul>
        <li><b>Bow (Proue)</b>: Point avant du navire</li>
        <li><b>Port (Bâbord)</b>: Point arrière gauche</li>
        <li><b>Stb (Tribord)</b>: Point arrière droit</li>
        </ul>
        <p>Ces trois points définissent le plan de référence du navire, 
        utilisé pour calculer les transformations des capteurs.</p>
        """
        
        QMessageBox.information(self, "Aide - Points clés", help_text)

    # Méthodes pour l'intégration avec le modèle de données central
    def sync_with_model(self):
        """Synchronise les données locales avec le modèle central"""
        if not self.app_data:
            return
        
        # Vérifier quel attribut est disponible dans app_data
        points = None
        if hasattr(self.app_data, 'dimcon_points'):
            points = self.app_data.dimcon_points
        elif hasattr(self.app_data, 'dimcon'):
            points = self.app_data.dimcon
        
        # Si nous avons trouvé les données, mettre à jour l'interface
        if points:
            # Convertir le format du modèle au format de notre widget
            for point_id in ["Bow", "Port", "Stb"]:
                if point_id in points:
                    coords = points[point_id]
                    
                    # Gérer différents formats possibles
                    if isinstance(coords, list) and len(coords) == 3:
                        # Format [X, Y, Z]
                        self.points_data[point_id] = {"X": coords[0], "Y": coords[1], "Z": coords[2]}
                    elif isinstance(coords, dict) and all(k in coords for k in ["X", "Y", "Z"]):
                        # Format {X: x, Y: y, Z: z}
                        self.points_data[point_id] = coords.copy()
                    
                    # Mettre à jour l'interface
                    for i, coord_name in enumerate(["X", "Y", "Z"]):
                        row = ["Bow", "Port", "Stb"].index(point_id)
                        spin_box = self.data_table.cellWidget(row, i+1)
                        if spin_box and coord_name in self.points_data[point_id]:
                            spin_box.setValue(self.points_data[point_id][coord_name])
            
            # Mettre à jour la vue 3D
            self.update_3d_view()
    
    def on_app_data_changed(self, section):
        """Réagit aux changements dans le modèle central"""
        if section == "dimcon":
            self.sync_with_model()
