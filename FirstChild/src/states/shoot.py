from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State
from util.packet import ParsedPacket
from util.vector import Vector
from util.orientation import Orientation
from util.ball_prediction_analysis import find_slice_at_time
from util.drive import steer_toward_target
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from util.util import get_angle

import math

from drawing_agent import DrawingAgent

class Shoot(State):

    NO_BOOST_MAX_SPEED: float = 1410.0
    DELTA_T_THRESH: float = 0.1
    CONTACT_Z_THRESH: float = 120.0
    contactPoint: Vector = None
    DIST_THRESHOLD: float = 400
    POWERSLIDE_THRESHOLD: float = 0.5
    

    def get_time(self, time, slice: Slice):
        return slice.game_seconds - time
    
    def score(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    def get_candidates(self, slices: [Slice], car_physics: Physics, agent: DrawingAgent) -> [Slice]:
        candidates = []
        for i, elem in enumerate(slices):
            pos = elem.physics.location
            if(i == 0 or i == len(slices) - 1):
                continue
            #elif(pos.z <= slices[i - 1].physics.location.z and pos.z <= slices[i + 1].physics.location.z):
            elif(pos.z < self.CONTACT_Z_THRESH):
                candidates.append(elem)
        return candidates

    def score_candidate(self, init_time: float, candidate: Slice, car_physics: Physics, agent: DrawingAgent) -> float:
        """
        Scores a candidate.
        < 0 => not considered a valid candidate
        >= 0 => valid candidate. Higher the number the better.
        """
        # Calculate the time the ball and car will take to get
        # to get to the candidate point. Assume car is pointed
        # in the correct direction.
        ball_time = self.get_time(init_time, candidate)
        dist = car_physics.location.dist(Vector(candidate.physics.location))
        car_time = dist / car_physics.velocity.length()
        delta = car_time - ball_time # < 0 means ball will get there after player

        # Check if we are able to turn to hit the ball?
        angle = get_angle(car_physics.rotation, car_physics.location, Vector(candidate.physics.location))

        cost = angle / 10 if dist < self.DIST_THRESHOLD else 0

        # If the car will get there too early, or the delta is too large, bail
        if (delta < 0 or delta > self.DELTA_T_THRESH):
            return - abs(delta)

        # Adjust the score to account for turning radius
        return (self.DELTA_T_THRESH - delta) - cost

        # Calculate the time the car will take to get there

    """
    Scan for potential contact points and choose the closest feasible one
    """
    def chooseContactPoint(self, slices: [Slice], carPhysics, agent: DrawingAgent):
        candidates: [Slice] = self.get_candidates(slices, carPhysics, agent)

        # calculate estimated time to reach each candidate
        init_time = slices[0].game_seconds
        optimalPoint = None
        optimalScore = -1
        for i, cand in enumerate(candidates):
            score = self.score_candidate(init_time, cand, carPhysics, agent)
            if (score > optimalScore):
                optimalPoint = cand.physics.location
                optimalScore = score
            
        if(optimalPoint != None):
            self.contactPoint = Vector(optimalPoint)
            agent.draw_rects([optimalPoint], agent.renderer.blue())
            agent.write_string(optimalPoint, f"{self.DELTA_T_THRESH - optimalScore:.2f}", 1, agent.renderer.lime())
        else:
            self.contactPoint = None
            

    def get_output(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: DrawingAgent) -> SimpleControllerState:
         # Gather some information about our car and the ball
        my_car = parsed_packet.my_car
        car_location = my_car.physics.location
        car_velocity = my_car.physics.velocity
        ball_location = parsed_packet.ball.physics.location
        ball_velocity = parsed_packet.ball.physics.velocity
        ball_prediction = agent.get_ball_prediction_struct()
        slices = list(map(lambda x : Vector(x.physics.location), ball_prediction.slices))

        agent.draw_circle(parsed_packet.my_car.physics.location, 400, agent.renderer.white(), False, 0)

        

        my_car_ori = Orientation(my_car.physics.rotation)
        car_to_ball = ball_location - car_location
        car_to_ball_angle = my_car_ori.forward.ang_to(car_to_ball)

        self.chooseContactPoint(ball_prediction.slices, my_car.physics, agent)
        
        if(self.contactPoint == None):
            flip_point = Vector(find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + 1).physics.location)
        else:
            flip_point = self.contactPoint
        target_location = flip_point

        if not agent.prev_seq_done and agent.WRITE_FLIP_PHYSICS_TO_DB:
            agent.prev_seq_done = True
            agent.write_flip_physics(agent.current_flip_physics)

        if car_location.dist(flip_point) < 300 and self.contactPoint != None:
            if agent.WRITE_FLIP_PHYSICS_TO_DB == True:
                # record physics info at beginning of flip
                agent.current_flip_physics = {}

                # TODO: add slices here

                
                agent.current_flip_physics["car_ball_angle"] = car_to_ball_angle
                agent.current_flip_physics["car_ball_dist"] = car_location.dist(ball_location)
                

                agent.current_flip_physics["car_velo_x"] = car_velocity[0]
                agent.current_flip_physics["car_velo_y"] = car_velocity[1]
                agent.current_flip_physics["car_velo_z"] = car_velocity[2]
                agent.current_flip_physics["car_velo_mag"] = car_velocity.length()

                agent.current_flip_physics["car_loc_x"] = car_location[0]
                agent.current_flip_physics["car_loc_y"] = car_location[1]
                agent.current_flip_physics["car_loc_z"] = car_location[2]

                agent.current_flip_physics["ball_velo_x"] = ball_velocity[0]
                agent.current_flip_physics["ball_velo_y"] = ball_velocity[1]
                agent.current_flip_physics["ball_velo_z"] = ball_velocity[2]
                agent.current_flip_physics["ball_velo_mag"] = ball_velocity.length()
                
                agent.current_flip_physics["ball_loc_x"] = ball_location[0]
                agent.current_flip_physics["ball_loc_y"] = ball_location[1]
                agent.current_flip_physics["ball_loc_z"] = ball_location[2]

                agent.current_flip_physics["contact"] = False

            return agent.begin_front_flip(packet)

        # Draw target to show where the bot is attempting to go
        if (self.contactPoint == None):
            agent.draw_line_with_rect(car_location, target_location, 8, agent.renderer.cyan())

        angle = get_angle(parsed_packet.my_car.physics.rotation, parsed_packet.my_car.physics.location, parsed_packet.ball.physics.location)
        agent.write_string_2d(1000, 1000, f"{angle}")

        # Set the final controls based off of above decision making
        controls = SimpleControllerState()
        controls.steer = steer_toward_target(my_car, target_location)
        controls.throttle = 1.0

        if (angle < self.POWERSLIDE_THRESHOLD):
            controls.handbrake = True

        # You can set more controls if you want, like controls.boost.
        return controls