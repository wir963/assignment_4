from math import sin, cos, atan2, hypot, exp, floor
from assignment_3.geometry import to_index, to_world, to_grid
import math
import rospy
import sys

# ------------------------------------------------------------------------------
# Given two integer coordinates of two cells return a list of coordinates of
# cells that are traversed by the line segment between the centers of the input
# cells
def line_seg(x0, y0, x1, y1):
  points = []

  # Setup initial conditions
  dx = abs(x1 - x0)
  dy = abs(y1 - y0)
  x = x0
  y = y0
  n = 1 + dx + dy
  x_inc = 1 if x1 > x0 else -1
  y_inc = 1 if  y1 > y0  else -1
  error = dx - dy
  dx *= 2
  dy *= 2

  # Traverse
  while n > 0:
    points.append((x, y))

    if error >= 0:
      x += x_inc
      error -= dy
    else:
      y += y_inc
      error += dx

    n-=1

  # Return
  return points


def update_angle(old_angle, update_amt):
  new_angle = old_angle + update_amt
  while new_angle < 0:
    new_angle = 2*math.pi+new_angle
  while new_angle > 2*math.pi:
    new_angle = new_angle-2*math.pi
  return new_angle


def calc_x(x0, y0, y1, angle):
  delta_y = y1-y0
  if angle >=0 and angle < math.pi/2:
    theta = angle
    x1 = delta_y/math.tan(theta)
  elif angle < math.pi:
    theta = math.pi - angle
    tan = math.tan(theta)
    x1 = -1*delta_y/math.tan(theta)
  elif angle < 3*math.pi/2:
    theta = angle - math.pi
    x1 = delta_y/math.tan(theta)
  elif angle < 2*math.pi:
    theta = 2*math.pi - angle
    x1 = -1*delta_y/math.tan(theta)
  else:
    sys.exit(1)
  return math.floor(x1+x0)

def calc_y(x0, y0, x1, angle):
  delta_x = x1-x0
  if angle >= 0 and angle < math.pi/2:
    theta = angle
    y1 = delta_x*math.tan(theta)
  elif angle < math.pi:
    theta = math.pi - angle
    y1 = -1*delta_x*math.tan(theta)
  elif angle < 3*math.pi/2:
    theta = angle - math.pi
    y1 = delta_x*math.tan(theta)
  elif angle < 2*math.pi:
    theta = 2*math.pi - angle
    y1 = -1*delta_x*math.tan(theta)
  else:
    sys.exit(1)
  return math.floor(y1+y0)

#-------------------------------------------------------------------------------
# Given a ray find the coordinates of the first occupied cell in a ray
# Parameters:
#   x0, y0    map coordinates of a cell containing ray origin
#   angle     angle of a ray
#   the_map   map
# Return:
#    the last point in the map (in map coordinates)
def get_last_point(x0, y0, angle, width, height):
  max_x = width
  max_y = height
  min_x = 0
  min_y = 0
  angle = update_angle(angle, 0)
  if angle < math.pi:
    x1 = calc_x(x0, y0, max_y, angle)
    p1 = (x1, max_y)
  else:
    x1 = calc_x(x0, y0, min_y, angle)
    p1 = (x1, min_y)
  if angle > math.pi/2 and angle < 3*math.pi/2:
    y1 = calc_y(x0, y0, min_x, angle)
    p2 = (min_x, y1)
  else:
    y1 = calc_y(x0, y0, max_x, angle)
    p2 = (max_x, y1)
  (x1,y1) = p1
  (x2,y2) = p2
  if x1 > max_x or x1 < min_x:
    return p2
  return p1

#-------------------------------------------------------------------------------
# Given a ray find the coordinates of the first occupied cell in a ray
# Parameters:
#   x0, y0    map coordinates of a cell containing ray origin
#   angle     angle of a ray
#   the_map   map
# Return:
#    first occupied cell
def ray_tracing(x0, y0, angle, the_map):
  # find the integer coordinates of the last point in the map that this ray will trace
  # grid coordinates means they are indexes into the map
  # Given x0, y0, angle and map, return the last point
  (x1, y1) = get_last_point(x0, y0, angle, the_map.info.width, the_map.info.height)
  # rospy.loginfo("starting point is (%i, %i), angle is %f and end point is (%i, %i)" %(x0,y0,angle,x1,y1))
  points = line_seg(x0, y0, x1, y1)
  for point in points:
    (x,y) = point
    index = to_index(x, y, the_map.info.width)
    if the_map.data[index] == 100:
      return (x,y)
  return None

#-------------------------------------------------------------------------------
# Returns a laser scan that the robot would generate from a given pose in a map
# Parameters:
#   x0, y0      robot position in map coordinates
#   theta       robot orientation
#   min_angle   minimum angle of laserscan
#   increment   laserscan increment
#   n_readings  number of readings in a laserscan
#   max_range   maxiimum laser range
#   the_map     map
# Return:
#   array of expected ranges
def expected_scan(x, y, theta, min_angle, increment, n_readings, max_range, the_map):
  readings = []
  for i in range(0,n_readings):
    measurement_angle = theta + min_angle + i*increment
    # rospy.loginfo("measurement angle is %f" %(measurement_angle))
    end_point = ray_tracing(x, y, measurement_angle, the_map)
    if end_point is None:
      readings.append(max_range)
      continue
    (x1, y1) = end_point
    # rospy.loginfo("end point is (%i, %i)" %(x1, y1))
    delta_x = (x-x1)
    delta_y = (y-y1)
    distance = math.hypot(delta_x, delta_y)*the_map.info.resolution
    # rospy.loginfo("distance is %f" %(distance))
    if distance > max_range:
      readings.append(max_range)
      continue
    readings.append(distance)
  return readings

#-------------------------------------------------------------------------------
# Computes the similarity between two laserscan readings.
# Parameters:
#   ranges0     first scan
#   ranges1     second scan
#   max_range   maximum laser range
# Return:
#   similarity score between two scans
def scan_similarity(ranges0, ranges1, max_range):
  total_score = 0
  for i in range(0, len(ranges0)):
    distance0 = ranges0[i]
    distance1 = ranges1[i]
    #print "distance0 is %f, distance1 is %f and max_range is %f" %(distance0, distance1, max_range)
    difference = math.fabs(distance0-distance1)/max_range
    score = 1 - difference #max(distance0, distance1)
    score = math.pow(score, 2)
    # if score < .8:
    #   score = score/2
    if score > 1:
      sys.exit()
    #print "score is %f" %(relative_diff)
    total_score += score
  return total_score/len(ranges0)

