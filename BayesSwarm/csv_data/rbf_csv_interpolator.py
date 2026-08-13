import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RBFInterpolator

# --- CONFIGURATION ---
csv_filename = "20x20_position_3.csv"

# --- LOAD DATA FROM CSV ---
waypoints = []
source_x, source_y = None, None

with open(csv_filename, mode="r") as file:
    reader = csv.reader(file)
    rows = list(reader)

# Clean rows (remove empty lines)
rows = [r for r in rows if r and not r[0].startswith("#")]

# Parse Source Coordinate (Row index 1 based on your sample)
# Sample format: ource_x_coordinate,source_y_coordinate -> 0.883, 0.647
try:
    source_x = float(rows[1][0])
    source_y = float(rows[1][1])
except (IndexError, ValueError):
    pass

# Parse Waypoints (Starting from row index 3 based on your sample)
# Sample format: waypoint_number, x_coordinate, y_coordinate, signal_strength
for row in rows[3:]:
    try:
        # row[0] = waypoint_number, row[1] = x, row[2] = y, row[3] = signal
        x = float(row[1])
        y = float(row[2])
        signal = float(row[3])
        waypoints.append([x, y, signal])
    except (IndexError, ValueError):
        continue

# print(f"Debug - Loaded source: ({source_x}, {source_y})")
# print(f"Debug - Loaded waypoints count: {len(waypoints)}")

if len(waypoints) == 0:
    raise ValueError(
        "No waypoints were loaded! Please check the CSV file structure."
    )

waypoints = np.array(waypoints)
points = waypoints[:, 0:2]  # X and Y coordinates
values = waypoints[:, 2]  # Signal strengths

# --- RBF INTERPOLATION ---
rbf = RBFInterpolator(points, values, kernel="thin_plate_spline")

# Create a grid for smooth plotting
grid_x = np.linspace(
    points[:, 0].min() - 0.2, points[:, 0].max() + 0.2, 100
)
grid_y = np.linspace(
    points[:, 1].min() - 0.2, points[:, 1].max() + 0.2, 100
)
gx, gy = np.meshgrid(grid_x, grid_y)
grid_points = np.column_stack([gx.ravel(), gy.ravel()])
grid_z = rbf(grid_points).reshape(gx.shape)

# --- PLOTTING ---
plt.figure(figsize=(8, 6))

# Plot interpolated heatmap
contour = plt.contourf(gx, gy, grid_z, levels=50, cmap="viridis")
plt.colorbar(contour, label="Interpolated Signal Strength (dB)")

# Plot waypoints
if len(waypoints) < 110:
    plt.scatter(
        points[:, 0],
        points[:, 1],
        c=values,
        cmap="viridis",
        edgecolor="white",
        s=100,
        label="Waypoints",
    )

# Plot source coordinate (if available in CSV)
if source_x is not None and source_y is not None:
    plt.scatter(
        source_x,
        source_y,
        color="red",
        marker="*",
        s=200,
        label="Source",
        zorder=5,
    )

# Annotate waypoints dynamically
if len(waypoints) < 110:
    for i, (x, y, val) in enumerate(waypoints):
        plt.annotate(
            f"WP {i}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            color="white",
            fontsize=8,
        )

plt.title(f"RBF Interpolation - Dataset: {csv_filename}")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.legend(loc="upper left")
plt.grid(True, linestyle="--", alpha=0.3)
plt.show()
