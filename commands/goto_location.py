import asyncio
import time

async def gotoLLA(drone, location, flytime, maneuver='goto'):
    """
    Moves the drone towards the target location until it is reached, 
    or until the specified flytime has elapsed, then lands.
    """
    print("-- Moving")
    #await drone.action.goto_location(*location)  # Move to target location
    goto_task = asyncio.create_task(drone.action.goto_location(*location))

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
 
        # Calculate the distance to the target location
        lat_diff = abs(current_position.latitude_deg - target_lat)
        lon_diff = abs(current_position.longitude_deg - target_lon)
        alt_diff = abs(current_position.absolute_altitude_m - target_alt) #using absolute altitude instead of relative altitude
        # Check if the drone has reached the target location
        if lat_diff < 0.0001 and lon_diff < 0.0001 and alt_diff < 2.0:
            print("-- Target location reached.")
            break  # Exit the loop when the target is reached

        # Check if the flytime has elapsed
        elapsed_time = time.time() - start_time
        if elapsed_time >= flytime:
            print("-- Flytime exceeded.")
            break  # Exit the loop after flytime is exceeded
        if maneuver == 'stop':
            print("-- Manual stop.")
            break

        # Delay to prevent overloading the system with constant checks
        await asyncio.sleep(1)
    print("-- Action complete")
    await hover(drone)
    return None

async def hover(drone):
    # If your drone supports this command, you can use it
    await drone.action.hold()

