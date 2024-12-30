#the purpose of this file is to take off the drone to a certain height
import asyncio
async def takeoff(drone, altitude = 2.5):
    async for position in drone.telemetry.altitude():
        if position.altitude_relative_m > 0.1:
            print("Drone is already in the air")
            break
        else:
            await drone.action.set_takeoff_altitude(altitude)
            await drone.action.takeoff()
            print(f"-- Taking off to {altitude} meters AGL")
            await asyncio.sleep(2)  # Wait for the drone to stabilize in the air