import math
import random


def rand_int(
        number: float,
        float_range: float = 0.1,
) -> int:
    low = number * (1 - float_range)
    high = number * (1 + float_range)

    low_bound = math.ceil(low)
    high_bound = math.floor(high)

    return random.randint(low_bound, high_bound)


if __name__ == '__main__':
    print(rand_int(10))
