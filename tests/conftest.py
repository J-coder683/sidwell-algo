import pytest
from tests.fixture_company import FIXTURE_INPUTS

@pytest.fixture
def mock_financials():
    return FIXTURE_INPUTS.copy()
