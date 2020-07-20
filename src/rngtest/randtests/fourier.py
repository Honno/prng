from dataclasses import dataclass
from math import erfc
from math import log
from math import sqrt

import pandas as pd
from numpy.fft import fft as _fft

from rngtest.randtests._decorators import elected
from rngtest.randtests._decorators import randtest
from rngtest.randtests._exceptions import NonBinarySequenceError
from rngtest.randtests._result import TestResult
from rngtest.randtests._tabulate import tabulate

__all__ = ["discrete_fourier_transform", "fft"]


class NonBinaryTruncatedSequenceError(NonBinarySequenceError):
    """Error if truncated sequence does not contain only 2 distinct values"""

    def __str__(self):
        return (
            "When truncated into an even-length, sequence contains only 1 distinct value\n"
            "i.e. the sequence was originally binary, but now isn't"
        )


@randtest(rec_input=1000)
@elected
def discrete_fourier_transform(series, candidate):
    """Potency of periodic features in sequence is compared to expected result

    The binary values are treated as the peaks and troughs respectively of a
    signal, which is applied a Fourier transform so as to find constituent
    periodic features. The strength of these features is referenced to the
    expected potent periodic features present in a hypothetically truly random
    RNG.

    Parameters
    ----------
    sequence : array-like
        Output of the RNG being tested
    candidate : Value present in given sequence
        The value which is considered the peak in oscillations

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value

    Raises
    ------
    NonBinaryTruncatedSequenceError
        When odd-lengthed sequence is truncated there is only one distinct value
        present

    """
    n = len(series)

    if n % 2 != 0:
        series = series[:-1]
        if series.nunique() != 2:
            raise NonBinaryTruncatedSequenceError()

    threshold = sqrt(log(1 / 0.05) * n)
    nbelow_expected = 0.95 * n / 2

    peak = candidate
    trough = next(value for value in series.unique() if value != candidate)

    oscillations = series.map({peak: 1, trough: -1})
    fourier = fft(oscillations)

    half_fourier = fourier[: n // 2]
    peaks = half_fourier.abs()

    nbelow = sum(peaks < threshold)

    diff = nbelow - nbelow_expected
    normdiff = diff / sqrt((n * 0.95 * 0.05) / 4)

    p = erfc(abs(normdiff) / sqrt(2))

    return DiscreteFourierTransformTestResult(
        statistic=normdiff,
        p=p,
        nbelow_expected=nbelow_expected,
        nbelow=nbelow,
        diff=diff,
    )


def fft(array) -> pd.Series:
    """Performs fast fourier transform

    Parameters
    ----------
    array : array-like
        Input array

    Returns
    -------
    `Series`
        Fourier transformation of `array`

    See Also
    --------
    numpy.fft.fft : Method adapted to return a `Series` as opposed to an `ndarray`
    """
    fourier_ndarray = _fft(array)
    fourier_series = pd.Series(fourier_ndarray)

    return fourier_series


@dataclass
class DiscreteFourierTransformTestResult(TestResult):
    nbelow_expected: float
    nbelow: int
    diff: float

    def __post_init__(self):
        pass

    def __str__(self):
        f_stats = self.stats_table("normalised diff")

        f_table = tabulate(
            [
                ("actual", self.nbelow),
                ("expected", round(self.nbelow_expected, 1)),
                ("diff", round(self.diff, 1)),
            ],
            colalign=("left", "right"),
        )

        return f"{f_stats}\n" "\n" "npeaks above threshold\n" f"{f_table}"
