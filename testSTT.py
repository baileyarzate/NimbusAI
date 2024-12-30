from RealtimeSTT import AudioToTextRecorder
import os
import json
import asyncio
import queue
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
import yaml
import threading
import time

#hiding api key here
import yaml
with open("api_key.yaml") as stream:
    try:
        api_key = yaml.safe_load(stream)['api_key']
    except yaml.YAMLError as exc:
        print(exc)

#replace with your own api key
client = genai.Client(api_key=api_key)

# Real-time STT setup
full_sentences = []
displayed_text = ""
user_input_queue = queue.Queue() # Initialize user input variable

def clear_console():
    os.system('clear' if os.name == 'posix' else 'cls')

# Track the last processed command
last_command = ""

def text_detected(text):
    """Handle text detected in real-time STT."""
    global displayed_text, last_command
    sentences_with_style = [
        f"{sentence} "
        for i, sentence in enumerate(full_sentences)
    ]
    new_text = "".join(sentences_with_style).strip() + " " + text if len(sentences_with_style) > 0 else text

    if new_text != displayed_text:
        displayed_text = new_text
        print(displayed_text, end="", flush=True)

    # Check if the current command is a duplicate
    if text.strip() != last_command:
        # Update user input queue and the last command
        user_input_queue.put(text.strip())
        last_command = text.strip()

def process_text(text):
    """Process and store completed sentences."""
    global full_sentences
    if text.strip() not in full_sentences:  # Avoid duplicate storage
        full_sentences.append(text)
    text_detected(text)

# Recorder configuration
recorder_config = {
    'spinner': False,
    'model': 'distil-large-v2',
    'language': 'en',
    'silero_sensitivity': 0.4,
    'webrtc_sensitivity': 2,
    'post_speech_silence_duration': 0.4,
    'min_length_of_recording': 0,
    'min_gap_between_recordings': 0,
    'enable_realtime_transcription': True,
    'realtime_processing_pause': 0.2,
    'realtime_model_type': 'distil-large-v2',
    'on_realtime_transcription_update': text_detected,
    'device': "cuda",
}

if __name__ == "__main__":
    def start_stt():
        global recorder
        recorder = AudioToTextRecorder(**recorder_config)
        #print("Transcription has begun...", end="", flush=True)
        while True: 
            recorder.text(process_text) 

    stt_thread = threading.Thread(target=start_stt)
    stt_thread.start()

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
            user_input = ""
            while True:
                # Retrieve telemetry data
                variable_state_info = await retrieveinfo(drone)
                formatted_telemetry = json.dumps(variable_state_info, indent=2)
                battery_level = variable_state_info.get("battery", {}).get("level", 100)
                if battery_level < 10:
                    print("Battery is low. Landing the drone.")
                    break

                try:
                    user_input = user_input_queue.get_nowait()
                except queue.Empty:
                    user_input = ""
                # Get user input
                #userinput = input("Enter command to control drone: ")
                if user_input:
                    if user_input.lower() == "exit":
                        print("Exiting the command interface.")
                        break
                    prompt = generateprompt(user_input, formatted_telemetry)
                else:
                    prompt = ""
                print(prompt)
                # Attempt to get and process the LLM response
                llm_command_fail = True
                while llm_command_fail:
                    try:
                        if prompt != "":
                            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                            llm_commands = response.text
                            llm_commands_clean = preprocess_plus_signs(llm_commands.strip('```json\n').strip('\n```'))
                            llm_commands_clean = preprocess_minus_signs(llm_commands_clean)
                            llm_commands_clean = json.loads(llm_commands_clean)
                            llm_command_fail = False
                        else:
                            llm_commands_clean = {}
                            llm_commands_clean['maneuver'] = "continue"
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
                elif llm_commands_clean['maneuver'] == "continue":
                    pass
                else:
                    print("Unknown command or maneuver. Please try again.")
                user_input = ""
                await asyncio.sleep(0.1) 
        stop_event = asyncio.Event()  # Event to manage stopping tasks
        await monitor_and_control_drone(drone, stop_event=stop_event)
        #executes the landing command, end of while loop
        print("-- Landing")
        await drone.action.land()
    asyncio.run(run())