import pygame
import sys
import moderngl
from array import array
import os
from noise import pnoise3

def resource_path(relative):
	if hasattr(sys, "_MEIPASS"):
		absolute_path = os.path.join(sys._MEIPASS, relative)
	else:
		absolute_path = os.path.join(relative)
	return absolute_path

screen = pygame.display.set_mode((800, 600), flags=pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface((800, 600))
ctx = moderngl.create_context()

clock = pygame.time.Clock()

quad_buffer = ctx.buffer(data=array('f', [-1.0, 1.0, 0.0, 0.0,  # topleft
										1.0, 1.0, 1.0, 0.0, #topright
										-1.0, -1.0, 1.0, 1.0, # bottomleft
										1.0, -1.0, 1.0, 1.0])) # bottomright

random_noise = pnoise3(10 * 0.1, 10,0)

vert_shader_path = resource_path("vertshader.txt")
frag_shader_path = resource_path("fragshader.txt")
with open(vert_shader_path, "r") as f:
	vert_shader = f.read()

with open(frag_shader_path, "r") as f:
	frag_shader = f.read()

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, "2f 2f", "vert", "texcoord")])

def surf_to_texture(surf):
	tex = ctx.texture(surf.get_size(), 4)
	tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
	tex.swizzle = 'BGRA'
	tex.write(surf.get_view('1'))
	return tex

def buffer(vertices):
	if isinstance(vertices, pygame.Rect):
		win_w, win_h = 800, 600
		l, t, r, b = vertices
		r_w_w = 1 / win_w
		r_w_h = 1 / win_h
		no_t = (t * r_w_h) * -2 + 1
		no_b = ((t + b) * r_w_h) * -2 + 1
		no_l = (l * r_w_w) * 2 - 1
		no_r = ((r + l) * r_w_w) * 2 - 1

		buffer = [
					# position (x, y), uv coords (x, y)
					no_l, no_t, 0, 0,  # topleft
					no_r, no_t, 1, 0,  # topright
					no_l, no_b, 0, 1,  # bottomleft
					no_r, no_b, 1, 1,  # bottomright
				]
	else:
		buffer = vertices

	vbo = ctx.buffer(array('f', buffer))


WHITE = (255, 255, 255)
while True:

	display.fill((0,0,0))

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
	mx, my = pygame.mouse.get_pos()


	frame_tex = surf_to_texture(display)
	frame_tex.use(0)
	program['tex'] = 0
	render_object.render(mode=moderngl.TRIANGLE_STRIP)

	pygame.display.flip()

	frame_tex.release()

	clock.tick(60)
