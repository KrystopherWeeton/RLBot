
from rlbot.utils.structures.game_data_struct import Physics, GameTickPacket, PlayerInfo
from rlbot.agents.base_agent import SimpleControllerState, BaseAgent
from util.packet import ParsedPacket

class State:

    def __init__(self):
        pass

    def score(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> float:
        return None

    def get_output(self, parsed_packet: ParsedPacket, packet: GameTickPacket, agent: BaseAgent) -> SimpleControllerState:
        return None



"""
    # Low priority
    FAST_KICKOFF    = "fast_kickoff"
    WAIT_FOR_TOUCH  = "wait_for_touch"      # Get in position to respond to a predicted touch from player
    AERIAL_SHOT     = "aerial_shot"         # Shoot at the opponents goal from the air
    GROUND_SHOT     = "ground_shot"         # Shoot at the opponents goal from the ground
    DRIBBLE         = "dribble"             # Dribble the ball towards the opponents goal
    FLICK           = "flick"               # Flick the ball forward
    BAIT            = "bait"                # Wait for opponent to jump in before we make a decision
    FAKE_CHALLENGE  = "fake_challenge"      # Get a little close and then back off
    HIT_BALL_AT     = "hit_ball_at"         # Center, clear, towards boost
    FIFTY           = "fifty"               # Fucking run at the ball and hope for the best
    WAVE_DASH       = "wave_dash"           # Wave dash
    GROUND_CLEAR    = "aerial_clear"        # Clear the ball to the opponents side, preferrably away from them
    SHADOW          = "shadow"              # Shadow the opponent to defend
    AERIAL_SAVE     = "aerial_save"         # Save a shot that is going through the air
    GET_BOOST       = "get_boost"           # Get a large pad of boost
    TOUCH_BALL      = "touch_ball"          # Reposition the ball (low level dribble)
    PHILIP_SHOT     = "philip_shot"         # Philip shot
    MUSTY_FLICK     = "musty_flick"         # Musty flick the ball
    PINCH           = "pinch"               # Pinch the ball
    FAKE            = "fake"                # Very small chance (1%) to randomly fake
    DEMO            = "demo"


class WhatIsGoingOn(Enum):
    OPPONNENT_HAS_POSSESION,
    HOW much boost do I have,
    How much boost does the opponent have   # we can perfectly track how much boost the opponent has.
"""