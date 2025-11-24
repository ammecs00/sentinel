import pytest


def test_get_clients(client, auth_headers):
    """Test getting list of clients"""
    response = client.get("/api/v1/clients/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_clients_unauthorized(client):
    """Test getting clients without authentication"""
    response = client.get("/api/v1/clients/")
    assert response.status_code == 403


def test_get_client_stats(client, auth_headers):
    """Test getting client statistics"""
    response = client.get("/api/v1/clients/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_clients" in data
    assert "online_clients" in data