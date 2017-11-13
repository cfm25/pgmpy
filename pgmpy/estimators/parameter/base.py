from pgmpy.estimators import BaseEstimator


class ParameterEstimator(BaseEstimator):
    def __init__(self, model, data, **kwargs):
        """
        Base class for parameter estimators in pgmpy.

        Parameters
        ----------
        model: pgmpy.models.BayesianModel or pgmpy.models.MarkovModel or pgmpy.models.NoisyOrModel
            model for which parameter estimation is to be done

        data: pandas DataFrame object
            datafame object with column names identical to the variable names of the model.
            (If some values in the data are missing the data cells should be set to `numpy.NaN`.
            Note that pandas converts each column containing `numpy.NaN`s to dtype `float`.)

        state_names: dict (optional)
            A dict indicating, for each variable, the discrete set of states (or values)
            that the variable can take. If unspecified, the observed values in the data set
            are taken to be the only possible states.

        complete_samples_only: bool (optional, default `True`)
            Specifies how to deal with missing data, if present. If set to `True` all rows
            that contain `np.Nan` somewhere are ignored. If `False` then, for each variable,
            every row where neither the variable nor its parents are `np.NaN` is used.
            This sets the behavior of the `state_count`-method.
        """

        if not set(model.nodes()) <= set(data.columns.values):
            raise ValueError("variable names of the model must be identical to column names in data")
        self.model = model

        super(ParameterEstimator, self).__init__(data, **kwargs)

    def state_counts(self, variable, **kwargs):
        """
        Return counts how often each state of 'variable' occured in the data.
        If the variable has parents, counting is done conditionally
        for each state configuration of the parents.

        Parameters
        ----------
        variable: string
            Name of the variable for which the state count is to be done.

        complete_samples_only: bool
            Specifies how to deal with missing data, if present. If set to `True` all rows
            that contain `np.NaN` somewhere are ignored. If `False` then
            every row where neither the variable nor its parents are `np.NaN` is used.
            Desired default behavior can be passed to the class constructor.

        Returns
        -------
        state_counts: pandas.DataFrame
            Table with state counts for 'variable'

        Examples
        --------
        >>> import pandas as pd
        >>> from pgmpy.models import BayesianModel
        >>> from pgmpy.estimators import ParameterEstimator
        >>> model = BayesianModel([('A', 'C'), ('B', 'C')])
        >>> data = pd.DataFrame(data={'A': ['a1', 'a1', 'a2'],
                                      'B': ['b1', 'b2', 'b1'],
                                      'C': ['c1', 'c1', 'c2']})
        >>> estimator = ParameterEstimator(model, data)
        >>> estimator.state_counts('A')
            A
        a1  2
        a2  1
        >>> estimator.state_counts('C')
        A  a1      a2
        B  b1  b2  b1  b2
        C
        c1  1   1   0   0
        c2  0   0   1   0
        """

        parents = sorted(self.model.get_parents(variable))
        return super(ParameterEstimator, self).state_counts(variable, parents=parents, **kwargs)

    def get_parameters(self):
        pass

