import csv
import pymongo

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.logging_utils import log

from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.sequence import Sequence, ControlStep
from util.vec import Vec3

from drawing_agent import DrawingAgent



class MyBot(DrawingAgent):

    current_flip_physics: dict = None
    min_dist: float = 30000

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.active_sequence: Sequence = None
        self.boost_pad_tracker = BoostPadTracker()
    
    def init_db(self):
        self.client = pymongo.MongoClient("mongodb+srv://first_child:steven111!@clusterbuster.kjog8.mongodb.net/RocketBot?retryWrites=true&w=majority")
        self.db = self.client.get_database("RocketBot")
        self.flip_physics = self.db.get_collection("flip_physics")

    def write_flip_physics(self, flip_physics):
        self.flip_physics.insert_one(flip_physics)


    def initialize_agent(self):
        # Set up information about the boost pads now that the game is active and the info is available
        self.boost_pad_tracker.initialize_boosts(self.get_field_info())

    def draw_state(self, my_car, car_location, car_velocity, ball_location, ball_velocity):


        # Draw ball prediction always
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vec3(x.physics.location), ball_prediction.slices))
        self.renderer.draw_polyline_3d(slices, self.renderer.white())

        # Write to the car the distance between the car and the ball
        self.write_string_on_car(car_location, f"{car_location.dist(ball_location):0.2f}")
    
    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        # Gather some information about our car and the ball
        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)
        car_velocity = Vec3(my_car.physics.velocity)
        ball_location = Vec3(packet.game_ball.physics.location)
        ball_velocity = Vec3(packet.game_ball.physics.velocity)
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vec3(x.physics.location), ball_prediction.slices))

        self.draw_state(my_car, car_location, car_velocity, ball_location, ball_velocity)

        # Keep our boost pad info updated with which pads are currently active
        self.boost_pad_tracker.update_boost_status(packet)

        if (car_location.dist(ball_location) < 155):
            self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Reactions_CloseOne)
            self.current_flip_physics["contact"] = True

        # This is good to keep at the beginning of get_output. It will allow you to continue
        # any sequences that you may have started during a previous call to get_output.
        if self.active_sequence and not self.active_sequence.done:
            controls = self.active_sequence.tick(packet)
            if controls is not None:
                return controls
        else:
            self.write_flip_physics(self.current_flip_physics)


        flip_point = Vec3(find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + 1).physics.location)
        self.renderer.draw_line_3d(ball_location, flip_point, self.renderer.green())

        target_location = flip_point

        #log(car_location.dist(ball_location))
        

        if car_location.dist(flip_point) < 1000:
            # record physics info at beginning of flip
            self.current_flip_physics = {}
            self.current_flip_physics["car_velo"] = car_velocity
            self.current_flip_physics["car_loc"] = car_location
            self.current_flip_physics["ball_velo"] = ball_velocity
            self.current_flip_physics["ball_loc"] = ball_location
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

        # Draw some things to help understand what the bot is thinking
        self.renderer.draw_line_3d(car_location, target_location, self.renderer.white())
        self.renderer.draw_rect_3d(target_location, 8, 8, True, self.renderer.cyan(), centered=True)
        """
        if 750 < car_velocity.length() < 800:
            # We'll do a front flip if the car is moving at a certain speed.
            return self.begin_front_flip(packet)
        """
        controls = SimpleControllerState()
        controls.steer = steer_toward_target(my_car, target_location)
        controls.throttle = 1.0
        # You can set more controls if you want, like controls.boost.

        return controls

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
