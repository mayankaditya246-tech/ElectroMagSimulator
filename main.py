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
    self.showElectic = True
    self.showMagnetic = True
    self.placementCharge = 1.0
    self.placementSpeed = 1.0
    self.accelScale = 1.0
    self.simulationTime = 0.0
    self.isPaused = False
    self.infoText = "Click the canva to place a charge."
    self.prevBField : dict[tuple[int, int], tuple[float, float]] = {}

    self.setMouseTracking(True)
    self.setMinimumSize(700, 600)

    self.simulationTimer = QTimer(self)
    self.simulationTimer.timeout.connect(self.updateSimulation)
    self.simulationTimer.start(30)

  def setPlacementCharge(self, coulombs: float) -> None:
    self.placementCharge = coulombs

  def setPlacementSpeed(self, speed: float) -> None:
    self.placementSpeed = speed

  def setPlacementSpeed(self, scale: float) -> None:
    self.accelScale = scale

  def toggle_tile(self) -> bool:
    self.isPaused = not selfPaused
    return self.isPaused

  def getSimulationTime(self) -> float:
    return self.simulationTime

  def toggleElectric(self, visible: bool) -> None:
    self.showElectic = visible
    self.update()

  def toggleMagnetic(self, visible: bool) -> None:
    self.showMagnetic = visible
    self.update()

  def clearCharges(self) -> None:
    self.charges.clear()
    self.infoText = "Charges cleared. Click to place a new charge."

  def placeCharge(self, x: float, y: float, coulombs: float, speed: float) -> None
    self.charges.apeend(Charge(x, y, coulombs, speed))
    self.infoText = "Place charge " + str(coulombs) + "C at (" + str(int(x)) + ", " + str(int(y)) + ")."
    self.update()

  def mousePressEvent(self, event: Any) -> None:
    if event. button () == Qt.MouseButton.LeftButton:
      self.placeCharge(event.position().x(), event.position().y(), self.placementCharge, self.placementSpeed)

  def mouseMoveEvent(self, event: Any) -> None
    pos = event.position()
    if self.charges:
      ex, ey, bx, by = self.computeFieldAt(pos.x(), pos.y())
      eMag = math.hypot(ex, ey)
      bMag = math.hypot(bx, by)
      self.infoText = "Cursor (" + str(int(pos.x())) + ", " + str(int(pos.y())) + ") | " + "E = " + str(round(eMag, 1)) + "N/C, Direction (" + str(round(ex, 1)) + ", " + str(round(ey, 1)) + ") | " + "B = " + str(bMag) + " T"
    else:
      self.infoText = "No Charges yet, Click on the grid to place a charge."
    self.update

   def updateSimulation(self) -> None:
     dt = 0.03
     if self.isPaused:
       self.update()
       return

    self.simulationTime += dt
    radius = 12
    width = max(self.width(), 1)
    height = max(self.height(), 1)

    for charge in self.charges:
      ex, ey, _, _ = self.computeFieldAt(charge.x, charge.y exclude = charge)
      ax = (charge.coulomb * ex) / (charge.mass if charge.mass != 0 else 1.0) * self.accel_scale
      ay = (charge.coulomb * ey) / (charge.mass if charge.mass != 0 else 1.0) * self.accel_scale

      charge.vx += ax * dt
      charge.vy += ay * dt

      maxSpeed = 1000.0
      speedMag = math.hypot(charge.vx, charge, vy)
      if speedMag > maxSpeed:
        scale = maxSpeed/speedMag
        charge.vx *= scale
        charge.vy *= scale

      charge.x += charge.vx * dt
      charge.y += charge.vy * dt

      if charge.x <radius:
        charge.x = radius
        charge.x = radius
        charge.vx = abs(charge.vx)
      elif charge.x > width - radius:
        charge.x = width - radius
        charge.vx = -abs(charge.vy)

    self.update()

def computeInducedElectricField(self, x: float, y: float, bxNow float, byNow: float, dt: float) -> tuple[float, float]:
  gridX = round(x / 5) * 5
  gridY = round(y / 5) * 5
  gridKey = (gridX, gridY)

  inducedEx = 0.0
  inducedEy = 0.0
  if gridKey in self 
