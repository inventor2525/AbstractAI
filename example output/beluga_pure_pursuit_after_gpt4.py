import math
import matplotlib.pyplot as plt
import numpy as np

# Define path points
points = [(0, 0), (10, 0), (10, 10), (0, 10)]

# Define vehicle parameters
lookahead_distance = 1  # Lookahead distance
path_width = 3  # Width of the path
vehicle_radius = 1  # Radius of the vehicle
max_speed = 10  # Maximum vehicle speed
max_steer_angle = math.pi / 4  # Maximum steering angle

# Initialize vehicle position, heading, and speed
x = 0
y = 0
heading = 0
speed = 0

# Initialize previous position and heading
prev_x = x
prev_y = y
prev_heading = heading

# Initialize path following error variables
path_follow_error_x = 0
path_follow_error_y = 0

# Initialize total path distance
total_distance = 0

# Initialize the path following flag
path_following = True

# Initialize the list to store the vehicle trajectory
trajectory = []

# Generate the path
path_x, path_y = [], []
for point in points:
  path_x.append(point[0])
  path_y.append(point[1])

while path_following:
  # Get the next point on the path
  next_x = path_x[int(path_follow_error_x / path_width)]
  next_y = path_y[int(path_follow_error_x / path_width)]

  # Calculate the lookahead point
  lookahead_x = next_x + lookahead_distance * math.cos(heading)
  lookahead_y = next_y + lookahead_distance * math.sin(heading)

  # Calculate the path following error
  path_follow_error_x = lookahead_x - x
  path_follow_error_y = lookahead_y - y
  path_follow_error_magnitude = math.sqrt(path_follow_error_x**2 + path_follow_error_y**2)

  # Calculate the desired speed
  desired_speed = min(path_follow_error_magnitude / lookahead_distance, max_speed)

  # Calculate the desired heading
  desired_heading = math.atan2(lookahead_y - y, lookahead_x - x)

  # Calculate the steering angle
  steer_angle = desired_heading - heading

  # Clamp the steering angle within the maximum limits
  if steer_angle > max_steer_angle:
      steer_angle = max_steer_angle
  elif steer_angle < -max_steer_angle:
      steer_angle = -max_steer_angle

  # Calculate the new vehicle position and heading
  x += desired_speed * math.cos(heading + steer_angle / 2)
  y += desired_speed * math.sin(heading + steer_angle / 2)
  heading += steer_angle

  # Update the total distance
  total_distance += desired_speed

  # Check if the vehicle has reached the end of the path
  if (path_follow_error_x == 0 and path_follow_error_y == 0) or x >= path_x[-1] and y >= path_y[-1]:
      path_following = False

  # Add the current vehicle position to the trajectory
  trajectory.append((x, y, heading, speed))

  # Update the previous position and heading for the next iteration
  prev_x = x
  prev_y = y
  prev_heading = heading

# Plot the path and vehicle trajectory
fig, ax = plt.subplots()
ax.plot(path_x, path_y, '--k', linewidth=2)
ax.plot([x[0] for x in trajectory], [x[2] for x in trajectory], linewidth=5)
ax.plot(x, y, 'ro', markersize=10)
ax.set_xlim(min(path_x) - 2, max(path_x) + 2)
ax.set_ylim(min(path_y) - 2, max(path_y) + 2)
ax.set_title('Pure Pursuit Algorithm')
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')

plt.show()