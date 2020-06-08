from dataclasses import dataclass
from math import erfc
from math import sqrt
from typing import Any

from scipy.special import gammaincc

from rngtest.stattests.common import TestResult
from rngtest.stattests.common import binary_stattest
from rngtest.stattests.common import chunks
from rngtest.stattests.common import elected

__all__ = ["runs", "longest_runs"]


@elected
@binary_stattest
def runs(series, candidate):
    """Actual number of runs is compared to expected result

    The number of runs (uninterrupted sequence of the same value) is found, and
    referenced to a hypothetically truly random RNG.

    Parameters
    ----------
    series : Series
        Output of the RNG being tested
    candidate : Value present in given series
        The value which is counted in each block

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value
    """
    n = len(series)

    counts = series.value_counts()

    ncandidates = counts[candidate]
    propcandidates = ncandidates / n

    nruns = sum(1 for _ in asruns(series))

    p = erfc(
        abs(nruns - (2 * ncandidates * (1 - propcandidates)))
        / (2 * sqrt(2 * n) * propcandidates * (1 - propcandidates))
    )

    return TestResult(statistic=nruns, p=p)


@elected
@binary_stattest
def longest_runs(series, candidate):
    # ----------------------
    # Finding test constants
    # ----------------------

    n = len(series)

    if n < 128:
        raise ValueError()
    elif n < 6272:
        blocksize = 8
        nblocks = 16
        freqbinranges = [1, 2, 3, 4]
    elif n < 750000:
        blocksize = 128
        nblocks = 49
        freqbinranges = [4, 5, 6, 7, 8, 9]
    else:
        blocksize = 10 ** 4
        nblocks = 75
        freqbinranges = [10, 11, 12, 13, 14, 15, 16]

    def freqbin(length):
        minrange = freqbinranges[0]
        midranges = freqbinranges[1:-1]
        maxrange = freqbinranges[-1]

        if length <= minrange:
            return 0

        elif minrange < length < maxrange:
            for i, binlength in enumerate(midranges, 1):
                if length == binlength:
                    return i

        elif length >= maxrange:
            maxbin = len(freqbinranges)
            return maxbin

    df = len(freqbinranges) - 1

    # TODO Work out a general solution (which is performative!)
    probabilities = {
        8: [0.2148, 0.3672, 0.2305, 0.1875],
        128: [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124],
        512: [0.1170, 0.2460, 0.2523, 0.1755, 0.1027, 0.1124],
        1000: [0.1307, 0.2437, 0.2452, 0.1714, 0.1002, 0.1088],
        10000: [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727],
    }
    try:
        maxlenprobabilities = probabilities[blocksize]
    except KeyError:
        raise NotImplementedError()

    # ----------
    # Test logic
    # ----------

    maxlengths = []
    for chunk in chunks(series, blocksize=blocksize):
        candidateruns = (run for run in asruns(chunk) if run.value == candidate)

        maxlen = 0
        for run in candidateruns:
            if run.length > maxlen:
                maxlen = run.length

        maxlengths.append(maxlen)

    freqbins = [0 for _ in freqbinranges]
    for length in maxlengths:
        freqbins[freqbin(length)] += 1

    partials = []
    for prob, bincount in zip(maxlenprobabilities, freqbins):
        partial = (bincount - nblocks * prob) ** 2 / (nblocks * prob)
        partials.append(partial)

    statistic = sum(partials)
    p = gammaincc(df / 2, statistic / 2)

    return TestResult(statistic=statistic, p=p)


@dataclass
class Run:
    value: Any
    length: int = 1


def asruns(series):
    first_value = series.iloc[0]
    current_run = Run(first_value, length=0)
    for _, value in series.iteritems():
        if value == current_run.value:
            current_run.length += 1
        else:
            yield current_run

            current_run = Run(value)
    else:
        yield current_run
