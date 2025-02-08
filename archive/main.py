import json
import asyncio
import numpy as np
import cv2
from mavsdk import System
from google import genai
from commands.goto_location import *
from commands.takeoff import *
from commands.land import *
from commands.stopactionandhold import *
from helper.generateprompt import generateprompt
from helper.processplussign import preprocess_plus_signs
from helper.processminussign import preprocess_minus_signs
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
    async def monitor_and_control_drone(drone, stop_event: asyncio.Event):
        rtb_state_info = await retrieveinfo(drone)
        while True:
            # Retrieve telemetry data
            variable_state_info = await retrieveinfo(drone)
            formatted_telemetry = json.dumps(variable_state_info, indent=2)
            battery_level = variable_state_info.get("battery", {}).get("level", 100)
            if battery_level < 10:
                print("Battery is low. Landing the drone.")
                break

            # Get user input
            userinput = input("Enter command to control drone: ")
            if userinput.lower() == "exit":
                print("Exiting the command interface.")
                break  # Exit the loop and stop listening for commands
            #print(drone.telemetry.position())

            # Generate prompt for the LLM
            prompt = generateprompt(userinput, formatted_telemetry)

            # Attempt to get and process the LLM response
            llm_command_fail = True
            while llm_command_fail:
                try:
                    response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    llm_commands = response.text
                    llm_commands_clean = preprocess_plus_signs(llm_commands.strip('```json\n').strip('\n```'))
                    llm_commands_clean = preprocess_minus_signs(llm_commands_clean)
                    llm_commands_clean = json.loads(llm_commands_clean)
                    llm_command_fail = False
                except json.JSONDecodeError:
                    print("Error decoding JSON. Retrying...")
                    llm_commands_clean = {}

            # Execute the appropriate maneuver
            #if llm_commands_clean.get('maneuver') == "goto":
            #    await gotoLLA(drone, location=llm_commands_clean['target_location'], flytime=llm_commands_clean['flytime'])
            if llm_commands_clean['maneuver'] == "goto":
                # Run the goto task concurrently while monitoring input
                asyncio.create_task(gotoLLA(drone, location=llm_commands_clean['target_location'], flytime=llm_commands_clean['flytime']))
            elif llm_commands_clean.get('maneuver') == "takeoff":
                await takeoff(drone, altitude=llm_commands_clean['altitude'])
            elif llm_commands_clean.get('maneuver') == "land":
                await land(drone)
            elif llm_commands_clean.get('maneuver') == "stop":
                #stop returns the drone to it's most recent retrieved location
                #theres a better way to do this
                #FIXME
                stop_event.set() 
                variable_state_info = await retrieveinfo(drone)
                asyncio.create_task(gotoLLA(drone, location=[variable_state_info['latitude_deg'], variable_state_info['longitude_deg'], variable_state_info['abs_altitude_m'], variable_state_info["yaw_deg"]], flytime=0, maneuver="stop"))
            elif llm_commands_clean.get('maneuver') == "rtb":
                stop_event.set() 
                asyncio.create_task(gotoLLA(drone, location=[rtb_state_info['latitude_deg'], rtb_state_info['longitude_deg'], rtb_state_info['abs_altitude_m'], rtb_state_info["yaw_deg"]], flytime=999))
                asyncio.create_task(gotoLLA(drone, location=[rtb_state_info['latitude_deg'], rtb_state_info['longitude_deg'], 0, rtb_state_info["yaw_deg"]], flytime=999))
            elif llm_commands_clean.get('maneuver') == "hold":
                await stopactionandhover(drone)
            else:
                print("Unknown command or maneuver. Please try again.")
        return None
    stop_event = asyncio.Event()  # Event to manage stopping tasks
    await monitor_and_control_drone(drone, stop_event=stop_event)
    #executes the landing command, end of while loop
    print("-- Landing")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())