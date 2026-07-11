"""
Electromagnetism Simulator - little Qt toy for visualizing E/B fields from moving point charges.
Started this as a demo for a physics class, kept adding stuff. Not production code, just have fun with it.
"""
import itertools  # leftover from when I tried pairwise combinations for a force-graph experiment, unused now
import math
import sys
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# physics constants - Coulomb's constant and mu0/4pi (SI-ish, though our units are pixels not meters so
# take the actual field magnitudes with a grain of salt, this is mostly tuned to look right, not be right)
K_COULOMB = 8.9875517923e9
MU0_OVER_4PI = 1e-7
CHARGE_RADIUS = 12
MAX_SPEED = 1000.0  # px/s. without this cap two opposite charges getting close basically explode to infinity

DEBUG = False  # flip on for console spam about field values near the cursor, handy when tuning fudge factors


@dataclass
class Charge:
    x: float
    y: float
    coulombs: float
    speed: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 1.0

    def __post_init__(self):
        # charges start moving purely along x for now - could add a launch angle control later but
        # honestly the current UI is cramped enough already
        self.vx = self.speed
        self.vy = 0.0


class FieldCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.charges = []
        self.show_electric = True
        self.show_magnetic = True
        self.placement_charge = 1.0
        self.placement_speed = 1.0
        self.accel_scale = 1.0
        self.simulation_time = 0.0
        self.is_paused = False
        self.info_text = 'Click the canvas to place a charge.'

        # keeps last frame's B field per grid cell so we can estimate dB/dt for induced E
        # (rough approximation, not a real Maxwell solver, but good enough visually)
        self.prev_b_field = {}

        self.setMouseTracking(True)
        self.setMinimumSize(700, 600)

        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(self.update_simulation)
        self.simulation_timer.start(30)  # ~33 fps, matches the 0.03 dt below

    def set_placement_charge(self, coulombs):
        self.placement_charge = coulombs

    def set_placement_speed(self, speed):
        self.placement_speed = speed

    def set_accel_scale(self, scale):
        self.accel_scale = scale

    def toggle_time(self):
        self.is_paused = not self.is_paused
        return self.is_paused

    def get_simulation_time(self):
        return self.simulation_time

    def toggle_electric(self, visible):
        self.show_electric = visible
        self.update()

    def toggle_magnetic(self, visible):
        self.show_magnetic = visible
        self.update()

    def clear_charges(self):
        self.charges.clear()
        self.info_text = "Charges cleared. Click to place a new charge."
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self.place_charge(pos.x(), pos.y(), self.placement_charge, self.placement_speed)

    def mouseMoveEvent(self, event):
        pos = event.position()
        if not self.charges:
            self.info_text = "No charges yet. Click to place a charge."
            self.update()
            return

        ex, ey, bx, by = self.compute_field_at(pos.x(), pos.y())
        e_mag = math.hypot(ex, ey)
        b_mag = math.hypot(bx, by)
        if DEBUG:
            print(f"[mousemove] pos=({pos.x():.0f},{pos.y():.0f}) E={e_mag:.2f} B={b_mag:.2e}")
        self.info_text = (
            f"Cursor ({int(pos.x())}, {int(pos.y())}) | "
            f"E = {e_mag:.1f} N/C, direction ({ex:.1f}, {ey:.1f}) | "
            f"B = {b_mag:.1e} T"
        )
        self.update()

    def update_simulation(self):
        dt = 0.03
        if self.is_paused:
            self.update()
            return

        self.simulation_time += dt
        width = max(self.width(), 1)
        height = max(self.height(), 1)

        # TODO: this is O(n^2) per frame (every charge checks every other charge in compute_field_at).
        # fine for a handful of charges, would need a spatial grid or something if this ever needs to
        # handle more than ~20-30 at once
        for charge in self.charges:
            ex, ey, _, _ = self.compute_field_at(charge.x, charge.y, exclude=charge)
            mass = charge.mass if charge.mass != 0 else 1.0
            ax = (charge.coulombs * ex) / mass * self.accel_scale
            ay = (charge.coulombs * ey) / mass * self.accel_scale

            charge.vx += ax * dt
            charge.vy += ay * dt

            # clamp speed, otherwise close encounters between opposite charges send things to infinity
            speed_mag = math.hypot(charge.vx, charge.vy)
            if speed_mag > MAX_SPEED:
                scale = MAX_SPEED / speed_mag
                charge.vx *= scale
                charge.vy *= scale

            charge.x += charge.vx * dt
            charge.y += charge.vy * dt

            # bounce off the walls - not physically motivated, just keeps charges from wandering off canvas
            if charge.x < CHARGE_RADIUS:
                charge.x = CHARGE_RADIUS
                charge.vx = abs(charge.vx)
            elif charge.x > width - CHARGE_RADIUS:
                charge.x = width - CHARGE_RADIUS
                charge.vx = -abs(charge.vx)

            if charge.y < CHARGE_RADIUS:
                charge.y = CHARGE_RADIUS
                charge.vy = abs(charge.vy)
            elif charge.y > height - CHARGE_RADIUS:
                charge.y = height - CHARGE_RADIUS
                charge.vy = -abs(charge.vy)

        self.update()

    def compute_induced_electric_field(self, x, y, bx_now, by_now, dt):
        # snap to a coarse grid so we're not tracking history per-pixel
        grid_key = (round(x / 5) * 5, round(y / 5) * 5)

        induced_ex = 0.0
        induced_ey = 0.0
        if grid_key in self.prev_b_field and dt > 0:
            prev_bx, prev_by = self.prev_b_field[grid_key]
            dbx_dt = (bx_now - prev_bx) / dt
            dby_dt = (by_now - prev_by) / dt
            # Faraday's law-ish: curl of E ~ -dB/dt. the 0.01 scale factor is basically eyeballed -
            # just enough to make the induced field visible without it drowning out the direct E field
            induced_ex = -dby_dt * 0.01
            induced_ey = dbx_dt * 0.01

        self.prev_b_field[grid_key] = (bx_now, by_now)
        return induced_ex, induced_ey

    def compute_field_at(self, x, y, exclude=None, dt=0.03):
        ex = ey = bx = by = 0.0

        for charge in self.charges:
            if exclude is not None and charge is exclude:
                continue

            dx = x - charge.x
            dy = y - charge.y
            r2 = dx * dx + dy * dy
            if r2 < 1.0:
                continue  # too close, field would blow up

            r = math.sqrt(r2)
            e_strength = K_COULOMB * charge.coulombs / r2
            ex += e_strength * dx / r
            ey += e_strength * dy / r

            charge_speed = math.hypot(charge.vx, charge.vy)
            if charge_speed > 0.0:
                v_cross_r = charge.vx * dy - charge.vy * dx
                b_strength = MU0_OVER_4PI * charge.coulombs * charge_speed / (r2 * r)
                sign = 1.0 if v_cross_r >= 0 else -1.0
                bx += sign * b_strength * (-dy)
                by += sign * b_strength * dx

        induced_ex, induced_ey = self.compute_induced_electric_field(x, y, bx, by, dt)
        ex += induced_ex
        ey += induced_ey
        return ex, ey, bx, by

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        self.draw_grid(painter)
        if self.show_electric or self.show_magnetic:
            self.draw_field_vectors(painter)
        self.draw_charges(painter)
        self.draw_info(painter)

    def draw_grid(self, painter):
        painter.setPen(QColor(50, 50, 50))
        step = 30
        w, h = self.width(), self.height()
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    def draw_field_vectors(self, painter):
        step = 24
        arrow_length = 24
        for y in range(step // 2, self.height(), step):
            for x in range(step // 2, self.width(), step):
                ex, ey, bx, by = self.compute_field_at(x, y)
                if self.show_electric:
                    self.draw_vector(painter, x, y, ex, ey, arrow_length, QColor(80, 180, 255, 220))
                if self.show_magnetic:
                    # B is tiny (Tesla-scale) compared to E, so it needs a big multiplier just to show up.
                    # 8e5 was picked by trial and error until the arrows looked reasonable next to the E field ones
                    self.draw_vector(painter, x, y, bx * 8e5, by * 8e5, arrow_length, QColor(255, 70, 70, 255))

    def draw_vector(self, painter, x, y, vx, vy, length_constant, color):
        magnitude = math.hypot(vx, vy)
        if magnitude < 1e-6:
            return

        nx, ny = vx / magnitude, vy / magnitude
        scaled_length = min(length_constant * 1.8, max(6.0, length_constant * (0.35 + min(1.0, magnitude / 2e6))))
        dx = nx * scaled_length
        dy = ny * scaled_length

        # magnetic vectors (reddish) get a slightly thicker/brighter treatment than electric ones
        if color.red() > 200 and color.green() < 120:
            width = min(7, max(3, int(3 + magnitude * 0.00008)))
            alpha = min(255, max(180, int(180 + magnitude * 0.0008)))
        else:
            width = min(6, max(1, int(1 + magnitude * 0.00002)))
            alpha = min(220, max(90, int(90 + magnitude * 0.00025)))

        arrow_color = QColor(color)
        arrow_color.setAlpha(alpha)

        pen = QPen(arrow_color)
        pen.setWidth(width)
        painter.setPen(pen)
        painter.drawLine(int(x), int(y), int(x + dx), int(y + dy))
        self.draw_arrow_head(painter, x + dx, y + dy, dx, dy, arrow_color, width + 1)

    def draw_arrow_head(self, painter, x, y, dx, dy, color, pen_width=1):
        angle = math.atan2(dy, dx)
        size = 6
        p1 = QPoint(int(x - size * math.cos(angle - math.pi / 6)), int(y - size * math.sin(angle - math.pi / 6)))
        p2 = QPoint(int(x - size * math.cos(angle + math.pi / 6)), int(y - size * math.sin(angle + math.pi / 6)))
        pen = QPen(color)
        pen.setWidth(pen_width)
        painter.setPen(pen)
        painter.drawLine(QPoint(int(x), int(y)), p1)
        painter.drawLine(QPoint(int(x), int(y)), p2)

    def draw_charges(self, painter):
        # using q instead of charge here just because I was copy-pasting from a physics notes file, whatever
        for q in self.charges:
            color = QColor(255, 80, 80) if q.coulombs > 0 else QColor(120, 210, 255)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), 220))
            painter.drawEllipse(
                int(q.x - CHARGE_RADIUS), int(q.y - CHARGE_RADIUS),
                CHARGE_RADIUS * 2, CHARGE_RADIUS * 2,
            )
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(int(q.x - 5), int(q.y + 5), "+" if q.coulombs > 0 else "–")

    def draw_info(self, painter):
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, self.height() - 20, self.info_text)

    def place_charge(self, x, y, coulombs, speed):
        self.charges.append(Charge(x=x, y=y, coulombs=coulombs, speed=speed))
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electromagnetism Simulator")
        self.canvas = FieldCanvas(self)
        self.setCentralWidget(self.create_main_widget())
        self.create_menu()
        self.resize(1000, 650)

    def create_main_widget(self):
        main_widget = QWidget(self)
        layout = QHBoxLayout(main_widget)
        layout.addWidget(self.canvas, 2)
        layout.addWidget(self.create_control_panel(), 0)
        return main_widget

    def create_control_panel(self):
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        title = QLabel("Charge Controls")
        title_font = QFont("Arial", 14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addWidget(self.create_charge_group())
        layout.addWidget(self.create_visual_group())
        layout.addWidget(self.create_simulation_control_group())

        clear_button = QPushButton("Clear All Charges")
        clear_button.clicked.connect(self.canvas.clear_charges)
        layout.addWidget(clear_button)

        layout.addStretch(1)
        return panel

    def create_charge_group(self):
        group = QGroupBox("Charge Placement")
        vbox = QVBoxLayout(group)

        vbox.addWidget(QLabel("Charge value (C):"))
        self.charge_spin = QDoubleSpinBox()
        self.charge_spin.setRange(-50.0, 50.0)
        self.charge_spin.setSingleStep(0.5)
        self.charge_spin.setValue(5.0)
        self.charge_spin.valueChanged.connect(self.canvas.set_placement_charge)
        vbox.addWidget(self.charge_spin)

        vbox.addWidget(QLabel("Charge speed (m/s):"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(-300.0, 300.0)
        self.speed_spin.setSingleStep(10.0)
        self.speed_spin.setValue(150.0)
        self.speed_spin.valueChanged.connect(self.canvas.set_placement_speed)
        vbox.addWidget(self.speed_spin)

        instructions = QLabel(
            "Click inside the field canvas to place a charge. "
            "Blue arrows = electric field. Red arrows = magnetic field. "
            "Positive charges repel, negative attract."
        )
        instructions.setWordWrap(True)
        vbox.addWidget(instructions)
        return group

    def create_visual_group(self):
        group = QGroupBox("Field Visualization")
        vbox = QVBoxLayout(group)

        self.electric_checkbox = QCheckBox("Show electric field")
        self.electric_checkbox.setChecked(True)
        self.electric_checkbox.stateChanged.connect(self.update_electric_toggle)

        self.magnetic_checkbox = QCheckBox("Show magnetic field")
        self.magnetic_checkbox.setChecked(True)
        self.magnetic_checkbox.stateChanged.connect(self.update_magnetic_toggle)

        vbox.addWidget(self.electric_checkbox)
        vbox.addWidget(self.magnetic_checkbox)
        return group

    def update_electric_toggle(self, state):
        # Qt gives us an int state, 2 == checked
        self.canvas.toggle_electric(state == 2)

    def update_magnetic_toggle(self, state):
        self.canvas.toggle_magnetic(state == 2)

    def create_simulation_control_group(self):
        group = QGroupBox("Simulation Control")
        vbox = QVBoxLayout(group)

        self.time_button = QPushButton("Pause")
        self.time_button.setCheckable(True)
        self.time_button.setChecked(False)
        self.time_button.clicked.connect(self.toggle_simulation_time)
        vbox.addWidget(self.time_button)

        self.time_label = QLabel("Time: 0.00 s")
        time_font = QFont("Arial", 10)
        time_font.setBold(True)
        self.time_label.setFont(time_font)
        vbox.addWidget(self.time_label)

        self.time_display_timer = QTimer(self)
        self.time_display_timer.timeout.connect(self.update_time_display)
        self.time_display_timer.start(100)
        return group

    def toggle_simulation_time(self):
        is_paused = self.canvas.toggle_time()
        self.time_button.setText("Resume" if is_paused else "Pause")

    def update_time_display(self):
        self.time_label.setText(f"Time: {self.canvas.get_simulation_time():.2f} s")

    def create_menu(self):
        # NOTE: this duplicates some of what's already in the side panel (clear charges, field
        # toggles). Left both in - someone wanted menu/keyboard access too and it was easier to
        # just wire it up here than refactor the panel to be the single source of truth
        menu_bar = self.menuBar()

        charge_menu = menu_bar.addMenu("Charge")
        positive_action = QAction("Place + charge", self)
        positive_action.triggered.connect(lambda: self.charge_spin.setValue(abs(self.charge_spin.value()) or 5.0))
        charge_menu.addAction(positive_action)

        negative_action = QAction("Place - charge", self)
        negative_action.triggered.connect(lambda: self.charge_spin.setValue(-abs(self.charge_spin.value()) or -5.0))
        charge_menu.addAction(negative_action)
        charge_menu.addSeparator()

        clear_action = QAction("Clear charges", self)
        clear_action.triggered.connect(self.canvas.clear_charges)
        charge_menu.addAction(clear_action)

        view_menu = menu_bar.addMenu("View")
        toggle_electric = QAction("Toggle electric field", self)
        toggle_electric.setCheckable(True)
        toggle_electric.setChecked(True)
        toggle_electric.toggled.connect(self.electric_checkbox.setChecked)
        view_menu.addAction(toggle_electric)

        toggle_magnetic = QAction("Toggle magnetic field", self)
        toggle_magnetic.setCheckable(True)
        toggle_magnetic.setChecked(True)
        toggle_magnetic.toggled.connect(self.magnetic_checkbox.setChecked)
        view_menu.addAction(toggle_magnetic)

        sim_menu = menu_bar.addMenu("Simulation")
        reset_action = QAction("Reset charges", self)
        reset_action.triggered.connect(self.canvas.clear_charges)
        sim_menu.addAction(reset_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        QMessageBox.information(
            self,
            "About Electromagnetism Simulator",
            "Electromagnetism Simulator\n"
            "Place charges with adjustable coulombs and speed.\n"
            "Electric field = blue arrows, magnetic field = red arrows.\n"
            "A moving charge produces a magnetic field in the plane.\n"
            "(units are more 'looks right' than SI-accurate, fair warning)",
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # looks decent cross-platform, native style was pretty ugly on my linux box
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
