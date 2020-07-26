import rlbot.utils.structures.game_data_struct as rl
from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State
from util.packet import ParsedPacket
from util.vector import Vector
from util.orientation import Orientation
from util.ball_prediction_analysis import find_slice_at_time
from util.drive import steer_toward_target
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice
import math
from typing import Callable
from rlbot.utils.logging_utils import log

def get_angle(car_rotation, car_location, ball_location) -> float:
    orientation = Orientation(car_rotation)
    car_to_ball = Vector(ball_location) - car_location
    angle = orientation.forward.ang_to(car_to_ball)
    return angle

__DISTANCE_THRESHOLD: float = 10
__COLLISSION_POINTS: float = 32

def __dist(space: (Vector, Vector)) -> float:
    return space[0].dist(space[1])

def __test_line(line: (Vector, Vector), test: Callable, num_points: int) -> bool:
    total_dist = __dist(line)
    dist = total_dist / num_points
    point = line[0]

    # Do a funky iterate to avoid a strange edge case
    tested = 0
    while (point.dist(line[0]) <= total_dist):
        result: bool = test(point)
        tested += 1
        if result:
            return True
        point = point + dist * (line[1] - line[0]).normalized()
    return False

def __get_corners(
    center: Vector,
    width: float,
    height: float,
    orientation: Orientation,
) -> [Vector]:
    up = orientation.up * 0.5 * height
    right = orientation.right * 0.5 * width

    return [
        center + up + right,
        center - up + right,
        center - up - right,
        center + up - right,
    ]

def get_corners(
    center: Vector,
    hitbox: rl.BoxShape,
    orientation: Orientation,
) -> [[Vector]]:
    forward_center: Vector = center + 0.5 * hitbox.length * orientation.forward
    backward_center: Vector = center - 0.5 * hitbox.length * orientation.forward

    return [
        __get_corners(forward_center, hitbox.width, hitbox.height, orientation),
        __get_corners(backward_center, hitbox.width, hitbox.height, orientation),
    ]


def __is_colliding(
    car_location: Vector,
    car_hitbox: rl.BoxShape, 
    orientation: Orientation,
    ball_location: Vector, 
    ball_hitbox: rl.SphereShape
) -> bool:
    front, back = get_corners(car_location, car_hitbox, orientation)
    radius = ball_hitbox.diameter / 2

    def test(point: Vector) -> bool:
        return point.dist(ball_location) <= (radius + __DISTANCE_THRESHOLD)

    # Check lines on each corner
    for i in [0, 1, 2, 3]:
        if __test_line((front[i], front[(i + 1) % 4]),  test, __COLLISSION_POINTS):
            return True
        if __test_line((back[i], back[(i + 1) % 4]),  test, __COLLISSION_POINTS):
            return True
        if __test_line((front[i], back[i]),  test, __COLLISSION_POINTS):
            return True
    return False



def __step(forward: bool, search_space: (Vector, Vector)) -> (Vector, Vector):
    dist = __dist(search_space)
    point: Vector = (search_space[1] - search_space[0]).normalized() * distance
    if forward:
        return (point, search_space[1])
    return (search_space[0], point)

def get_collission(
    car_location: Vector,
    car_orientation: Orientation,
    car_hitbox: rl.BoxShape, 
    ball_hitbox: rl.SphereShape, 
    ball_location: Vector
) -> Vector:
    search_space: (Vector, Vector) = (car_location, ball_location)
    dist = __dist(search_space)
    while (dist < __DISTANCE_THRESHOLD):
        forward = __is_colliding(car_location, car_hitbox, car_orientation, ball_location, ball_hitbox)
        search_space = __step(forward, search_space)
        dist = __dist(search_space)
