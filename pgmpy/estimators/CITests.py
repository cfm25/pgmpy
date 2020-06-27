from warnings import warn

import numpy as np
import pandas as pd
from scipy import stats

from pgmpy.independencies import IndependenceAssertion


def independence_match(X, Y, Z, independencies, **kwargs):
    """
    Checks if `X _|_ Y | Z` is in `independencies`. This method is implemneted to
    have an uniform API when the independencies are provided instead of data.

    Parameters
    ----------
    X: str
        The first variable for testing the independence condition X _|_ Y | Z

    Y: str
        The second variable for testing the independence condition X _|_ Y | Z

    Z: list/array-like
        A list of conditional variable for testing the condition X _|_ Y | Z

    data: pandas.DataFrame The dataset in which to test the indepenedence condition.

    Returns
    -------
    p-value: float (Fixed to 0 since it is always confident)
    """
    return IndependenceAssertion(X, Y, Z) in independencies


def chi_square(X, Y, Z, data, boolean=True, **kwargs):
    """
    Chi-square conditional independence test.
    Tests the null hypothesis that X is independent from Y given Zs.

    This is done by comparing the observed frequencies with the expected
    frequencies if X,Y were conditionally independent, using a chisquare
    deviance statistic. The expected frequencies given independence are
    `P(X,Y,Zs) = P(X|Zs)*P(Y|Zs)*P(Zs)`. The latter term can be computed
    as `P(X,Zs)*P(Y,Zs)/P(Zs).

    Parameters
    ----------
    X: int, string, hashable object
        A variable name contained in the data set

    Y: int, string, hashable object
        A variable name contained in the data set, different from X

    Z: list (array-like)
        A list of variable names contained in the data set, different from X and Y.
        This is the separating set that (potentially) makes X and Y independent.
        Default: []

    data: pandas.DataFrame
        The dataset on which to test the independence condition.

    boolean: bool
        If boolean=True, an additional argument `significance_level` must
            be specified. If p_value of the test is greater than equal to
            `significance_level`, returns True. Otherwise returns False.
        If boolean=False, returns the chi2 and p_value of the test.

    Returns
    -------
    chi2: float
        The chi2 test statistic.

    p_value: float
        The p_value, i.e. the probability of observing the computed chi2
        statistic (or an even higher value), given the null hypothesis
        that X _|_ Y | Zs.

    sufficient_data: bool
        A flag that indicates if the sample size is considered sufficient.
        As in [4], require at least 5 samples per parameter (on average).
        That is, the size of the data set must be greater than
        `5 * (c(X) - 1) * (c(Y) - 1) * prod([c(Z) for Z in Zs])`
        (c() denotes the variable cardinality).



    References
    ----------
    [1] Koller & Friedman, Probabilistic Graphical Models - Principles and Techniques, 2009
    Section 18.2.2.3 (page 789)
    [2] Neapolitan, Learning Bayesian Networks, Section 10.3 (page 600ff)
        http://www.cs.technion.ac.il/~dang/books/Learning%20Bayesian%20Networks(Neapolitan,%20Richard).pdf
    [3] Chi-square test https://en.wikipedia.org/wiki/Pearson%27s_chi-squared_test#Test_of_independence
    [4] Tsamardinos et al., The max-min hill-climbing BN structure learning algorithm, 2005, Section 4

    Examples
    --------
    >>> import pandas as pd
    >>> import numpy as np
    >>> data = pd.DataFrame(np.random.randint(0, 2, size=(50000, 4)), columns=list('ABCD'))
    >>> data['E'] = data['A'] + data['B'] + data['C']
    >>> chi_square(X='A', Y='C', Z=[], data=data, boolean=True, significance_level=0.05)
    True
    >>> chi_square(X='A', Y='B', Z=['D'], data=data, boolean=True, significance_level=0.05)
    True
    >>> chi_square(X='A', Y='B', Z=['D', 'E'], data=data, boolean=True, significance_level=0.05)
    False
    """
    if isinstance(Z, (frozenset, list, set, tuple)):
        Z = list(Z)
    else:
        Z = [Z]

    if "state_names" in kwargs.keys():
        state_names = kwargs["state_names"]
    else:
        state_names = {
            var_name: data.loc[:, var_name].unique() for var_name in data.columns
        }
    num_params = (
        (len(state_names[X]) - 1)
        * (len(state_names[Y]) - 1)
        * np.prod([len(state_names[z]) for z in Z])
    )
    sufficient_data = len(data) >= num_params * 5

    if not sufficient_data:
        warn(
            f"Insufficient data for testing {X} _|_ {Y} | {Z}. At least {5*num_params} samples recommended, {len(data)} present."
        )

    # compute actual frequency/state_count table:
    # = P(X,Y,Zs)
    XYZ_state_counts = pd.crosstab(
        index=data[X], columns=[data[Y]] + [data[z] for z in Z]
    )
    # reindex to add missing rows & columns (if some values don't appear in data)
    row_index = state_names[X]
    column_index = pd.MultiIndex.from_product(
        [state_names[Y]] + [state_names[z] for z in Z], names=[Y] + Z
    )
    if not isinstance(XYZ_state_counts.columns, pd.MultiIndex):
        XYZ_state_counts.columns = pd.MultiIndex.from_arrays([XYZ_state_counts.columns])
    XYZ_state_counts = XYZ_state_counts.reindex(
        index=row_index, columns=column_index
    ).fillna(0)

    # compute the expected frequency/state_count table if X _|_ Y | Zs:
    # = P(X|Zs)*P(Y|Zs)*P(Zs) = P(X,Zs)*P(Y,Zs)/P(Zs)
    if Z:
        XZ_state_counts = XYZ_state_counts.sum(axis=1, level=Z)  # marginalize out Y
        YZ_state_counts = XYZ_state_counts.sum().unstack(Z)  # marginalize out X
    else:
        XZ_state_counts = XYZ_state_counts.sum(axis=1)
        YZ_state_counts = XYZ_state_counts.sum()
    Z_state_counts = YZ_state_counts.sum()  # marginalize out both

    XYZ_expected = pd.DataFrame(
        index=XYZ_state_counts.index, columns=XYZ_state_counts.columns
    )
    for X_val in XYZ_expected.index:
        if Z:
            for Y_val in XYZ_expected.columns.levels[0]:
                XYZ_expected.loc[X_val, Y_val] = (
                    XZ_state_counts.loc[X_val]
                    * YZ_state_counts.loc[Y_val]
                    / Z_state_counts
                ).values
        else:
            for Y_val in XYZ_expected.columns:
                XYZ_expected.loc[X_val, Y_val] = (
                    XZ_state_counts.loc[X_val]
                    * YZ_state_counts.loc[Y_val]
                    / float(Z_state_counts)
                )
    observed = XYZ_state_counts.values.flatten()
    expected = XYZ_expected.fillna(0).values.flatten()
    # remove elements where the expected value is 0;
    # this also corrects the degrees of freedom for chisquare
    observed, expected = zip(
        *((o, e) for o, e in zip(observed, expected) if not e == 0)
    )

    chi2, p_value = stats.chisquare(observed, expected)

    if boolean:
        if p_value >= kwargs["significance_level"]:
            return True
        else:
            return False
    else:
        return chi2, p_value


def pearsonr(X, Y, Z, data, boolean=True, **kwargs):
    r"""
    Computes Pearson correlation coefficient and p-value for testing non-correlation. Should be used
    only on continuous data. In case when :math:`Z != \null` uses linear regression and computes pearson
    coefficient on residuals.

    Parameters
    ----------
    X: str
        The first variable for testing the independence condition X _|_ Y | Z

    Y: str
        The second variable for testing the independence condition X _|_ Y | Z

    Z: list/array-like
        A list of conditional variable for testing the condition X _|_ Y | Z

    data: pandas.DataFrame
        The dataset in which to test the indepenedence condition.

    boolean: bool
        If boolean=True, an additional argument `significance_level` must
            be specified. If p_value of the test is greater than equal to
            `significance_level`, returns True. Otherwise returns False.
        If boolean=False, returns the pearson correlation coefficient and p_value
            of the test.

    Returns
    -------
    Pearson's correlation coefficient: float
    p-value: float

    References
    ----------
    [1] https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
    [2] https://en.wikipedia.org/wiki/Partial_correlation#Using_linear_regression
    """
    # Step 1: Test if the inputs are correct
    if not hasattr(Z, "__iter__"):
        raise ValueError(f"Variable Z. Expected type: iterable. Got type: {type(Z)}")
    else:
        Z = list(Z)

    if not isinstance(data, pd.DataFrame):
        raise ValueError(
            f"Variable data. Expected type: pandas.DataFrame. Got type: {type(data)}"
        )

    # Step 2: If Z is empty compute a non-conditional test.
    if len(Z) == 0:
        coef, p_value = stats.pearsonr(data.loc[:, X], data.loc[:, Y])

    # Step 3: If Z is non-empty, use linear regression to compute residuals and test independence on it.
    else:
        X_coef = np.linalg.lstsq(data.loc[:, Z], data.loc[:, X], rcond=None)[0]
        Y_coef = np.linalg.lstsq(data.loc[:, Z], data.loc[:, Y], rcond=None)[0]

        residual_X = data.loc[:, X] - data.loc[:, Z].dot(X_coef)
        residual_Y = data.loc[:, Y] - data.loc[:, Z].dot(Y_coef)
        coef, p_value = stats.pearsonr(residual_X, residual_Y)

    if boolean:
        if p_value >= kwargs["significance_level"]:
            return True
        else:
            return False
    else:
        return coef, p_value
