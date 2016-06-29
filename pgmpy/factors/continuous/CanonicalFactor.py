# -*- coding: utf-8 -*-

from __future__ import division

import six
import numpy as np
from scipy.stats import multivariate_normal

from pgmpy.factors import ContinuousFactor
from pgmpy.factors import JointGaussianDistribution

class CanonicalFactor(ContinuousFactor):
    u"""
    The intermediate factors in a Gaussian network can be described
    compactly using a simple parametric representation called the
    canonical form. This representation is closed under the basic
    operations used in inference: factor product, factor division,
    factor reduction, and marginalization. Thus, we define this
    CanonicalFactor class that allows the inference process to be
    performed on joint Gaussian networks.

    A canonical form C (X; K,h,g) is defined as

    C (X; K,h,g) = exp( ((-1/2) * X.T * K * X) + (h.T * X) + g)

    Reference
    ---------
    Probabilistic Graphical Models, Principles and Techniques,
    Daphne Koller and Nir Friedman, Section 14.2, Chapter 14.

    """
    def __init__(self, variables, K, h, g, pdf=None):
        """
        Parameters
        ----------
        Parameters
        ----------
        variables: list or array-like
        The variables for wich the distribution is defined.

        K: n x n, 2-d array-like

        h : n x 1, array-like

        g : int, float

        The terms K, h and g are defined parameters for canonical
        factors representation.

        pdf: function
        The probability density function of the distribution.

        Examples
        --------
        Examples
        --------
        >>> from pgmpy.factors import CanonicalFactor
        >>> phi = CanonicalFactor(['X', 'Y'], np.array([[1, -1], [-1, 1]]),
                                  np.array([[1], [-1]]), -3)
        >>> phi.variables
        ['X', 'Y']

        >>> phi.K
        array([[1, -1],
               [-1, 1]])

        >>> phi.h
        array([[1],
               [-1]])

        >>> phi.g
        -3

        """
        no_of_var = len(variables)

        if len(h) != no_of_var:
            raise ValueError("Length of h parameter vector must be equal to the"
                         "number of variables.")

        self.h = np.asarray(np.reshape(h, (no_of_var, 1)), dtype=float)
        self.g = g
        self.K = np.asarray(K, dtype=float)

        if self.K.shape != (no_of_var, no_of_var):
            raise ValueError("The K matrix should be a square matrix with order equal to"
                             "the number of variables. Got: {got_shape}, Expected: {exp_shape}".format
                             (got_shape=self.covariance.shape, exp_shape=(no_of_var, no_of_var)))

        super(CanonicalFactor, self).__init__(variables, pdf)

    def assignment(self, *args):
        if self.pdf is None:
            self.pdf = self.to_joint_gaussian().pdf
        return super(CanonicalFactor, self).assignment(*args)

    def copy(self):
        """
        Makes a copy of the factor.

        Returns
        -------
        CanonicalFactor object: Copy of the factor

        Examples
        --------
        >>> from pgmpy.factors import CanonicalFactor
        >>> phi = CanonicalFactor(['X', 'Y'], np.array([[1, -1], [-1, 1]]),
                                  np.array([[1], [-1]]), -3)
        >>> phi.variables
        ['X', 'Y']

        >>> phi.K
        array([[1, -1],
               [-1, 1]])

        >>> phi.h
        array([[1],
               [-1]])

        >>> phi.g
        -3

        >>> phi2 = phi.copy()

        >>> phi2.variables
        ['X', 'Y']

        >>> phi2.K
        array([[1, -1],
               [-1, 1]])

        >>> phi2.h
        array([[1],
               [-1]])

        >>> phi2.g
        -3

        """
        copy_factor = CanonicalFactor(self.scope(), self.K.copy(),
                                      self.h.copy(), self.g, self.pdf)
        if self.pdf is not None:
            copy_factor.pdf = self.pdf

        return copy_factor

    def to_joint_gaussian(self):
        """
        Return an equivalent Joint Gaussian Distribution.

        Examples
        --------

        >>> import numpy as np
        >>> from pgmpy.factors import CanonicalFactor
        >>> phi = CanonicalFactor(['x1', 'x2'], np.array([[3, -2], [-2, 4]]),
                                  np.array([[5], [-1]]), 1)
        >>> jgd = phi.to_joint_gaussian()
        >>> jgd.variables
        ['x1', 'x2']
        >>> jgd.covariance
        array([[ 0.5  ,  0.25 ],
               [ 0.25 ,  0.375]])
        >>> jgd.mean
        array([[ 2.25 ],
               [ 0.875]])

        """
        covariance = np.linalg.inv(self.K)
        mean = np.dot(covariance, self.h)

        return JointGaussianDistribution(self.scope(), mean, covariance)

    def reduce(self, values, inplace=True):
        """
        Reduces the distribution to the context of the given variable values.

        Let C(X,Y ; K, h, g) be some canonical form over X,Y where,

        k = [[K_XX, K_XY],        ;       h = [[h_X],
             [K_YX, K_YY]]                     [h_Y]]

        The formula for the obtained conditional distribution for setting
        Y = y is given by,

        .. math:: K' = K_{XX}
        .. math:: h' = h_X - K_{XX} * y
        .. math:: g' = {h^T}_Y * y + 0.5 * y^T * K_{YY} * y
        

        Parameters
        ----------
        values: list, array-like
            A list of tuples of the form (variable name, variable value).

        inplace: boolean
            If inplace=True it will modify the factor itself, else would return
            a new CaninicalFactor object.

        Returns
        -------
        CanonicalFactor or None:
                if inplace=True (default) returns None
                if inplace=False returns a new CanonicalFactor instance.

        Examples
        --------
        >>> from pgmpy.factors import CanonicalFactor
        >>> phi = CanonicalFactor(['X1', 'X2', 'X3'], 
                                  np.array([[1, -1, 0], [-1, 4, -2], [0, -2, 4]]),
                                  np.array([[1], [4], [-1]]), -2)
        >>> phi.variables
        ['X1', 'X2', 'X3']

        >>> phi.K
        array([[ 1., -1.],
                [-1.,  3.]])

        >>> phi.h
        array([[ 1. ],
                [ 3.5]])

        >>> phi.g
        -2

        >>> phi.reduce([('X3', 0.25)])

        >>> phi.variables
        ['X1', 'X2']

        >>> phi.K
        array([[ 1, -1],
                [-1,  4]])

        >>> phi.h
        array([[ 1. ],
                [ 4.5]])

        >>> phi.g
        array([[-2.375]])
        """
        if not isinstance(values, list):
            raise TypeError("values: Expected type list or array-like,\
                             got type {var_type}".format(var_type=type(values)))

        phi = self if inplace else self.copy()

        var_to_reduce = [var for var, value in values]

        # index_to_keep -> j vector
        index_to_keep = [self.variables.index(var) for var in self.variables
                         if var not in var_to_reduce]
        # index_to_reduce -> i vector
        index_to_reduce = [self.variables.index(var) for var in var_to_reduce]

        K_i_i = self.K[np.ix_(index_to_keep, index_to_keep)]
        K_i_j = self.K[np.ix_(index_to_keep, index_to_reduce)]
        K_j_j = self.K[np.ix_(index_to_reduce, index_to_reduce)]
        h_i = self.h[index_to_keep]
        h_j = self.h[index_to_reduce]

        # The values for the reduced variables.
        y = np.array([value for index,
                      value in sorted([(self.variables.index(var), value) for var,
                                        value in values])]).reshape(len(index_to_reduce), 1)

        phi.variables = [self.variables[index] for index in index_to_keep]
        phi.K = K_i_i
        phi.h = h_i - np.dot(K_i_j, y)
        phi.g = self.g + np.dot(h_j.T, y) - 0.5 * np.dot(np.dot(y.T, K_j_j), y)
        phi.pdf = None

        if not inplace:
            return phi
