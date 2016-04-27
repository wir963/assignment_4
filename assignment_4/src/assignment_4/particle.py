from assignment_3.geometry import *
from math import pi
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def to_grid_helper(x,y,the_map):
  return to_grid(x, y, the_map.info.origin.position.x, the_map.info.origin.position.y, the_map.info.width,
                 the_map.info.height, the_map.info.resolution)

#-------------------------------------------------------------------------------
# Generates a random pose in the map (in real world coordinates)
def random_particle(the_map):

  min_x = the_map.info.origin.position.x
  min_y = the_map.info.origin.position.y
  max_x = min_x + (the_map.info.width*the_map.info.resolution)
  max_y = min_y + (the_map.info.height*the_map.info.resolution)
  max_theta = 2*pi

  x = random.uniform(min_x, max_x)
  y = random.uniform(min_y, max_y)
  theta = random.uniform(0, max_theta)

  (x_grid, y_grid) = to_grid_helper(x,y,the_map)
  index = to_index(x_grid, y_grid, the_map.info.width)

  if the_map.data[index] == 100:
    return random_particle(the_map)
  return (x, y, theta)

#-------------------------------------------------------------------------------
# Generates a new particle from an old one by adding noise to it
def new_particle(particle, spatial_var, angle_var, the_map):
  (x,y,theta) = particle
  new_x = random.gauss(x, spatial_var)
  new_y = random.gauss(y, spatial_var)

  # check to see if new_particle is still on the map
  grid_coordinates = to_grid_helper(new_x, new_y, the_map)
  if grid_coordinates is None:
    return new_particle(particle, spatial_var, angle_var, the_map)
  # check to see if new_particle would return an occupied grid
  (x_grid, y_grid) = grid_coordinates
  index = to_index(x_grid, y_grid, the_map.info.width)
  if the_map.data[index] == 100:
    return new_particle(particle, spatial_var, angle_var, the_map)

  min_angle = theta-angle_var
  max_angle = theta+angle_var
  new_angle = random.uniform(min_angle, max_angle)
  return (new_x, new_y, new_angle)
    
#-------------------------------------------------------------------------------
# Resamples the particles.
# NOTE: particle weights are not normalized i.e. it is not guaranteed that the 
# sum of all particle weights is 1.
# n_particles in the number of particles
# scores is a list of tuples of the form (score, (x,y,theta) )
def resample(particles_weighted, n_particles, the_map):
  total_score = 0
  particles = []
  # lets normalize data from (0,1)
  min_score = 1
  max_score = 0
  for (score, particle) in particles_weighted:
    max_score = max(max_score, score)
    min_score = min(min_score, score)
  # normalize scores
  #print "min_score is %f and max_score is %f" %(min_score, max_score)
  particles_normalized = []
  for (score, particle) in particles_weighted:
    # if score < max_score-.1:
    #   score = score/2
    norm_score = (score-min_score)/(max_score-min_score)
    # norm_score = math.pow(norm_score,2)
    total_score += norm_score
    particles_normalized.append((norm_score, particle))
    #print "norm score is %f" %(norm_score)
  gap = total_score/(n_particles+1)
  #print "gap is %f" %(gap)
  start = random.uniform(0,gap)
  current_score = start
  cumulative_score = 0
  current_particle = -1
  for i in range(0,n_particles):
    while cumulative_score < current_score:
      current_particle += 1
      (score, particle) = particles_normalized[current_particle]
      cumulative_score += score
    particle = new_particle(particle, 1-score, 1-score, the_map)
    particles.append(particle)
    current_score += gap
  assert len(particles) == n_particles
  return particles      

# ----------------------------------------------------------------------------
# Draw an occupancy grid
def draw_occupancy_grid(the_map, ax):

  for cellId in range(len(the_map.data)):

    # Get cell grid coordinates
    x = cellId // the_map.info.width
    y = cellId %  the_map.info.width

    # Get cell world coordinates
    (x, y) = to_world ( x, y,
                    the_map.info.origin.position.x,
                    the_map.info.origin.position.y,
                    the_map.info.width, the_map.info.height,
                    the_map.info.resolution)


    # Add patch
    res = the_map.info.resolution
    if the_map.data[cellId] == 100:
      patch = patches.Rectangle ( (x-res/2, y-res/2), res, res, color='k', alpha=0.5)
      ax.add_patch(patch)
    elif the_map.data[cellId] == 0:
      patch = patches.Rectangle ( (x-res/2, y-res/2), res, res, color='b', alpha=0.5)
      ax.add_patch(patch)

  None

# ----------------------------------------------------------------------------
# Draw scored particles. If no scores were assigned to the particles (i.e. all
# particles have score 0) then particles are drawn with score of 0.1
def draw_particles_scored(particles_weighted):

  # Check if scores are unassigned
  scoresAssigned = False
  for particle in particles_weighted:
    if particle[0] != 0.0:
      scoresAssigned  = True

  # Draw particles
  for ptclId in range(len(particles_weighted)):
    (x, y, theta) = particles_weighted[ptclId][1]

    mSize = 0.1
    if scoresAssigned:
      mSize = particles_weighted[ptclId][0] * 20

    plt.plot( [x,  x - math.sin(theta)*0.5],
          [y,  y + math.cos(theta)*0.5],
          'g', linewidth=mSize / 5)
    plt.plot(x, y, 'ro', markersize=mSize, markeredgecolor='r')
  None

#-------------------------------------------------------------------------------
# This function is called each interation after calculating the scores of the
# particles. Use it for debugging
def debug_call(particles_weighted, the_map):

  debug = False

  if not debug:
    return 

  # Initialize figure
  my_dpi = 96
  plt.figure(1, figsize=(800/my_dpi, 800/my_dpi), dpi=my_dpi)
  plt.cla()
  plt.xlim ( the_map.info.origin.position.x, the_map.info.origin.position.x + the_map.info.width )
  plt.ylim ( the_map.info.origin.position.y, the_map.info.origin.position.y + the_map.info.height )
  plt.gca().set_aspect('equal', adjustable='box')
  plt.xlabel('X world')
  plt.xlabel('Y world')
  ax = plt.axes()

  # Draw map
  draw_occupancy_grid(the_map, ax)

  # Draw particles
  draw_particles_scored(particles_weighted)

  # Show plot
  plt.draw()

  pause = True
  if pause:
    k = plt.waitforbuttonpress(1)
    while not k:
      k = plt.waitforbuttonpress(1)
  else:
    plt.waitforbuttonpress(1e-6)

None  