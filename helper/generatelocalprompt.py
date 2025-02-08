def generatelocalprompt(user_command, telemetry_data):
    prompt = """
    You are an AI language model responsible for generating JSON output for drone maneuvers.

    Live Telemetry Data:
    //[Latitude, Longitude, Altitude] = [0.1, 111.1, 30]
    Here is the current telemetry data: {telemetry_data}  

    Instructions:

    Given the user command, generate ONLY the JSON representing the drone maneuver.  Do NOT include any explanations, calculations, reasoning, or any other text.  The JSON must be in the following format, and you must populate the `target_location` with the calculated values based on the rules below.  Any other text in your response will be considered an error.

    Calculation Rules:
    * North: Increase latitude. South: Decrease latitude.
    * East: Increase longitude. West: Decrease longitude.
    * Maintain altitude if not specified.
    * meters_per_second maximum is 100. 


    OUTPUT:
    json```
    {
        "target_location": [New_Latitude, New_Longitude, New_Altitude, New_Meters_per_Second]
    }
    ```
    Generate ONLY and EXACTLY the following JSON structure.  Do NOT include any other text.  The `target_location` array MUST contain EXACTLY four values. Any deviation from this structure will be considered an error.

    User Command: "Fly South Really Far and really slow." ## {user_command}
    """
    return prompt