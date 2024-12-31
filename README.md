# Drone Command Interface with Natural Language Processing

This project enables commanding a drone using natural language. Leveraging MAVSDK for drone control and a Large Language Model (LLM) for natural language interpretation, it supports real-time decision-making and drone navigation.

## Features

- **Natural Language Commands**: Use plain English to command the drone to perform tasks such as takeoff, landing, navigation, and returning to the base.
- **Real-time Telemetry**: Integrates live drone telemetry for informed decision-making.
- **Customizable LLM Prompts**: Generates context-aware prompts for LLM interpretation.
- **Dynamic Maneuver Execution**: Executes commands like "goto", "land", "stop", and "rtb" (return to base).

## Technologies Used

- **MAVSDK**: For drone communication and control.
- **Google GenAI**: For natural language command processing.
- **Asyncio**: To handle concurrent tasks.
- **YAML**: For secure API key management.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/baileyarzate/NimbusAI.git
   cd NimbusAI
   ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt #requirements file yet to be created.
    ```
3. Add your Google GenAI API key in api_key.yaml:
    ```yaml
    api_key: YOUR_API_KEY
    ```

## Usage
1. Ensure your drone is set up and connected to MAVSDK.
2. Start the program:
    ```bash
    python main.py
    ```
3. Enter natural language commands in the terminal, such as:
    - Fly North to 50.123, 10.456
    - Land at the current location
    - Return to base

4. The drone will interpret and execute commands, displaying real-time telemetry and status updates.

## Supported Commands
Command	    Description
goto	    Fly to a specified location with latitude, longitude, altitude, and yaw.
takeoff	    Take off to a specified altitude.
land	    Land at the current location.
stop	    Stop current action and hover at the current location.
rtb	        Return to the base location recorded at initialization.
hold	    Hold position and hover in place.

## Architecture
    - Commands: Each maneuver is implemented in modular command files (commands folder).
    - Helpers: Utility functions for prompt generation and JSON processing (helper folder).
    - Telemetry: Retrieves and formats real-time telemetry data (stateinfo folder).

## Future Improvements
    - Add speech-to-text integration for hands-free commands.
    - Enhance error handling for robust operation in diverse scenarios.
    - Expand the command set for advanced drone operations.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request with proposed changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
