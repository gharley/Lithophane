import os
import sys
import json

from PyQt5 import uic
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QComboBox, QLineEdit, QCheckBox, QFileDialog
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

        self.config = DotDict()
        self.props = DotDict()

        self._load_config()
        self._load_ui()

        self._mesh_plotter = pvqt.QtInteractor(self.plotFrame)
        geo = self.plotFrame.geometry()
        self._mesh_plotter.window_size = [geo.width(), geo.height()]

    def closeEvent(self, event) -> None:
        with open('config.json', 'w') as out_file:
            json.dump(self.config, out_file)

    def _init_connections(self):
        self.actionOpen.triggered.connect(self._load_image)
        self.actionSave.triggered.connect(self._save_model)

    def _init_properties(self):
        self.props = DotDict()
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
            self.process_image()

    def _load_ui(self):
        ui_file = QFile('mainwindow.ui')
        # ui_file = QFile(':resources/mainwindow.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self._init_connections()

        self.show()

        # style_sheet = QFile(':resources/form.qss')
        # if style_sheet.exists():
        #     style_sheet.open(QFile.ReadOnly)
        #     style = str(style_sheet.readAll(), 'utf-8')
        #     self.setStyleSheet(style)
        #     style_sheet.close()
        #
        # self.setWindowIcon(QIcon(':images/end_all.svg'))

    def process_image(self):
        self._init_properties()
        filename = self.config.image_dir
        # filename = "C:/Users/gharley/Pictures/Abby.jpg"
        # filename = "C:/Cloud/Google/Fab/CNC/3D/bee3D.jpg"
        litho = lp.Lithophane()

        self._vertices = litho.prepare_image(filename, self.props)
        pcd, base = litho.create_point_cloud_from_vertices(self._vertices, self.props)
        mesh = litho.create_mesh_from_point_cloud(pcd, base)
        mesh = litho.scale_to_final_size(mesh, self.props)

        geo = self.plotFrame.geometry()
        scale = max(geo.width(), geo.height()) / max(mesh.bounds[1], mesh.bounds[3])

        self._mesh_plotter.add_mesh(mesh.copy().scale(scale, inplace=True), color=[1.0, 1.0, 0.0], point_size=10.0, render_points_as_spheres=True)
        self._mesh_plotter.show_grid()
        self._mesh_plotter.show()
        self._mesh_plotter.window_size = [geo.width(), geo.height()]
        self._mesh_plotter.update()

        self._mesh = mesh

    def _save_model(self):
        if self._mesh is not None:
            filename = os.path.splitext(self.config.image_dir)[0] + '.stl'
            dialog = QFileDialog()

            dir_name = dialog.getSaveFileName(None, 'Save Model', filename, 'Model Files (*.stl)')
            if dir_name[0]:
                self._mesh.save(dir_name[0])


if __name__ == "__main__":
    app = QApplication([])
    main_window = Main()
    sys.exit(app.exec_())
