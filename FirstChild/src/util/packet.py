import rlbot.utils.structures.game_data_struct as rl
from rlbot.utils.logging_utils import log_warn, log
from util.vector import Vector, vectorize

class Physics:
    location: Vector = None
    rotation: rl.Rotator = None
    velocity: Vector = None
    angular_velocity: Vector = None

    def __init__(self, other: rl.Physics):
        self.location = vectorize(other.location)
        self.velocity = vectorize(other.velocity)
        self.angular_velocity = vectorize(other.angular_velocity)
        self.rotation = other.rotation
            
class Car:
    physics: Physics = None
    jumped: bool = None
    double_jumped: bool = None
    team: int = None
    boost: int = None
    hitbox: rl.BoxShape = None
    hitbox_offset: Vector = None

    def __init__(self, player_info: rl.PlayerInfo):
        self.physics = Physics(player_info.physics)
        self.jumped = player_info.jumped
        self.double_jumped = player_info.double_jumped
        self.team = player_info.team
        self.boost = player_info.team
        self.boost = player_info.boost
        self.hitbox = player_info.hitbox
        self.hitbox_offset = vectorize(player_info.hitbox_offset)

class Touch:
    player_name: str = None
    time_seconds: float = None
    hit_location: Vector = None
    hit_normal: Vector = None
    team: int = None
    player_index: int = None

    def __init__(self, other: rl.Touch):
        for (k, v) in other._fields_:
            setattr(self, k, vectorize(v) if isinstance(v, rl.Vector3) else v)

class BallInfo:
    physics: Physics = None
    latest_touch: Touch = None
    hitbox: rl.SphereShape = None

    def __init__(self, other: rl.BallInfo):
        self.physics = Physics(other.physics)
        self.latest_touch = Touch(other.latest_touch)
        self.hitbox = other.collision_shape.sphere


class ParsedPacket:
    my_car: Car = None
    opponent: Car = None
    ball: BallInfo = None
    game_info: rl.GameInfo = None
    my_team: rl.TeamInfo = None
    enemy_team: rl.TeamInfo = None

    def __init__(self, player_index: int, other: rl.GameTickPacket):
        self.my_car = Car(other.game_cars[player_index])
        self.opponent = Car(other.game_cars[1 - player_index])  # Steven trick
        self.ball = BallInfo(other.game_ball)
        self.game_info = other.game_info
        self.my_team = other.teams[player_index]
        self.enemy_team = other.teams[1 - player_index]

class GoalInfo:
    team_num: int = None
    location: Vector = None
    direction: Vector = None
    width: float = None
    height: float = None

    def __init__(self, other: rl.GoalInfo):
        self.location = Vector(other.location)
        self.team_num = other.team_num
        self.direction = Vector(other.direction)
        self.width = other.width
        self.height = other.height



class FieldInfoPacket:
    my_goal: GoalInfo = None
    opponent_goal: GoalInfo = None
    num_goals: int = None

    def __init__(self, my_team: int, other: rl.FieldInfoPacket):
        self.num_goals = other.num_goals
        goals = [GoalInfo(info) for info in other.goals]
        if goals[0].team_num == my_team:
            self.my_goal = goals[0]
            self.opponent_goal = goals[1]
        else:
            self.my_goal = goals[1]
            self.opponent_goal = goals[0]



def parse_packet(player_index, packet) -> ParsedPacket:
    return ParsedPacket(player_index, packet)

def parse_field_info(my_team, packet: rl.FieldInfoPacket) -> FieldInfoPacket:
    return FieldInfoPacket(my_team, packet)