from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State

class RotateBack(State):

    def __init__(self):
        pass

    def score(self, my_car: PlayerInfo, my_physics: Physics, ball_physics: Physics, team: int, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    def get_output(self, my_car: PlayerInfo, my_physics: Physics, ball_physics: Physics, team: int, packet: GameTickPacket, agent: BaseAgent) -> SimpleControllerState:
        target_location = goal_center(team)
        return self.move_towards_point(my_car, target_location, True) 
