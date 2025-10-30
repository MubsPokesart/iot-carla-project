import pytest

from api.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    rv = client.get('/api/health')
    assert rv.status_code == 200
    # Further checks on the response data can be added here

def test_run_smoke(client):
    """Test the smoke run endpoint."""
    rv = client.post('/api/run/smoke', json={
        "seed": 42,
        "map": "Town03",
        "fps": 20,
        "duration": 1
    })
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['status'] == 'started'
    assert 'run_id' in json_data
