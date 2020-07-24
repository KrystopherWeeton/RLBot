from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.utils.rendering.rendering_manager import RenderingManager
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State
from util.packet import ParsedPacket
from util.vector import Vector
from util.orientation import Orientation
from util.ball_prediction_analysis import find_slice_at_time
from util.drive import steer_toward_target

from agent import Agent

class Shoot(State):

    CONTACT_Z_THRESH: float = 100
    
    def score(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    """
    Scan for potential contact points and choose the closest feasible one
    """
    def chooseContactPoint(self, slices, carPhysics, agent: Agent):
        candidates = list(filter(lambda pos : pos.z < self.CONTACT_Z_THRESH, slices))
        #agent.dr

    def get_output(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> SimpleControllerState:
         # Gather some information about our car and the ball
        my_car = parsed_packet.my_car
        car_location = my_car.physics.location
        car_velocity = my_car.physics.velocity
        ball_location = parsed_packet.ball.physics.location
        ball_velocity = parsed_packet.ball.physics.velocity
        ball_prediction = agent.get_ball_prediction_struct()
        slices = list(map(lambda x : Vector(x.physics.location), ball_prediction.slices))

        my_car_ori = Orientation(my_car.physics.rotation)
        car_to_ball = ball_location - car_location
        car_to_ball_angle = my_car_ori.forward.ang_to(car_to_ball)
        flip_point = Vector(find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + 1).physics.location)
        target_location = flip_point

        if not agent.prev_seq_done and agent.WRITE_FLIP_PHYSICS_TO_DB:
            agent.prev_seq_done = True
            agent.write_flip_physics(agent.current_flip_physics)

        #self.draw_sphere(self.goal_center(my_car.team), 20, self.renderer.red())

        if car_location.dist(flip_point) < 1000:
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
        agent.draw_line_with_rect(car_location, target_location, 8, agent.renderer.cyan())

        # Set the final controls based off of above decision making
        controls = SimpleControllerState()
        controls.steer = steer_toward_target(my_car, target_location)
        controls.throttle = 1.0

        # You can set more controls if you want, like controls.boost.
        return controls