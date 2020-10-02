import sts

from ._implementation import Implementation


def monobit(bits):
    return sts.frequency(bits)


def linear_complexity(bits, blocksize):
    return sts.linear_complexity(bits, blocksize)


def serial(bits, blocksize):
    return sts.serial(bits, blocksize)


def cusum(bits, reverse=False):
    return sts.cumulative_sums(bits, reverse=reverse)


testmap = {
    "monobit": Implementation(monobit),
    "linear_complexity": Implementation(linear_complexity),
    "serial": Implementation(serial),
    "cusum": Implementation(cusum),
}
