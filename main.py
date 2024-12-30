import json
import asyncio
from mavsdk import System
from google import genai
from commands.goto_location import *
from commands.takeoff import *
from commands.land import *
from helper.generateprompt import generateprompt
from helper.processplussign import preprocess_plus_signs
from stateinfo.recieve_state_info import retrieveinfo

#hiding api key here
import yaml
with open("api_key.yaml") as stream:
    try:
        api_key = yaml.safe_load(stream)['api_key']
    except yaml.YAMLError as exc:
        print(exc)

#replace with your own api key
client = genai.Client(api_key=api_key)

async def run():
    drone = System(mavsdk_server_address='localhost', port=50051)
    print("Connecting to MAVSDK server...")
    await drone.connect(system_address="udp://172.22.160.11:18570")

    #verify drone is connected
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    #verify drone global position estimate is okay
    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break
    #drone arm 
    print("-- Arming")
    await drone.action.arm()

    print("-- Taking off")
    await drone.action.set_takeoff_altitude(2.5)
    await drone.action.takeoff()

    await asyncio.sleep(2)  # Wait for the drone to stabilize in the air

    #while loop would start here
    variable_state_info = await retrieveinfo(drone)
    formatted_telemetry = json.dumps(variable_state_info, indent=2)
    print(variable_state_info)
    userinput = input("Enter command to control drone: ")
    prompt = generateprompt(userinput, formatted_telemetry)
    llm_command_fail = True
    while llm_command_fail:
        try:
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            llm_commands = response.text
            #print(llm_commands)
            llm_commands_clean = preprocess_plus_signs(llm_commands.strip('```json\n').strip('\n```'))
            llm_commands_clean = json.loads(llm_commands_clean)
            print(llm_commands_clean)
            llm_command_fail = False
        except json.JSONDecodeError:
            print("Error decoding JSON")
            print('Retrying...')
            llm_commands_clean = {}
        print(llm_commands_clean)

    if llm_commands_clean['maneuver'] == "goto":
        # Execute the command with the specified location and flytime
        await goto(drone, location=llm_commands_clean['target_location'], flytime=llm_commands_clean['flytime'])

    elif llm_commands_clean['maneuver'] == "takeoff":
        # Execute the command with the specified altitude
        await takeoff(drone, altitude=llm_commands_clean['altitude'])

    elif llm_commands_clean['maneuver'] == "land":
        await land(drone)


    #executes the landing command, end of while loop
    print("-- Landing")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())