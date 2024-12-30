async def land(drone):
    await drone.action.land()
    print("-- Landing")
    return None