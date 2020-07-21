from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from util.vec import Vec3

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


    def draw_circle(self, center: Vec3, radius, color=None, num_sides=4):
        color = color or self.renderer.orange()
        degrees = 360.0 / num_sides
        cur_degrees = 0

        init_point = center + 

        while cur_degrees < 360:

        # Handle last line. From previous point to initial point
