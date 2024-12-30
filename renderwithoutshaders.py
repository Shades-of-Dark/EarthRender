import random

import pygame
import math as m
import numpy as np
import time
import noise

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height), 0, 32)
pygame.display.set_caption("3D Planet Renderer")

# Colors
BLACK = (0, 0, 0)
PLANET_BASE_COLOR = (0, 255, 0)

PLANET_SIZE = 66
LIGHT_DIRECTION = pygame.math.Vector3(0, 0, 1)  # Direction of light (example: from top-right)
ROTATION_SPEED = 0.002

vectors = []
scaleFactor = 3
smallDisplay = pygame.Surface((width // scaleFactor, height // scaleFactor))

GUST = pygame.USEREVENT + 1
pygame.time.set_timer(GUST, 10000)
def generate_rotation_matrix(angle_x, angle_y, angle_z):
    rotation_x = [[1, 0, 0],
                  [0, m.cos(angle_x), -m.sin(angle_x)],
                  [0, m.sin(angle_x), m.cos(angle_x)]]

    rotation_y = [[m.cos(angle_y), 0, m.sin(angle_y)],
                  [0, 1, 0],
                  [-m.sin(angle_y), 0, m.cos(angle_y)]]

    rotation_z = [[m.cos(angle_z), -m.sin(angle_z), 0],
                  [m.sin(angle_z), m.cos(angle_z), 0],
                  [0, 0, 1]]

    return np.dot(rotation_x, np.dot(rotation_y, rotation_z))


# size = 2
# Generate two patterns with different scales


# Combine them
dither_texture = pygame.image.load("bayer_2x2.png").convert()


# pygame.image.save(dither_texture, f"bayer_{size}x{size}.png")

def convertLightToColorIndex(light_amount):
    index = int(round((light_amount - 0.1) * (4 / 0.8)))
    return index


def get_terrain_color(light_amount, terrain_value, pallette):
    index = convertLightToColorIndex(light_amount)

    if terrain_value < 0.15:  # water
        color = pallette.get_at((index, 2))
    elif 0.2 > terrain_value >= 0.15:  # lighter water
        color = pallette.get_at((index, 2))
    elif 0.24 > terrain_value >= 0.2:  # sand
        color = pallette.get_at((index, 1))
    else:
        color = pallette.get_at((index, 0))

    return color


# Planet properties
def draw_circle(display, radius, position, pallette, light_dir, rotationmatrix, noiseshiftx, noiseshifty, noiseshiftz,
                dithertexture):
    dither_size = dithertexture.get_width()
    cloud_radius = int(radius * 1.15)
    for x in range(-cloud_radius, cloud_radius, 1):
        for y in range(-cloud_radius, cloud_radius, 1):

            distance_squared = x * x + y * y
            inside_earth = distance_squared <= radius * radius
            inside_cloud_layer = distance_squared <= cloud_radius * cloud_radius
            if inside_earth or inside_cloud_layer:
                # Sample dither texture
                dither_x = int((x + position.x) % dither_size)
                dither_y = int((y + position.y) % dither_size)
                dither_value = dithertexture.get_at((dither_x, dither_y))[0] / 255.0
                normal = pygame.math.Vector3()

                normal.x = x / radius
                normal.y = y / radius

                centerPos = (int(position.x + x), int(position.y + y))
                # Apply rotation
                if inside_earth:
                    normal.z = m.sqrt(1 - (normal.x ** 2 + normal.y ** 2))
                    normal.normalize()

                    result = np.dot(rotationmatrix, normal)
                    normal = pygame.math.Vector3(result[0], result[1], result[2])

                    factor = normal.dot(light_dir)

                    # Adjust light intensity with dithering
                    light_intensity = min(1.0, max(0.0, factor + (dither_value - 0.5) * 0.1))

                    # Layer terrain
                    terrain_value = noise.pnoise3(normal.x, normal.y, normal.z) * 0.5
                    terrain_value += 0.25 * (
                            noise.pnoise3(normal.x * 4, normal.y * 4, normal.z * 4) + 1) / 2
                    terrain_value += 0.125 * (
                            noise.pnoise3(normal.x * 8, normal.y * 8, normal.z * 8) + 1) / 2
                    terrain_value += 0.125 * (noise.pnoise3(normal.x * 16, normal.y * 16,
                                                            normal.z * 16) + 1) / 2
                    color = get_terrain_color(light_intensity, terrain_value, pallette)

                    display.set_at((centerPos[0], centerPos[1]), color)

                # Inside the draw_circle function

                if inside_cloud_layer:
                    # Update normal calculation for clouds to reflect spherical geometry
                    normal = pygame.math.Vector3(x / cloud_radius, y / cloud_radius,
                                                 0)
                    z_component = 1.0 - (normal.x ** 2 + normal.y ** 2)
                    normal.z = m.sqrt(max(0.0, z_component))  # Clamp to prevent negative values

                    normal.normalize()


                    # Apply rotation matrix
                    result = np.dot(rotationmatrix, normal)
                    normal = pygame.math.Vector3(result[0], result[1], result[2])
                    normal.normalize()

                    # Lighting calculation (Ensure normal is facing the light direction correctly)
                    factor = normal.dot(light_dir)
                    light_intensity = max(0.0, min(1.0, factor + (dither_value - 0.5) * 0.1))

                    cloud_value = 0.0
                    # Base noise layer with lower frequency (large, smooth cloud patterns)
                    cloud_value += noise.pnoise3(normal.x + noiseshiftx, normal.y + noiseshifty,
                                                 normal.z + noiseshiftz) * 0.4
                    # Higher frequency noise layer (smaller, wispy details)
                    cloud_value += noise.pnoise3(normal.x * 2 + noiseshiftx, normal.y * 2 + noiseshifty,
                                                 normal.z * 2 + noiseshiftz) * 0.3
                    # Even higher frequency noise layer (fine details)
                    cloud_value += noise.pnoise3(normal.x * 4 + noiseshiftx, normal.y * 4 + noiseshifty,
                                                 normal.z * 4 + noiseshiftz) * 0.2
                    # Optional: add a very high frequency noise layer for additional fine texture
                    cloud_value += noise.pnoise3(normal.x * 8 + noiseshiftx, normal.y * 8 + noiseshifty,
                                                 normal.z * 8 + noiseshiftz) * 0.1

                    # Smooth the cloud value using a sigmoid or similar smooth function
                    cloud_value = (cloud_value + 1.0) / 2.0  # Normalize to [0, 1]
                    cloud_value = 1 / (1 + m.exp(-10 * (cloud_value - 0.5)))  # Sigmoid function for smooth transitions
                    cloud_threshold = 0.6

                    if cloud_value > cloud_threshold:
                        # Color adjustment based on light intensity
                        light_color = convertLightToColorIndex(light_intensity)
                        cloud_color = pallette.get_at((light_color, 3))

                        # Set the pixel color for clouds
                        display.set_at((int(centerPos[0]), int(centerPos[1])), tuple(cloud_color))

# Main game loop
clock = pygame.time.Clock()
angle = 0
running = True
last_time = time.time()

pos = pygame.math.Vector2(smallDisplay.get_width() // 2, smallDisplay.get_height() // 2)
rotx = 0

earthPallette = pygame.image.load("earth.png").convert()

angle_x, angle_y, angle_z = 0, 0, 0
cloudShiftx, cloudShifty, cloudShiftz = 0, 0, 0
# normal.z = m.sqrt(1 - (normal.x ** 2 + normal.y ** 2))
wind = random.randint(-1, 1)
while running:
    screen.fill(BLACK)
    smallDisplay.fill(BLACK)
    dt = time.time() - last_time
    dt *= 60
    last_time = time.time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == GUST:
            time_factor = pygame.time.get_ticks() / 1000.0  # Time in seconds
            wind = random.randint(-1, 1) * m.sin(time_factor * 2)

    LIGHT_DIRECTION = pygame.math.Vector3(m.sin(rotx), 0, m.cos(rotx)) # light vector
    LIGHT_DIRECTION.normalize()

    rotationMatrix = generate_rotation_matrix(angle_x, angle_y, angle_z) # rotation of earth
    angle_y += ROTATION_SPEED * dt

    rotx -= ROTATION_SPEED * dt # move the light source
    if rotx > 2 * m.pi:
        rotx -= 2 * m.pi * dt

    cloudShifty += 0.0008 * dt
    cloudShiftx += 0.0005 * dt
    cloudShiftz += 0.0002 * dt
    # Rotate and project points
    pygame.display.set_caption("3D Planet Renderer " + str(clock.get_fps()))
    draw_circle(smallDisplay, PLANET_SIZE, pos, earthPallette, LIGHT_DIRECTION, rotationMatrix, cloudShiftx,
                cloudShifty, cloudShiftz,
                dither_texture)
    screen.blit(pygame.transform.scale(smallDisplay, (width, height)), (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
