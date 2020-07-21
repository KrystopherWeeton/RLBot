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

from decision_agent import DecisionAgent
from rlbot.utils.logging_utils import log, log_warn
from rlbot.utils.structures.game_data_struct import Physics

class Agent(DecisionAgent):

    # The minimum y value that the ball should have for marking a goal
    GOAL_THRESHOLD = 5180

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.init_db()
    
    def init_db(self):
        self.client = pymongo.MongoClient("mongodb+srv://first_child:steven111!@clusterbuster.kjog8.mongodb.net/RocketBot?retryWrites=true&w=majority")
        self.db = self.client.get_database("RocketBot")
        self.flip_physics = self.db.get_collection("flip_physics")
    
    def write_flip_physics(self, flip_physics):
        if flip_physics is None:
            log_warn("Attempt to write None to database. Nothing will be written.", {})
            return
        self.flip_physics.insert_one(flip_physics)

    def parse_packet(self, packet: GameTickPacket):
        # Gather some information about our car and the ball
        my_car = packet.game_cars[self.index]
        my_physics = my_car.physics
        ball_physics = packet.game_ball.physics
        return (my_car, my_physics, ball_physics)

    def draw_state(self, my_physics, ball_physics, packet):
        # Draw ball prediction line for where the ball is going to go
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vec3(x.physics.location), ball_prediction.slices))
        self.renderer.draw_polyline_3d(slices, self.renderer.white())

        # Write to the car the appropriate string
        self.write_string(my_physics.location, self.display_on_car(my_physics, ball_physics, packet))

        # Determine whether or not the ball is going to go into the goal
        goal_overlap: Vec3 = self.get_goal_overlap()
        if goal_overlap is not None:        # The ball is going in
            self.draw_circle(goal_overlap, 100)
        else:
            self.renderer.draw_string_2d(1000, 1000, 1, 1, str(Vec3(ball_physics.location)), self.renderer.white())

    def get_goal_overlap(self) -> Vec3:
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vec3(x.physics.location), ball_prediction.slices))
        for (index, loc) in enumerate(slices):
            if abs(loc.y) < self.GOAL_THRESHOLD:
                continue

            if index < len(slices) - 1 and abs(slices[index + 1].y) < self.GOAL_THRESHOLD:
                continue

            return loc

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        # Parse the packet to gather relevant information
        my_car, my_physics, ball_physics = self.parse_packet(packet)
        # Draw the ball if appropriate
        if self.draw_ball_physics:
            self.draw_legend()
            self.draw_physics_info(ball_physics)
        # Draw the state / debug information
        self.draw_state(my_physics, ball_physics, packet)
        return self.determine_output(my_car, my_physics, ball_physics, packet)