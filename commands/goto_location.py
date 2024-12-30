import asyncio
import time

async def goto(drone, location, flytime):
    """
    Moves the drone towards the target location until it is reached, 
    or until the specified flytime has elapsed, then lands.
    """
    print("-- Moving")
    await drone.action.goto_location(*location)  # Move to target location

    # Store the start time of the flight
    start_time = time.time()

    target_lat, target_lon, target_alt = location[0], location[1], location[2]
    
    while True:
        # Get the current position
        current_position = None
        async for pos in drone.telemetry.position():
            current_position = pos
            break  # Exit after getting the latest position
        
        if current_position is None:
            print("Error: Unable to retrieve current position.")
            return

        # Check if the drone has reached the target location
        if (abs(current_position.latitude_deg - target_lat) < 0.00001 and
            abs(current_position.longitude_deg - target_lon) < 0.00001 and
            abs(current_position.relative_altitude_m - target_alt) < 0.5):
            print("-- Target location reached.")
            break  # Exit the loop when the target is reached

        # Check if the flytime has elapsed
        elapsed_time = time.time() - start_time
        if elapsed_time >= flytime:
            print("-- Flytime exceeded, landing.")
            break  # Exit the loop after flytime is exceeded

        # Delay to prevent overloading the system with constant checks
        await asyncio.sleep(1)
    return None