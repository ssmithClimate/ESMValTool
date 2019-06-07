"""Gradient Boosting Regression model (using :mod:`xgboost´)."""

import logging
import os

from xgboost import XGBRegressor

from esmvaltool.diag_scripts.mlr.models import MLRModel
from esmvaltool.diag_scripts.mlr.models.gbr import GBRModel

logger = logging.getLogger(os.path.basename(__file__))


@MLRModel.register_mlr_model('gbr_xgboost')
class XGBoostGBRModel(GBRModel):
    """Gradient Boosting Regression model (:mod:`xgboost` implementation).

    Note
    ----
    See :mod:`esmvaltool.diag_scripts.mlr.models`.

    """

    _CLF_TYPE = XGBRegressor

    def plot_prediction_error(self, filename=None):
        """Plot prediction error for training and (if possible) test data.

        Parameters
        ----------
        filename : str, optional (default: 'prediction_error')
            Name of the plot file.

        """
        clf = self._clf.steps[-1][1].regressor_
        evals_result = clf.evals_result()
        train_score = evals_result['validation_0']['rmse']
        test_score = None
        if 'test' in self.data:
            test_score = evals_result['validation_1']['rmse']
        self._plot_prediction_error(train_score, test_score, filename)

    def _update_fit_kwargs(self, fit_kwargs):
        """Add transformed training and test data as fit kwargs."""
        reduced_fit_kwargs = {}
        for (param_name, param_val) in fit_kwargs.items():
            reduced_fit_kwargs[param_name.replace(
                f'{self._clf.steps[-1][0]}__', '')] = param_val
        x_train = self.get_x_array('train')
        y_train = self.get_y_array('train')
        self._clf.fit_transformers_only(x_train, y_train, **reduced_fit_kwargs)
        self._clf.steps[-1][1].fit_transformer_only(y_train,
                                                    **reduced_fit_kwargs)

        # Transform input data
        x_train = self._clf.transform_only(x_train)
        y_train = self._clf.transform_target_only(y_train)
        eval_set = [(x_train, y_train)]
        if 'test' in self.data:
            x_test = self._clf.transform_only(self.get_x_array('test'))
            y_test = self._clf.transform_target_only(self.get_y_array('test'))
            eval_set.append((x_test, y_test))

        # Update kwargs
        fit_kwargs.update({
            f'{self._clf.steps[-1][0]}__regressor__eval_metric':
            'rmse',
            f'{self._clf.steps[-1][0]}__regressor__eval_set':
            eval_set,
        })
        logger.debug(
            "Updated keyword arguments of fit() function with training and "
            "(if possible) test datasets for evaluation of prediction error")
        return fit_kwargs