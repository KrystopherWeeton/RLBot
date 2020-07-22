import csv
import pymongo

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.logging_utils import log, log_warn

from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.sequence import Sequence, ControlStep
from util.vec import Vec3
from util.orientation import Orientation, relative_location

from drawing_agent import DrawingAgent

from state import State
from typing import Dict, Callable

class DecisionAgent(DrawingAgent):

    # The minimum y value that the ball should have for marking a goal
    GOAL_THRESHOLD = 5180

    # flip_physics database stuff
    current_flip_physics: dict = None
    min_dist: float = 30000
    prev_seq_done: bool = True

    # Strategy things
    state: State = State.KICKOFF        # Initial state is kickoff

    # Behavior toggles
    DRAW_BALL_PHYSICS: bool = False         # Draw some basics physics information on the ball
    WRITE_STATE: bool = True
    WRITE_FLIP_PHYSICS_TO_DB: bool = True   # Write flip physics info to database

    # Maps state to functions
    state_map: Dict[str, Callable] = {}

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.state_map = {
            State.KICKOFF:          self.kickoff,
            State.FAST_KICKOFF:     self.kickoff,
            State.RECOVER:          self.recover,
            State.CLEAR:            self.clear,
            State.SHOOT:            self.shoot
        }

    def goal_center(self, team: int) -> Vec3:
        x: float = 0
        y: float = self.GOAL_THRESHOLD if team == 1 else -self.GOAL_THRESHOLD
        z: float = 100
        return Vec3(x, y, z)

    def signed_dist_to_ball(self, car_location: Vec3, ball_location: Vec3, team) -> float:
        """
        Returns signed y distance from car to the ball.
        The sign represents the direction. E.g. a positive sign indicates towards opponents goal.
        """
        team_goal_y = self.goal_center(team).y
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
    
    def next_state(self, my_car, my_physics, ball_physics, packet: GameTickPacket) -> State:
        # Cast everything if necessary
        car_location = Vec3(my_physics.location)
        ball_location = Vec3(ball_physics.location)

        # Check if we are on the wrong side of the ball
        signed_dist = self.signed_dist_to_ball(car_location, ball_location, my_car.team)
        if (signed_dist < 0):
            return State.RECOVER

        return State.SHOOT  # For now all behavior is described in SHOOT, so
        # always return that as the state


    def kickoff(self, packet: GameTickPacket) -> SimpleControllerState:
        log_warn("I am in an invalid state with no defined behavior.", {})

        
    def recover(self, packet: GameTickPacket) -> SimpleControllerState:
        my_car = packet.game_cars[self.index]
        target_location = self.goal_center(my_car.team)
        return self.move_towards_point(my_car, target_location, True)

        
    def clear(self, packet: GameTickPacket) -> SimpleControllerState:
        log_warn("I am in an invalid state with no defined behavior.", {})


    def shoot(self, packet: GameTickPacket) -> SimpleControllerState:
         # Gather some information about our car and the ball
        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)
        car_velocity = Vec3(my_car.physics.velocity)
        ball_location = Vec3(packet.game_ball.physics.location)
        ball_velocity = Vec3(packet.game_ball.physics.velocity)
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vec3(x.physics.location), ball_prediction.slices))

        my_car_ori = Orientation(my_car.physics.rotation)
        car_to_ball = ball_location - car_location
        car_to_ball_angle = my_car_ori.forward.ang_to(car_to_ball)            
        flip_point = Vec3(find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + 1).physics.location)
        target_location = flip_point

        #self.draw_sphere(self.goal_center(my_car.team), 20, self.renderer.red())

        if car_location.dist(flip_point) < 1000:
            if self.WRITE_FLIP_PHYSICS_TO_DB == True:
                # record physics info at beginning of flip
                self.current_flip_physics = {}

                # TODO: add slices here

                
                self.current_flip_physics["car_ball_angle"] = car_to_ball_angle
                self.current_flip_physics["car_ball_dist"] = car_location.dist(ball_location)
                

                self.current_flip_physics["car_velo_x"] = car_velocity[0]
                self.current_flip_physics["car_velo_y"] = car_velocity[1]
                self.current_flip_physics["car_velo_z"] = car_velocity[2]
                self.current_flip_physics["car_velo_mag"] = car_velocity.length()

                self.current_flip_physics["car_loc_x"] = car_location[0]
                self.current_flip_physics["car_loc_y"] = car_location[1]
                self.current_flip_physics["car_loc_z"] = car_location[2]

                self.current_flip_physics["ball_velo_x"] = ball_velocity[0]
                self.current_flip_physics["ball_velo_y"] = ball_velocity[1]
                self.current_flip_physics["ball_velo_z"] = ball_velocity[2]
                self.current_flip_physics["ball_velo_mag"] = ball_velocity.length()

                self.current_flip_physics["ball_loc_x"] = ball_location[0]
                self.current_flip_physics["ball_loc_y"] = ball_location[1]
                self.current_flip_physics["ball_loc_z"] = ball_location[2]

                self.current_flip_physics["contact"] = False

            return self.begin_front_flip(packet)

        """
        if car_location.dist(ball_location) > 1500:
            # We're far away from the ball, let's try to lead it a little bit
            ball_prediction = self.get_ball_prediction_struct()  # This can predict bounces, etc
            ball_in_future = find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + 2)
            target_location = Vec3(ball_in_future.physics.location)
        else:
            target_location = ball_location
        """

        # Draw target to show where the bot is attempting to go
        self.draw_line_with_rect(car_location, target_location, 8, self.renderer.cyan())

        # Set the final controls based off of above decision making
        controls = SimpleControllerState()
        controls.steer = steer_toward_target(my_car, target_location)
        controls.throttle = 1.0

        # You can set more controls if you want, like controls.boost.
        return controls


    def display_on_car(self, my_physics, ball_physics, packet):
        """
        A function that should return what should be printed on the car.
        """
        state: str = f"{self.state}"
        return state[state.index(".") + 1:]
        #return f"{Vec3(my_physics.location).dist(Vec3(ball_physics.location)):0.2f}"


    def begin_front_flip(self, packet):
        # Send some quickchat just for fun
        self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Information_IGotIt)

        # Do a front flip. We will be committed to this for a few seconds and the bot will ignore other
        # logic during that time because we are setting the active_sequence.
        self.active_sequence = Sequence([
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=True)),
            ControlStep(duration=0.05, controls=SimpleControllerState(jump=False)),
            ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1)),
            ControlStep(duration=0.8, controls=SimpleControllerState()),
        ])

        # Return the controls associated with the beginning of the sequence so we can start right away.
        return self.active_sequence.tick(packet)
