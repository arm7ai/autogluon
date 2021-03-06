import logging

from pandas import DataFrame, Series

from .abstract import AbstractFeatureGenerator
from ..feature_metadata import FeatureMetadata, R_INT
from ..types import get_type_map_real

logger = logging.getLogger(__name__)


# TODO: Add int fillna input value options: 0, set value, mean, mode, median
class AsTypeFeatureGenerator(AbstractFeatureGenerator):
    """
    Enforces type conversion on the data to match the types seen during fitting.
    If a feature cannot be converted to the correct type, an exception will be raised.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._feature_metadata_in_real: FeatureMetadata = None  # FeatureMetadata object based on the original input features real dtypes (will contain dtypes such as 'int16' and 'float32' instead of 'int' and 'float').
        # self.inplace = inplace  # TODO, also add check if dtypes are same as expected and skip .astype

    # TODO: consider returning self._transform(X) if we allow users to specify real dtypes as input
    def _fit_transform(self, X: DataFrame, **kwargs) -> (DataFrame, dict):
        return X, self.feature_metadata_in.type_group_map_special

    def _transform(self, X: DataFrame) -> DataFrame:
        int_features = self.feature_metadata_in.get_features(valid_raw_types=[R_INT])
        if int_features:
            null_count = X[int_features].isnull().sum()
            with_null = null_count[null_count != 0]
            # If int feature contains null during inference but not during fit.
            if len(with_null) > 0:
                # TODO: Consider imputing to mode? This is tricky because training data had no missing values.
                # TODO: Add unit test for this situation, to confirm it is handled properly.
                with_null_features = list(with_null.index)
                logger.warning(f'WARNING: Int features without null values at train time contain null values at inference time! Imputing nulls to 0. To avoid this, pass the features as floats during fit!')
                logger.warning(f'WARNING: Int features with nulls: {with_null_features}')
                X[with_null_features] = X[with_null_features].fillna(0)
        if self._feature_metadata_in_real.type_map_raw:
            # TODO: Confirm this works with sparse and other feature types!
            X = X.astype(self._feature_metadata_in_real.type_map_raw)
        return X

    @staticmethod
    def get_default_infer_features_in_args() -> dict:
        return dict()

    def _infer_features_in_full(self, X: DataFrame, feature_metadata_in: FeatureMetadata = None):
        super()._infer_features_in_full(X=X, feature_metadata_in=feature_metadata_in)
        type_map_real = get_type_map_real(X[self.feature_metadata_in.get_features()])
        self._feature_metadata_in_real = FeatureMetadata(type_map_raw=type_map_real, type_group_map_special=self.feature_metadata_in.get_type_group_map_raw())

    def _remove_features_in(self, features):
        super()._remove_features_in(features)
        if features:
            self._feature_metadata_in_real = self._feature_metadata_in_real.remove_features(features=features)

    def print_feature_metadata_info(self, log_level=20):
        self._log(log_level, '\tOriginal Features (exact raw dtype, raw dtype):')
        self._feature_metadata_in_real.print_feature_metadata_full(self.log_prefix + '\t\t', print_only_one_special=True, log_level=log_level)
        super().print_feature_metadata_info(log_level=log_level)
