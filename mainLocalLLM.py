import socket
from langchain_ollama import OllamaEmbeddings, ChatOllama
import helper.processminussign as pms
import helper.processplussign as pps
import helper.generatelocalprompt as glp
import helper.jsontodict as jtd
import asyncio
import json 
import time
import re

class Altitude:
    def __init__(self, msl_m=0):
        self.msl_m = msl_m

class LL:
    def __init__(self, latitude=0, longitude=0, altitude=None):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude or Altitude()

class Waypoint:
    def __init__(self, ll=None):
        self.ll = ll or LL()

class CommandData:  # New class to hold both Waypoint and airspeed
    def __init__(self):
        self.waypoint = Waypoint()  # .waypoint attribute
        self.airspeed_mps = 0  # .airspeed_mps attribute

class AutonomyCommand:
    def __init__(self):
        self.waypoint_cmd = CommandData()  # waypoint_cmd is now a CommandData object
    
    def set_cmds(self, latitude, longitude, altitude, meters_per_second):
        self.waypoint_cmd.waypoint.ll.latitude = latitude
        self.waypoint_cmd.waypoint.ll.longitude = longitude
        self.waypoint_cmd.waypoint.ll.altitude.msl_m = altitude
        self.waypoint_cmd.airspeed_mps = meters_per_second

    def SerializeToString(self):
        str1 = "Latitude: " + str(self.waypoint_cmd.waypoint.ll.latitude) + "\n"
        str2 = "Longitude: " + str(self.waypoint_cmd.waypoint.ll.longitude) + "\n"
        str3 = "Altitude: " + str(self.waypoint_cmd.waypoint.ll.altitude.msl_m) + "\n"
        str4 = "Meters per Second: " + str(self.waypoint_cmd.airspeed_mps) + "\n"
        return str1 + str2 + str3 + str4

async def send_cmd_every_second(sock, reciever_address, autonomyCmd, serialized_data):
    while True:
        # Send the command every second
        sock.sendto(serialized_data, reciever_address)
        print("Resending command...")
        await asyncio.sleep(1)  # Non-blocking sleep for 1 second

async def run():
    #connect to the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    reciever_address = ('localhost', 5006)

    #load the language model
    try:
        llm
    except:
        llm = ChatOllama(model="codellama:7b", device="cuda")

    autonomyCmd = AutonomyCommand()
    last_command_time = time.time()

    while True:
        #generate the prompt
        #prompt = glp.generatelocalprompt("Fly South Really Far and really slow.")

        telemetry_data, sender_address = sock.recvfrom(1024)
        print(f"Received data from {sender_address}")
        print(telemetry_data)
        userinput = input("Enter command to control drone: ")
        if userinput.lower() == "exit":
            print("Exiting the command interface.")
            break  # Exit the loop and stop listening for commands

        # Generate prompt for the LLM
        prompt = glp.generatelocalprompt(userinput, telemetry_data)

        response = llm.invoke(prompt, telemetry_data).content
        python_dict = jtd.json_string_to_dict(response)
        if python_dict:
            # Access elements:
            target_location = python_dict["target_location"]
            latitude = target_location[0]
            longitude = target_location[1]
            altitude = target_location[2]
            meters_per_second = target_location[3]

            autonomyCmd.set_cmds(latitude, longitude, altitude, abs(meters_per_second))
            serialized_data = autonomyCmd.SerializeToString()
            print(serialized_data)
            sock.sendto(serialized_data, reciever_address)

            #ideally this should just keep sending the command until a new one is recieved, this is the heartbeat
            asyncio.create_task(send_cmd_every_second(sock, reciever_address, autonomyCmd, serialized_data))
    


if __name__ == "__main__":
    asyncio.run(run())