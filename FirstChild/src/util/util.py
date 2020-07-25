import rlbot.utils.structures.game_data_struct as rl
from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State
from util.packet import ParsedPacket, Physics
from util.vector import Vector
from util.orientation import Orientation
from util.ball_prediction_analysis import find_slice_at_time
from util.drive import steer_toward_target
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
import math
from drawing_agent import DrawingAgent

def get_angle(car_rotation, car_location, ball_location) -> float:
    orientation = Orientation(car_rotation)
    car_to_ball = Vector(ball_location) - car_location
    angle = orientation.forward.ang_to(car_to_ball)
    return angle

def get_post_collision_velocity(ball_physics: Physics, car_physics: Physics) -> Vector:
    return ball_physics.velocity + car_physics.velocity