from dataclasses import dataclass
from functools import wraps
from itertools import product
from math import exp
from math import floor
from math import sqrt
from typing import List
from warnings import warn

import pandas as pd
from scipy.special import gammaincc
from scipy.special import hyp1f1
from tabulate import tabulate

from rngtest.stattests._common import TestResult
from rngtest.stattests._common import rawblocks
from rngtest.stattests._common import stattest

__all__ = ["non_overlapping_template_matching", "overlapping_template_matching"]


# ------------------------------------------------------------------------------
# Template decorator for type checking and defaults


class TemplateContainsElementsNotInSequenceError(ValueError):
    pass


def template(func):
    @wraps(func)
    def wrapper(series: pd.Series, template=None, *args, **kwargs):
        if template is None:
            n = len(series)
            template_size = min(floor(sqrt(n)), 9)
            # TODO random template
            template_list = next(product(series.unique(), repeat=template_size))
            template = pd.Series(template_list)

        else:
            if not isinstance(template, pd.Series):
                template = pd.Series(template)

            for value in template.unique():
                if value not in series.unique():
                    raise TemplateContainsElementsNotInSequenceError()

        result = func(series, template, *args, **kwargs)

        return result

    return wrapper


# ------------------------------------------------------------------------------
# Non-overlapping Template Matching Test


@stattest(min_input=288)  # template_size=9, nblocks=8, blocksize=4*template_size
@template
def non_overlapping_template_matching(series, template, nblocks=8):
    """Matches of template per block is compared to expected result

    The sequence is split into blocks, where the number of non-overlapping
    matches to the template in each block is found. This is referenced to the
    expected mean and variance in matches of a hypothetically truly random RNG.

    Parameters
    ----------
    sequence : array-like
        Output of the RNG being tested
    template : array-like
        Template to match with the sequence
    nblocks : int
        Number of blocks to split sequence into

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value.

    Raises
    ------
    TemplateContainsElementsNotInSequenceError
        If template contains values not present in sequence
    """
    n = len(series)
    blocksize = n // nblocks
    template_size = len(template)

    recommendations = {
        "nblocks <= 100": nblocks <= 100,
        "blocksize > 0.01 * n": blocksize > 0.01 * n,
        "nblocks == n // blocksize": nblocks == n // blocksize,
    }
    for rec, success in recommendations.items():
        if success is False:
            warn(f"Input parameters fail recommendation {rec}", UserWarning)

    matches_expect = (blocksize - template_size + 1) / 2 ** template_size
    variance = blocksize * (
        (1 / 2 ** template_size) - ((2 * template_size - 1)) / 2 ** (2 * template_size)
    )

    template_tup = template.values

    block_matches = []
    for block_tup in rawblocks(series, blocksize=blocksize):
        matches = 0
        pointer = 0

        boundary = len(block_tup) - template_size
        while pointer < boundary:
            window = block_tup[pointer : pointer + template_size]

            if all(x == y for x, y in zip(window, template_tup)):
                matches += 1
                pointer += template_size
            else:
                pointer += 1

        block_matches.append(matches)

    match_diffs = [matches - matches_expect for matches in block_matches]

    statistic = sum(diff ** 2 / variance for diff in match_diffs)
    p = gammaincc(nblocks / 2, statistic / 2)

    return NonOverlappingTemplateMatchingTestResult(
        statistic=statistic,
        p=p,
        template=template,
        matches_expect=matches_expect,
        variance=variance,
        block_matches=block_matches,
        match_diffs=match_diffs,
    )


@dataclass
class NonOverlappingTemplateMatchingTestResult(TestResult):
    template: pd.Series
    matches_expect: float
    variance: float
    block_matches: List[int]
    match_diffs: List[float]

    def __str__(self):
        ftable = tabulate(
            {
                "block": [x for x in range(len(self.block_matches))],
                "matches": self.block_matches,
                "diff": [round(diff, 1) for diff in self.match_diffs],
            },
            headers="keys",
        )

        return (
            f"{self.p3f()}\n"
            "\n"
            f"template: {self.template.values}\n"
            f"expected matches per block: ~{round(self.matches_expect, 1)}\n"
            "\n"
            f"{ftable}"
        )


# ------------------------------------------------------------------------------
# Overlapping Template Matching Test


@stattest()
@template
def overlapping_template_matching(series, template, nblocks=8):
    """Overlapping matches of template per block is compared to expected result

    The sequence is split into blocks, where the number of overlapping matches
    to the template in each block is found. This is referenced to the expected
    mean and variance in matches of a hypothetically truly random RNG.

    Parameters
    ----------
    sequence : array-like
        Output of the RNG being tested
    template : array-like
        Template to match with the sequence
    nblocks : int
        Number of blocks to split sequence into

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value.

    Raises
    ------
    TemplateContainsElementsNotInSequenceError
        If template contains values not present in sequence
    """
    n = len(series)
    blocksize = n // nblocks

    template_size = len(template)
    template_tup = template.values

    block_matches = []
    for block_tup in rawblocks(series, blocksize=blocksize):
        matches = 0

        for pointer in range(blocksize):
            window = block_tup[pointer : pointer + template_size]

            if all(x == y for x, y in zip(window, template_tup)):
                matches += 1

        block_matches.append(matches)

    tallies = [0 for _ in range(6)]
    for matches in block_matches:
        i = min(matches, 5)
        tallies[i] += 1

    lambda_ = (blocksize - template_size + 1) / 2 ** template_size
    eta = lambda_ / 2

    probabilities = [
        ((eta * exp(-2 * eta)) / 2 ** x) * hyp1f1(x + 1, 2, eta)
        for x in range(len(tallies))
    ]

    statistic = sum(
        (tally - nblocks * probability) ** 2 / (nblocks * probability)
        for tally, probability in zip(tallies, probabilities)
    )

    df = len(tallies) - 1
    p = gammaincc(df / 2, statistic / 2)

    return TestResult(statistic=statistic, p=p)
