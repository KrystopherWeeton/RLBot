from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State

class AerialClear(State):

    def score(self, my_car: PlayerInfo, my_physics: Physics, ball_physics: Physics, team: int, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    def get_output(self, my_car: PlayerInfo, my_physics: Physics, ball_physics: Physics, team: int, packet: GameTickPacket, agent: BaseAgent) -> SimpleControllerState:
        return None