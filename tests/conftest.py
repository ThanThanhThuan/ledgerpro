import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/testdb'


@pytest.fixture
def app():
    from api.index import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
