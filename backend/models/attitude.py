from enum import Enum, unique


@unique
class Attitude(Enum):
    BAD = (-1.0, -0.8)
    NEUTRAL_NEGATIVE = (-0.8, -0.3)
    NEUTRAL = (-0.3, 0.3)
    NEUTRAL_POSITIVE = (0.3, 0.7)
    GOOD = (0.7, 0.95)
    PERFECT = (0.95, 1.0)

    @classmethod
    def from_value(cls, value: float):
        if value > 1.0:
            value = 1.0
        elif value < -1.0:
            value = -1.0

        for label in cls:
            lower, upper = label.value
            if (value == lower and value != -1.0) or (lower <= value < upper):
                return label
            if value == 1.0:
                return cls.PERFECT

    @classmethod
    def parse(cls, attitude_input: str):
        if not attitude_input:
            return None
        attitude_input = attitude_input.strip()
        label_map = {
            "极差": cls.BAD,
            "不友善": cls.NEUTRAL_NEGATIVE,
            "中立": cls.NEUTRAL,
            "友善": cls.NEUTRAL_POSITIVE,
            "极好": cls.GOOD,
            "狂热": cls.PERFECT
        }
        if attitude_input in label_map:
            return label_map[attitude_input]
        if attitude_input.startswith("Attitude."):
            enum_name = attitude_input.split(".", 1)[-1]
            try:
                return cls[enum_name]
            except KeyError:
                pass
        try:
            return cls[attitude_input]
        except KeyError:
            pass
        normalized_output = attitude_input.lower()
        for label, enum_val in label_map.items():
            if normalized_output == label.lower():
                return enum_val
        return None

    @classmethod
    def create_dict(cls):
        return {
            cls.BAD: [],
            cls.NEUTRAL_NEGATIVE: [],
            cls.NEUTRAL: [],
            cls.NEUTRAL_POSITIVE: [],
            cls.GOOD: [],
            cls.PERFECT: []
        }

    def __str__(self):
        attitude_name_map = {
            self.BAD: "极差",
            self.NEUTRAL_NEGATIVE: "不友善",
            self.NEUTRAL: "中立",
            self.NEUTRAL_POSITIVE: "友善",
            self.GOOD: "极好",
            self.PERFECT: "狂热"
        }
        return attitude_name_map[self]


if __name__ == '__main__':
    print(Attitude.from_value(0.95))
    print(Attitude.BAD)
    print(str(Attitude.BAD) == "极差")
    print(Attitude.parse("很好"))
    print(Attitude.parse("狂热"))
    print(Attitude.create_dict())
