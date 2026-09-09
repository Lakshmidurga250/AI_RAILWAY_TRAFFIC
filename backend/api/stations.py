"""Stations and Platform Management API Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from backend.services.network_service import NetworkService
from backend.schemas.network import StationSchema

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("", response_model=List[StationSchema])
def list_stations():
    return NetworkService.get_stations()

@router.get("/{station_id}", response_model=StationSchema)
def get_station(station_id: str):
    stations = NetworkService.get_stations()
    for s in stations:
        if s["id"] == station_id or s["code"] == station_id:
            return s
    raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
