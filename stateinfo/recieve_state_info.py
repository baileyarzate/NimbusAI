import asyncio
from mavsdk import System

async def retrieveinfo(drone):
    telemetry = {}

    async for position in drone.telemetry.position():
        telemetry["latitude_deg"] = position.latitude_deg
        telemetry["longitude_deg"] = position.longitude_deg
        telemetry["abs_altitude_m"] = position.absolute_altitude_m 
        break

    async for velocity in drone.telemetry.velocity_ned():
        telemetry["velocity_north_m_s"] = velocity.north_m_s
        telemetry["velocity_east_m_s"] = velocity.east_m_s
        telemetry["velocity_down_m_s"] = velocity.down_m_s
        break

    async for attitude in drone.telemetry.attitude_euler():
        telemetry["roll_deg"] = attitude.roll_deg
        telemetry["pitch_deg"] = attitude.pitch_deg
        telemetry["yaw_deg"] = attitude.yaw_deg
        break

    async for battery in drone.telemetry.battery():
        telemetry["battery_rem_percent"] = battery.remaining_percent * 100
        break

    return telemetry
