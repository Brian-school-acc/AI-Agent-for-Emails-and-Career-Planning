@tool(approval_mode="never_require")
def get_weather(location: str) -> str:
    """
    Get the current weather conditions and temperature for a given location.

    Args:
        location: The city name or location string (e.g., 'Seattle', 'Hong Kong').
    """
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(15, 32)
    low_temp = high_temp - random.randint(5, 10)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."






@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[
        str,
        Field(
            description="The city name or location string (e.g., 'Seattle', 'Hong Kong')."
        ),
    ],
) -> str:
    """Get the current weather conditions and temperature for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(15, 32)
    low_temp = high_temp - random.randint(5, 10)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."











@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str,Field(description="The city name or location string (e.g., 'Seattle', 'Hong Kong')."),],
) -> str:
    """Get the current weather conditions and temperature for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "overcast", "clear"]
    chosen_condition = random.choice(conditions)
    high_temp = random.randint(15, 32)
    low_temp = high_temp - random.randint(5, 10)

    return f"The weather in {location} is currently {chosen_condition} with a high of {high_temp}°C and a low of {low_temp}°C."

