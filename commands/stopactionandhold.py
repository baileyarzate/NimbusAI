async def stopactionandhover(drone):
    await drone.action.hold()
    print("-- Action Stopped, Hovering")
    return None