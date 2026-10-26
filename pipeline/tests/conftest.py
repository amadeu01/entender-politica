import pytest

from compilador.catalog import Indicator
from tests.helpers import make_indicator


@pytest.fixture
def gini() -> Indicator:
    return make_indicator()
