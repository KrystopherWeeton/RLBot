import math
from typing import Union

from rlbot.utils.structures.game_data_struct import Vector3
from rlbot.utils.structures.struct import Struct
from rlbot.utils.logging_utils import log

class Vector:
    __slots__ = [
        'x',
        'y',
        'z'
    ]

    def __init__(self, x: Union[float, 'Vector', 'Vector3']=0, y: float=0, z: float=0):
        if hasattr(x, 'x'):
            # We have been given a vector. Copy it
            self.x = float(x.x)
            self.y = float(x.y) if hasattr(x, 'y') else 0
            self.z = float(x.z) if hasattr(x, 'z') else 0
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)

    def __getitem__(self, item: int):
        return (self.x, self.y, self.z)[item]

    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def __mul__(self, scale: float) -> 'Vector':
        return Vector(self.x * scale, self.y * scale, self.z * scale)

    def __rmul__(self, scale):
        return self * scale

    def __truediv__(self, scale: float) -> 'Vector':
        scale = 1 / float(scale)
        return self * scale

    def __str__(self):
        return f"<{self.x:.2f}, {self.y:.2f}, {self.z:.2f})>"

    def __repr__(self):
        return self.__str__()
    
    def flat(self):
        """Returns a new Vector that equals this Vector but projected onto the ground plane. I.e. where z=0."""
        return Vector(self.x, self.y, 0)

    def length(self):
        """Returns the length of the vector. Also called magnitude and norm."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def dist(self, other: 'Vector') -> float:
        """Returns the distance between this vector and another vector using pythagoras."""
        return (self - other).length()

    def normalized(self):
        """Returns a vector with the same direction but a length of one."""
        return self / self.length()

    def rescale(self, new_len: float) -> 'Vector':
        """Returns a vector with the same direction but a different length."""
        return new_len * self.normalized()

    def dot(self, other: 'Vector') -> float:
        """Returns the dot product."""
        return self.x*other.x + self.y*other.y + self.z*other.z

    def cross(self, other: 'Vector') -> 'Vector':
        """Returns the cross product."""
        return Vector(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def ang_to(self, ideal: 'Vector') -> float:
        """Returns the angle to the ideal vector. Angle will be between 0 and pi."""
        cos_ang = self.dot(ideal) / (self.length() * ideal.length())
        return math.acos(cos_ang)


def vectorize(vec: Vector3):
    return Vector(vec.x, vec.y, vec.z)


def polar_to_cartesian(hor_degrees: float, vert_degrees: float, r: int) -> Vector:
    hor_angle = hor_degrees * math.pi/180
    vert_angle = vert_degrees * math.pi/180
    x = r * math.sin(vert_angle) * math.cos(hor_angle)
    y = r * math.sin(vert_angle) * math.sin(hor_angle)
    z = r * math.cos(vert_angle)
    return Vector(x, y, z)

def get_items(obj) -> list:
    try:
        return obj.items()
    except (AttributeError, TypeError):
        return None