from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.vector import Vector, polar_to_cartesian

from math import sin

from rlbot.utils.logging_utils import log

from util.packet import Physics
import rlbot.utils.structures.game_data_struct as rl

class LegendEntry:
    text: str = None
    color = None

    def __init__(self, text, color):
        self.text = text
        self.color = color

class DrawingAgent(BaseAgent):
    

    def __init__(self, name, team, index):
        super().__init__(name, team, index)

    def draw_physics_info(self, physics: Physics):
        location = physics.location
        velocity = physics.velocity * 100
        angular_velocity = physics.angular_velocity
        self.draw_line_with_rect(location, location + velocity, 8, self.renderer.green())
        self.draw_line_with_rect(location, location + angular_velocity, 8, self.renderer.blue())

    def draw_legend(self, entries: [LegendEntry]):
        offset = 600
        for entry in entries:
            self.renderer.draw_string_2d(10, offset, 1, 1, entry.text, entry.color)
            offset += 30

    def draw_polyline(self, vecs: [Vector], color):
        self.renderer.draw_polyline_3d(vecs, color)

    def write_string(self, location, message, scale=1, color=None):
        """
        Writes a string at the provided location
        """
        color = color or self.renderer.cyan()
        self.renderer.draw_string_3d(location, scale, scale, str(message), color)


    def draw_line_with_rect(self, start, end, size, color=None):
        """
        Draws a line from the start location to the end location with a rectangle at the end
        """
        color = color or self.renderer.cyan()
        self.renderer.draw_line_3d(start, end, color)
        self.renderer.draw_rect_3d(end, size, size, True, color, True)

    def draw_rects(self, rects: [Vector], color):
        for r in rects:
            self.renderer.draw_rect_3d(r, 10, 10, True, color, True)

    def draw_sphere(self, center: Vector, radius, color=None, num_sides=12):
        # Draw vertical circles
        color = color or self.renderer.red()
        self.draw_circle(
            center, radius, color, vertical=True, horizontal_rotation=0, num_sides = num_sides
        )
        self.draw_circle(
            center, radius, color, vertical=True, horizontal_rotation=90, num_sides = num_sides
        )


    def draw_circle(self, center: Vector, radius, color=None, vertical=True, horizontal_rotation: float = 0, num_sides=18):
        """
        Draws a circle at the specified location horizontally.
        """
        # Math shit which works
        color = color or self.renderer.white()
        angles = [ k * 360 / num_sides for k in range(num_sides) ]
        if (vertical):
            points = [ center + polar_to_cartesian(horizontal_rotation, angle, radius) for angle in angles ]
        else:
            points = [ center + polar_to_cartesian(angle, 90 - sin(radius / center.z), radius) for angle in angles ]
        i = 0
        while i < len(points) - 1:
            self.renderer.draw_line_3d(points[i], points[i + 1], color)
            i += 1
        self.renderer.draw_line_3d(points[len(points) - 1], points[0], color)