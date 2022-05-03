import os
import sys
import json
import threading
import time

import litho_gen_rc

import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import QFile, QDir
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QCheckBox, QFileDialog, QWidget
from PIL import Image
import pyvistaqt as pvqt

from common import DotDict
import Lithophane as lp


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self._img = None
        self._heights = None
        self._vertices = None
        self._mesh = None
        self._img_id = None
        self._mesh_id = None
        self._mesh_plotter = None

        self.config = DotDict()
        self.config.spec_dir = ''

        self.props = DotDict()

        self._load_config()
        self._load_ui()

        self._mesh_plotter = pvqt.QtInteractor(self.plotWidget)
        geo = self.plotWidget.geometry()
        self._mesh_plotter.window_size = [geo.width(), geo.height()]

    def closeEvent(self, event) -> None:
        with open('config.json', 'w') as out_file:
            json.dump(self.config, out_file)

    def resizeEvent(self, event) -> None:
        if self._mesh_plotter is not None:
            geo = self.plotWidget.geometry()
            self._mesh_plotter.window_size = [geo.width(), geo.height()]
            self._mesh_plotter.update()

    def _init_connections(self):
        self.actionOpen.triggered.connect(self._load_image)
        self.actionSave.triggered.connect(self._save_model)
        self.actionLoad_Settings.triggered.connect(self._load_specs)
        self.actionSave_Settings.triggered.connect(self._save_specs)
        self.actionGenerate.triggered.connect(self.process_image)
        self.btnGenerate.clicked.connect(self.process_image)
        self.actionExit.triggered.connect(self.close)

    def _init_properties(self):
        for obj in self.findChildren(QCheckBox):
            self.props[obj.objectName()] = obj.isChecked()

        for obj in self.findChildren(QLabel):
            buddy = obj.buddy()
            if buddy is not None:
                buddy_name = buddy.objectName()
                self.props[buddy_name] = int(buddy.text()) if buddy_name.startswith('num') else float(buddy.text())

    def _load_config(self):
        self.config.image_dir = '/'
        if os.path.exists('config.json'):
            with open('config.json', 'r') as in_file:
                self.config = DotDict(json.load(in_file))

    def _load_image(self):
        dialog = QFileDialog()

        dir_name = dialog.getOpenFileName(None, 'Load Image', self.config.image_dir, 'Images (*.png;*.jpg)')
        if dir_name[0]:
            self.config.image_dir = dir_name[0]
            self.props.img = Image.open(dir_name[0])
            scale = 300.0 / self.props.img.width
            self.lblImage.setPixmap(QPixmap(dir_name[0]).scaled(self.props.img.width * scale, self.props.img.height * scale))

    def _load_specs(self):
        dialog = QFileDialog()

        dir_name = dialog.getOpenFileName(None, 'Load Specifications', self.config.spec_dir, 'Specifications (*.spec)')
        if dir_name[0]:
            self.config.spec_dir = dir_name[0]

            with open(dir_name[0], 'r') as in_file:
                specs = DotDict(json.load(in_file))

            for key, value in specs.items():
                widget = self.findChild(QWidget, key)
                if widget is None: continue

                if key.startswith('chk') or key.startswith('btn'):
                    widget.setChecked(value)
                else:
                    widget.setText(value)

    def _load_ui(self):
        ui_file = QFile('litho_gen.ui')
        # ui_file = QFile(':ui/litho_gen.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self._init_connections()
        self.resize(1920, 1080)

        self.show()

        style_sheet = QFile('litho_gen.qss')
        # style_sheet = QFile(':ui/litho_gen.qss')
        if style_sheet.exists():
            style_sheet.open(QFile.ReadOnly)
            style = str(style_sheet.readAll(), 'utf-8')
            self.setStyleSheet(style)
            style_sheet.close()
        #
        # self.setWindowIcon(QIcon(':images/end_all.svg'))

    mesh_id = None

    def process_image(self):
        in_progress = True

        def update_progress():
            value = 0
            while in_progress:
                if value > self.progressBar.maximum():
                    value = 0
                    self.progressBar.reset()

                self.progressBar.setValue(value)
                value += 1
                time.sleep(0.5)

            self.progressBar.setValue(0)

        thread = threading.Thread(target=update_progress)
        thread.start()

        self._init_properties()

        if self._mesh_id is not None:
            self._mesh_plotter.remove_actor(self._mesh_id)

        litho = lp.Lithophane()

        self._vertices = litho.prepare_image(self.props)
        pcd, base = litho.create_point_cloud_from_vertices(self._vertices, self.props)
        mesh = litho.create_mesh_from_point_cloud(pcd, base)
        mesh = litho.scale_to_final_size(mesh, self.props)

        geo = self.plotWidget.geometry()
        scale = max(geo.width(), geo.height()) / max(mesh.bounds[1], mesh.bounds[3])
        matrix = np.array([
            [scale, 0, 0, 0],
            [0, scale, 0, 0],
            [0, 0, scale, 0],
            [0, 0, 0, 1]])

        self._mesh_id = self._mesh_plotter.add_mesh(mesh.copy().transform(matrix), color=[1.0, 1.0, 0.0], render_points_as_spheres=True, pbr=False,
                                                    metallic=1.0)
        # self._mesh_plotter.add_camera_orientation_widget()
        self._mesh_plotter.show_axes()
        self._mesh_plotter.show()
        self._mesh_plotter.window_size = [geo.width(), geo.height()]
        self._mesh_plotter.view_xy()
        self._mesh_plotter.update()

        self._mesh = mesh

        in_progress = False

    def _save_model(self):
        if self._mesh is not None:
            filename = os.path.splitext(self.config.image_dir)[0] + '.stl'
            dialog = QFileDialog()

            dir_name = dialog.getSaveFileName(None, 'Save Model', filename, 'Model Files (*.stl)')
            if dir_name[0]:
                self._mesh.save(dir_name[0])

    def _save_specs(self):
        dialog = QFileDialog()

        dir_name = dialog.getSaveFileName(None, 'Save Specifications', self.config.spec_dir, 'Specifications (*.spec)')
        if dir_name[0]:
            self.config.spec_dir = dir_name[0]

            specs = DotDict()
            for child in self.findChildren(QLineEdit):
                specs[child.objectName()] = child.text()

            for child in self.findChildren(QCheckBox):
                specs[child.objectName()] = child.isChecked()

            with open(dir_name[0], 'w') as out_file:
                json.dump(specs, out_file)


if __name__ == "__main__":
    app = QApplication([])
    main_window = Main()
    sys.exit(app.exec_())
