from enum import Enum


class State(Enum):
    KICKOFF         = "kickoff"
    FAST_KICKOFF    = "fast_kickoff"
    RECOVER         = "recover"
    CLEAR           = "clear"
    SHOOT           = "shoot"
