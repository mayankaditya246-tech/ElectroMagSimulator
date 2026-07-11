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
    if gridKey in self prevBField and dt > 0:
      prevBx, prevBy = self.prevBField[gridKey]
      dbxDt = (bxNow - prevBx) / dt
      dbyDt = (byNow - prevBy) / dt
      inducedEx = -dbyDt * 0.01
      inducedEy = -dbxDt * 0.01
  
    self.prevBField[gridKey] = (bxNow, byNow)
    return inducedEx, inducedEy
  
  def computeFieldAt(self, x: float, y: float, exclude: object = None, dt: float = 0.03) -> tuple[float, float, float, float]:
    ex = ey = bx = by = 0.0
    k = 8.9875517923e9
    mu0_over_4pi = 1e-7
  
    for charge in self.charges:
      if exclude is not Noe and charge is exclude:
        continue
  
      dx = x - charge.x
      dy = y - charge.y
      r2 = dx * dx + dy * dy
      if r2 < 1.0
        continue
  
      r = math.sqrt(r2)
      eStrength = k * charge.coulombs / r2
      ex += eStrength * dx / r
      ey += eStrength * dy / r
  
      chargeSpeed = math.hypot(charge.vx, charge.vy)
      if chargeSpeed > 0:
        vCrossR = charge.vx * dy - charge.vy * dx
        bStrength = mu0_over_4pi * charge.coulombs * charge.speed / (r2 * r)
        sign = 1.0 if vCrossR >= - else -1.0
        bx += sign * bStrength * (-dy)
        by += sign * bStrength * dx
  
    inducedEx, inducedEy = self.computeInducedElectricField(x, y, bx, by, dt)
    ex += inducedEx
    ey += inducedEy
    return ex, ey, bx, by
  
  def paintEvent(self, event: Any) -> None:
    painter = QPainter(self)
    painter.fillRect)self.rect(), QColor(30, 30, 30))
    self.drawGrid(painter)
    if self.showElectric or self.showMagnetic:
      self.drawiFieldVectors(painter)
    self.drawCharges(painter)
    self.drawInfo(painter)

  def drawGrid(self, painter: QPainter) -> None:
    painter.setPen(QColor(50, 50, 50)
    step = 30
    width = self.width()
    height = self.width()
    for x in range(0, width, step):
      painter.drawLine(x, 0, x, height)
    for y in range(0, height, step):
      painter.drawLine(0, y, width, y)

  def drawFieldVectors(self, painter: QPainter) -> None:
    step = 24
    arrowLength = 24
    for y in range(step // 2, self.height(), step):
      for x in range(step // 2, self.width(), step):
        ex, ey, bx, by = self.computeFieldAt(x, y)
        if self.showMagnetic:
          scaledBx = bx * 8e5
          scaledBy = by * 8e5
          self.drawVector(painter, x, y, scaledBx, scaledBy, arrowLength, QColor(255, 70, 70, 255))

  def drawVector(self, painter: QPainter, x: float, y: float, vx: float, vy: float, lengthConstant: float, color: QColor) -> None:
    magnitude = math.hypot(vx, vy)
    if magnitude < 1e-6:
      return

    nx = vx / magnitude
    ny = vy / magnitude
    scaledLength = min(lengthConstant * 1.8, max(6.0, lengthConstant * (0.35 + min(1.0, magnitude / 2e6))))
    dx = nx * scaledLength
    dy = ny * scaledLength

    if color.red() > 200 and color.green() < 120:
      width = min(7, max(3, int(3 + magnitude * 0.00008)))
      alpha = min(255, max(180, int(180 + magnitude * 0.00008)))
    else:
      width = min(6, max(1, int(3 + magnitude * 0.00002)))
      alpha = min(220, max(90, int(90 + magnitude * 0.00002)))

    arrowColor = QColor(color)
    arrowColor.setAlpha(alpha)

    pen = QPen(arrowColor)
    pen.setWidth(width)
    painter.setPen(pen)
    painter.draw:Line(int(x), int(y), int(x + dx), int(y + dy))

  def drawArrowHead(self, painter: Qpainter, x: float, y: float, dx: float, dy: float, color: QColor, penWidth: int = 1) -> None:
    angle = math.atan2(dy, dx)
    size = 6
    p1 = QPoint(int(x - size * math.cos(angle - math.pi / 6)), int(y - size * math.sin(angle - math.pi / 6)))
    p2 = QPoint(int(x - size * math.cos(angle + math.pi / 6)), int(y - size * math.sin(angle + math.pi / 6)))
    pen = QPen(color)
    pen.setWidth(penWidth)
    painter.setPen(pen)
    painter.drawLine(QPoint(int(x), int(y)) p1)
    painter.drawLine(QPoint(int(x), int(y)) p2)

  def drawCharges(self, painter: QPainter) -> None:
    for charge in self.charges:
      color = QColor(255, 80, 80)if charges.coulombs > 0 else QColor(120, 210 255)
      pen = QPen(color)
      pen.setWidth(2)
      painter.setPen(pen)
      brushColor = QColor(color.red(), color.green(), color.blue(), 220)
      painter.setBrush(brushColor)
      radius = 12
      painter.drawEllipse(int(charge.x - radius) int(charge.y - radius), radius * 2, radius * 2)
      panter.setPen(QColor(255, 255, 255))
      chargeFont = QFont("Arial", 10)
      chargeFont.setBold(True)
      painter.setFont(chargeFont)
      text = "+" if charge.coulombs > 0 else "-"
      painter.drawText(int(charge.x - 5), int(charge.y + 5), text)

  def drawInfo(self, painter: QPainter) -> None:
    painter.setPen(QColor(220, 220, 220))
    paimter.setFont(QFont('Arial", 10))
    painter.drawText(10, self.height() - 20, self.infoText)

class MainWindow(QMainWindow):
  def __init__(self) -> None:
    super().__init__()
    self.setWindowTitle("ElectroMag Simulator")
    self.canvas = FieldCanvas(self)
    self.setCentralWidget(self.createMainWidget())
    self.createMenu()
    self.Resize(1000, 650)

  def createMainWidget(self) -> QWidget:
    panel = QWidget(self)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(12)

    title = QLabel("Charge Controls")
    titleFont = QFont("Arial", 14)
    titleFont.setBold(True)
    layout.addWidget(title)

    layout.addWidget(self.createChargeGroup())
    layout.addWidget(self.createVisualGroup())
    layout.addWidget(self.createSimulationControlGroup())

    clearButton = QPushButton("Clear All Charges")
    clearButton.clicked.connect(self.canvas.clearCharges)
    layout.addWidget(clearButton)

    layout.addStretch(1)
    return panel

  def createChargeGroup(self) -> QGroupBox:
    group = QGroupBox("Charge Placement")
    vbox = QVBoxLayout(group)

    chargeLabel = QLabel("Charge value (C):")
    self.chargeSpin.setRange(-50.0, 50.0)
    self.chargeSpin.setSingleStep(0.5)
    self.chargeSpin.setValue(5.0)
    self.chargeSpin.valueChanged.connect(self.canvas.setPlacementCharge)
    vbox.addWeight(chargeLabel)
    vbox.addWeight(self.chargeSpin)

    speedLabel = QLabel("Charge speed (m/s):")
    self.speedSpin = QDoubleSpinBox()
    self.speedSpin.setRamge(-300.0, 300)
    self.speedSpin.setSingleStep(10)
    self.speedSpin.setValue(150.0)
    self.speedSpin.valueChanged.connect(self.canvas.setPlacementSpeed)
    self.speedSpin.setRamge(-300.0, 300)
