import json
def json_string_to_dict(json_string):
    """Converts a JSON string to a Python dictionary.

    Args:
        json_string: The JSON string.

    Returns:
        A Python dictionary, or None if the string is not valid JSON.
    """
    try:
        data = json.loads(json_string)  # Use json.loads()
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}") # Print the error
        return None