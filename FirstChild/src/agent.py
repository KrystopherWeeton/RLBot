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
from util.vector import Vector

from drawing_agent import DrawingAgent, LegendEntry

from decision_agent import DecisionAgent
from rlbot.utils.logging_utils import log, log_warn

import rlbot.utils.structures.game_data_struct as rl
from util.packet import ParsedPacket, Physics, parse_field_info

from util.vector import Vector
from util.packet import parse_packet, ParsedPacket, FieldInfoPacket

from states.state import State

class Agent(DecisionAgent):


    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.active_sequence: Sequence = None
        self.boost_pad_tracker = BoostPadTracker()
        self.init_db()
    
    
    def initialize_agent(self):
        # Set up information about the boost pads now that the game is active and the info is available
        self.boost_pad_tracker.initialize_boosts(self.get_field_info())
    

    def init_db(self):
        self.client = pymongo.MongoClient("mongodb+srv://first_child:steven111!@clusterbuster.kjog8.mongodb.net/RocketBot?retryWrites=true&w=majority")
        self.db = self.client.get_database("RocketBot")
        self.flip_physics = self.db.get_collection("flip_physics")
    

    def write_flip_physics(self, flip_physics):
        if flip_physics is None:
            log_warn("Attempt to write None to database. Nothing will be written.", {})
            return
        self.flip_physics.insert_one(flip_physics)


    def draw_state(self, parsed_packet: ParsedPacket, packet: rl.GameTickPacket):
        # Draw ball prediction line for where the ball is going to go
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vector(x.physics.location), ball_prediction.slices))
        self.renderer.draw_polyline_3d(slices[::10], self.renderer.white())

        # Write to the car the appropriate string
        self.write_string(parsed_packet.my_car.physics.location, self.display_on_car(parsed_packet, packet))

        # Determine whether or not the ball is going to go into the goal
        goal_overlap: Vector = self.get_goal_overlap()
        if goal_overlap is not None:        # The ball is going in
            self.draw_circle(goal_overlap, 100)

    def get_goal_overlap(self) -> Vector:
        ball_prediction = self.get_ball_prediction_struct()
        slices = list(map(lambda x : Vector(x.physics.location), ball_prediction.slices))
        threshold = self.field_info.my_goal.location.y
        for (index, loc) in enumerate(slices):
            if abs(loc.y) < threshold:
                continue
            if index < len(slices) - 1 and abs(slices[index + 1].y) < threshold:
                continue
            return loc


    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        # Parse the packet to gather relevant information
        parsed_packet = parse_packet(self.team, packet)
        my_car = parsed_packet.my_car
        ball = parsed_packet.ball
        self.field_info = parse_field_info(self.team, self.get_field_info())

        # Draw the ball if appropriate
        legend_entries: [LegendEntry] = []
        if self.WRITE_STATE:
            state: str = f"{self.state}"
            legend_entries += [
                LegendEntry(f"{self.state.__class__.__name__}", self.renderer.white()),
            ]

        if self.DRAW_BALL_PHYSICS:
            legend_entries += [
                LegendEntry("Velocity", self.renderer.green()),
                LegendEntry("Angular Velocity", self.renderer.blue()),
            ]
            self.draw_physics_info(ball_physics)
        
        self.draw_legend(legend_entries)

        # Draw the state / debug information
        self.draw_state(parsed_packet, packet)

        # Keep our boost pad info updated with which pads are currently active
        self.boost_pad_tracker.update_boost_status(packet)

        # For fernado, make the bot shit talk a little bit
        if (my_car.physics.location.dist(ball.physics.location)) < 165:
            self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Reactions_CloseOne)
            if self.current_flip_physics:
                self.current_flip_physics["contact"] = True

        # Check for current sequence and continue sequence if there is one
        if self.active_sequence and not self.active_sequence.done:
            controls = self.active_sequence.tick(packet)
            if controls is not None:
                self.prev_seq_done = False
                continue_sequence = self.sequence_hook(controls)
                if continue_sequence:
                    return controls

        # Determine game state (different from draw state)
        self.state = self.next_state(parsed_packet, packet)
        return self.state.get_output(parsed_packet, packet, self)