from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from states.state import State
from util.packet import ParsedPacket


class RotateBack(State):

    def score(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    def get_output(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> SimpleControllerState:
        target_location = agent.field_info.my_goal.location
        return agent.move_towards_point(parsed_packet.my_car, target_location, True) 
