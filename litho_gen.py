import os
import sys
import json
import threading
import time

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import \
    QApplication, QMainWindow, QLabel, QLineEdit, QCheckBox, \
    QFileDialog, QWidget, QRadioButton, QSlider, QMessageBox

import vtkmodules.all  # DO NOT REMOVE, required for pyinstaller

from PIL import Image, ImageOps
from PIL.ImageQt import ImageQt
import pyvistaqt as pvqt

from common import *
from Lithophane import Lithophane

import litho_gen_rc


class Main(QMainWindow):
    _heights = None
    _mesh = None
    _mesh_id = None
    _mesh_plotter = None

    _is_modelDirty = False

    config = DotDict()
    props = DotDict()

    def __init__(self):
        super().__init__()

        self.config.spec_dir = ''
        self._load_config()
        self._load_ui()
        self._set_control_states()

        self._mesh_plotter = pvqt.QtInteractor(self.plotWidget)
        self._mesh_plotter.show()

        self.resizeEvent(None)

    def closeEvent(self, event) -> None:
        btn = self._check_save()
        if btn == QMessageBox.Save:
            self._save_model()
        elif btn == QMessageBox.Cancel:
            event.ignore()
        else:
            with open('config.json', 'w') as out_file:
                json.dump(self.config, out_file)

    def resizeEvent(self, event) -> None:
        if self._mesh_plotter is not None:
            geo = self.plotWidget.geometry()
            dpi_ratio = app.devicePixelRatio()
            self._mesh_plotter.window_size = [int(geo.width() * dpi_ratio), int(geo.height() * dpi_ratio)]

    def _check_save(self):
        if self._is_modelDirty:
            msg_box = QMessageBox()
            msg_box.setText('The generated model has not been saved.')
            msg_box.setInformativeText('Do you wish to save the model.')
            msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Save)

            return msg_box.exec_()

        return QMessageBox.Discard

    def _init_connections(self):
        self.actionOpen.triggered.connect(self._load_image)
        self.actionSave.triggered.connect(self._save_model)
        self.actionLoad_Settings.triggered.connect(self._load_specs)
        self.actionSave_Settings.triggered.connect(self._save_specs)
        self.actionGenerate.triggered.connect(self.process_image)
        self.btnGenerate.clicked.connect(self.process_image)
        self.actionExit.triggered.connect(self.close)

        self.chkInvert.stateChanged.connect(self._set_pixmap)
        self.chkMirror.stateChanged.connect(self._set_pixmap)
        self.chkSmooth.stateChanged.connect(self._set_control_states)
        self.chkGrid.stateChanged.connect(self._set_control_states)

        self.btnMetric.toggled.connect(self._switch_units)

    def _init_properties(self):
        self.props.statusBar = self.statusBar()
        for obj in self.findChildren(QCheckBox):
            self.props[obj.objectName()] = obj.isChecked()

        for obj in self.findChildren(QSlider):
            self.props[obj.objectName()] = obj.value()

        self.props.btnWidth = self.btnWidth.isChecked()

        factor = 1.0 if self.btnMetric.isChecked() else MM_PER_INCH
        for obj in self.findChildren(QLabel):
            buddy = obj.buddy()
            if buddy is not None:
                buddy_name = buddy.objectName()
                self.props[buddy_name] = int(buddy.text()) if buddy_name.startswith('num') else float(buddy.text()) * factor

    def _load_config(self):
        self.config.image_dir = '/'
        if os.path.exists('config.json'):
            with open('config.json', 'r') as in_file:
                self.config = DotDict(json.load(in_file))

    def _load_image(self):
        if self._is_modelDirty:
            self._check_save()

        dialog = QFileDialog()

        dir_name = dialog.getOpenFileName(None, 'Load Image', self.config.image_dir, 'Images (*.png;*.jpg)')
        if dir_name[0]:
            self.config.image_dir = dir_name[0]
            self.props.img = Image.open(dir_name[0])
            self._set_pixmap()
            self._set_control_states()
            self._set_app_title()

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
                elif key.startswith('sld'):
                    widget.setValue(value)
                else:
                    widget.setText(value)

    def _load_ui(self):
        # ui_file = QFile('litho_gen.ui')
        ui_file = QFile(':ui/litho_gen.ui')
        ui_file.open(QFile.ReadOnly)
        self._main = uic.loadUi(ui_file, self)
        ui_file.close()

        self._init_connections()

        self._set_app_title()
        self.show()

        # style_sheet = QFile('litho_gen.qss')
        style_sheet = QFile(':ui/litho_gen.qss')
        if style_sheet.exists():
            style_sheet.open(QFile.ReadOnly)
            style = str(style_sheet.readAll(), 'utf-8')
            self.setStyleSheet(style)
            style_sheet.close()

        self.setWindowIcon(QIcon(':ui/AppIcon.ico'))

    mesh_id = None

    def process_image(self):
        in_progress = True

        def update_progress():
            value = 1
            while in_progress:
                if value > self.progressBar.maximum():
                    value = 0
                    self.progressBar.reset()

                self.progressBar.setValue(value)
                value += 1
                time.sleep(0.2)

            self.progressBar.setValue(0)

        thread = threading.Thread(target=update_progress)
        thread.start()

        self._init_properties()

        if self._mesh_id is not None:
            self._mesh_plotter.remove_actor(self._mesh_id)

        litho = Lithophane()
        self._mesh = litho.generate_mesh(self.props)

        display_mesh = self._mesh.copy()
        self._mesh_id = self._mesh_plotter.add_mesh(display_mesh, color=[1.0, 1.0, 0.0], render_points_as_spheres=True)
        self._mesh_plotter.add_camera_orientation_widget()
        self._mesh_plotter.view_xy()

        in_progress = False
        self._is_modelDirty = True
        self._set_control_states()
        self._set_app_title()

    def _save_model(self):
        if self._mesh is not None:
            filename = os.path.splitext(self.config.image_dir)[0] + '.stl'
            dialog = QFileDialog()

            dir_name = dialog.getSaveFileName(None, 'Save Model', filename, 'Model Files (*.stl)')
            if dir_name[0]:
                self._mesh.save(dir_name[0])
                self._is_modelDirty = False
                self._set_app_title()

    def _save_specs(self):
        dialog = QFileDialog()

        dir_name = dialog.getSaveFileName(None, 'Save Specifications', self.config.spec_dir, 'Specifications (*.spec)')
        if dir_name[0]:
            self.config.spec_dir = dir_name[0]

            specs = DotDict()
            for child in self.findChildren(QRadioButton):
                specs[child.objectName()] = child.isChecked()

            for child in self.findChildren(QLineEdit):
                specs[child.objectName()] = child.text()

            for child in self.findChildren(QCheckBox):
                specs[child.objectName()] = child.isChecked()

            for child in self.findChildren(QSlider):
                specs[child.objectName()] = child.value()

            with open(dir_name[0], 'w') as out_file:
                json.dump(specs, out_file)

    APP_NAME = 'Lithophane Generator 0.1.0'

    def _set_app_title(self):
        title = self.APP_NAME
        if self.props.img is not None:
            title += ' - ' + self.config.image_dir
        if self._is_modelDirty:
            title += '*'

        self.setWindowTitle(title)

    def _set_control_states(self):
        if self._mesh_plotter is not None:
            if self.chkGrid.isChecked():
                self._mesh_plotter.show_grid()
            else:
                self._mesh_plotter.remove_bounds_axes()

        enable = self.chkSmooth.isChecked()
        self.sldSmooth.setEnabled(enable)
        self.lblMin.setEnabled(enable)
        self.lblMax.setEnabled(enable)

        enable = self.props.img is not None
        self.actionGenerate.setEnabled(enable)
        self.btnGenerate.setEnabled(enable)
        self.chkInvert.setEnabled(enable)
        self.chkMirror.setEnabled(enable)
        self.chkSmooth.setEnabled(enable)
        self.chkGrid.setEnabled(enable)

        self.actionSave.setEnabled(self._mesh is not None)

    def _set_pixmap(self):
        if self.props.img is None: return

        geo = self.leftSideLayout.geometry()
        scale = geo.width() / self.props.img.width
        img = ImageOps.scale(ImageOps.grayscale(self.props.img), scale, True)

        if self.chkInvert.isChecked(): img = ImageOps.invert(img)
        if self.chkMirror.isChecked(): img = ImageOps.mirror(img)

        # noinspection PyTypeChecker
        self.lblImage.setPixmap(QPixmap.fromImage(ImageQt(img)))

    def _switch_units(self):
        if self.btnMetric.isChecked():
            factor = MM_PER_INCH
        else:
            factor = 1 / MM_PER_INCH

        for obj in self.findChildren(QLabel):
            buddy = obj.buddy()
            if buddy is not None:
                buddy_name = buddy.objectName()
                if not buddy_name.startswith('num'):
                    value = round(float(buddy.text()) * factor * 100) / 100
                    buddy.setText(str(value))


if __name__ == "__main__":
    app = QApplication([])
    main_window = Main()
    sys.exit(app.exec_())
