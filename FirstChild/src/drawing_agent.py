from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.vec import Vec3, polar_to_cartesian

from math import sin

from rlbot.utils.logging_utils import log

class DrawingAgent(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)

    def write_string_on_car(self, location, message, scale=1, color=None):
        """
        Writes a string at the provided location
        """
        # Add in a default color at runtime to avoid self reference issues
        color = color or self.renderer.cyan()

        # Get physics location for where to write messages
        car_location = Vec3(location)
        
        # Render information
        self.renderer.draw_string_3d(car_location, scale, scale, str(message), color)

    def draw_line_with_rect(self, start, end, size, color=None):
        """
        Draws a line from the start location to the end location with a rectangle at the end
        """
        color = color or self.renderer.cyan()
        self.renderer.draw_line_3d(start, end, color)
        self.renderer.draw_rect_3d(end, size, size, True, color, True)

    def draw_sphere(self, center: Vec3, radius, color=None, num_sides=12):
        # Draw vertical circles
        color = color or self.renderer.red()
        self.draw_circle(
            center, radius, color, vertical=True, horizontal_rotation=0, num_sides = num_sides
        )
        self.draw_circle(
            center, radius, color, vertical=True, horizontal_rotation=90, num_sides = num_sides
        )


    def draw_circle(self, center: Vec3, radius, color=None, vertical=True, horizontal_rotation: float = 0, num_sides=18):
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