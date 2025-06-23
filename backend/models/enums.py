from enum import Enum, unique


@unique
class Attitude(Enum):
    BAD = (-1.0, -0.7)
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
            if (value == lower and value != -1.0) or (value >= lower and value < upper):
                return label
            if value == 1.0:
                return cls.PERFECT

    @classmethod
    def from_label(cls, label: str):
        label_map = {
            "极差": cls.BAD,
            "不友善": cls.NEUTRAL_NEGATIVE,
            "中立": cls.NEUTRAL,
            "友善": cls.NEUTRAL_POSITIVE,
            "极好": cls.GOOD,
            "狂热": cls.PERFECT
        }

        normalized_label = label.strip().lower()
        for label_str, enum_value in label_map.items():
            if normalized_label == label_str.lower():
                return enum_value
        return None

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
    print(Attitude.from_label("很好"))
    print(Attitude.from_label("狂热"))
