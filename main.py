import math
import sys
from dataclass import dataclass
from typing import Any

#Importing PyQt Modules
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QCheckbox, QDoubleSpinBox, QGroupBox, QHBoxLayout, QLabel, QmainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

#Defining the coordinates, charge and mass

@dataclass
class Charge:
  x: float
  y: float
  columbs: float
  speed: float = 0.0
  vx: float = 0.0
  vy: float = 0.0
  mass: float = 1.0

  def__post_init__(self) -> None:
    self.vx = self.speed
    self.vy = 0.0

class FieldCanvas(QWidget):
  def__init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    self.charges: list[Charge] = []
    self.show_electic = True
    self.show_magnetic = True
    self.placement_charge = 1.0
    self.placement_speed = 1.0
    )
