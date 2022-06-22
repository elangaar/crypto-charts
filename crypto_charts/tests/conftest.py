import json
import pytest

from crypto_charts.__init__ import create_app

@pytest.fixture()
def test_client():
    """Fixture create test client using Flask app."""
    app = create_app()
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client

@pytest.fixture
def mock_data():
    """Fixture return sample of data from exchange."""
    with open('tests/test_data.json') as f:
        return json.load(f)