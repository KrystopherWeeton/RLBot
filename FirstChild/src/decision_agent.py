import csv
import pymongo

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
import rlbot.utils.structures.game_data_struct as rl
from util.packet import ParsedPacket, FieldInfoPacket

from rlbot.utils.logging_utils import log, log_warn


from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.sequence import Sequence, ControlStep
from util.vector import Vector
from util.orientation import Orientation, relative_location

from drawing_agent import DrawingAgent

from states.state import State
from states.rotate_back import RotateBack
from states.kickoff import Kickoff
from states.aerial_clear import AerialClear
from states.shoot import Shoot
from states.get_down_wall import GetDownWall
from states.ground_save import GroundSave
from states.recover import Recover
class DecisionAgent(DrawingAgent):

    # flip_physics database stuff
    current_flip_physics: dict = None
    min_dist: float = 30000
    prev_seq_done: bool = True

    # Strategy things
    state: State = None

    # Behavior toggles
    DRAW_BALL_PHYSICS: bool = False         # Draw some basics physics information on the ball
    WRITE_STATE: bool = True
    WRITE_FLIP_PHYSICS_TO_DB: bool = False   # Write flip physics info to database

    # States
    ROTATE_BACK: State = RotateBack()
    KICKOFF: State = Kickoff()
    AERIAL_CLEAR: State = AerialClear()
    SHOOT: State = Shoot()
    GET_DOWN_WALL = GetDownWall()
    GROUND_SAVE = GroundSave()
    RECOVER = Recover()

    # fieldInfo
    field_info: FieldInfoPacket = None

    def __init__(self, name, team, index):
        super().__init__(name, team, index)



    def signed_dist_to_ball(self, car_location: Vector, ball_location: Vector, team) -> float:
        """
        Returns signed y distance from car to the ball.
        The sign represents the direction. E.g. a positive sign indicates towards opponents goal.
        """
        team_goal_y = self.field_info.my_goal.location.y
        car_dist = team_goal_y - car_location.y
        ball_dist = team_goal_y - ball_location.y
        return ball_dist - car_dist

    def move_towards_point(self, my_car, point, boost: bool) -> SimpleControllerState:
         # Set the final controls based off of above decision making
        controls = SimpleControllerState()
        controls.steer = steer_toward_target(my_car, point)
        controls.throttle = 1.0
        if boost:
            controls.boost = True
        return controls
   

    def sequence_hook(self, controls: SimpleControllerState) -> bool:
        """
        Placeholder for if we want to do something when a sequence is being run, e.g
        cancel the sequence or do something else.
        Return true to continue sequence, false to cancel
        """
        return True
      

    def next_state(self, parsed_packet: ParsedPacket, packet: rl.GameTickPacket) -> State:
        return self.SHOOT
        # Cast everything if necessary
        car_location = parsed_packet.my_car.physics.location
        ball_location = parsed_packet.ball.physics.location

        # Check if we are on the wrong side of the ball
        signed_dist = self.signed_dist_to_ball(car_location, ball_location, parsed_packet.my_car.team)
        if (signed_dist < 0):
            return self.RECOVER

        return self.SHOOT # For now all behavior is described in SHOOT, so
        # always return that as the state


    def display_on_car(self, parsed_packet, packet):
        """
        A function that should return what should be printed on the car.
        """
        return f"{self.state.__class__.__name__}"
        # return f"{my_physics.location.dist(ball_physics.location):0.2f}"


    def begin_front_flip(self, packet):
        self.active_sequence = Sequence([
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=True)),
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=False)),
            ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1)),
            ControlStep(duration=0.8, controls=SimpleControllerState()),
        ])

        # Return the controls associated with the beginning of the sequence so we can start right away.
        return self.active_sequence.tick(packet)
