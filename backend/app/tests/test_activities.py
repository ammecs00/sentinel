import pytest
from datetime import datetime


def test_get_activities(client, auth_headers):
    """Test getting list of activities"""
    response = client.get("/api/v1/activities/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_activities_unauthorized(client):
    """Test getting activities without authentication"""
    response = client.get("/api/v1/activities/")
    assert response.status_code == 403


def test_get_activity_stats(client, auth_headers):
    """Test getting activity statistics"""
    response = client.get("/api/v1/activities/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_activities" in data
    assert "active_clients" in data