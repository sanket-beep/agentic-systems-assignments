import json

# Step 1 — Parse the API Response
raw_api_response = '''
{
  "route": "Delhi → Mumbai",
  "search_date": "2026-06-10",
  "flights": [
    {"flight_id": "AI-201", "airline": "Air India", "departure": "06:00", "price": 4500, "seats_available": 3},
    {"flight_id": "6E-305", "airline": "IndiGo", "departure": "09:30", "price": 3800, "seats_available": 1},
    {"flight_id": "SG-112", "airline": "SpiceJet", "departure": "13:15", "price": 3200, "seats_available": 0},
    {"flight_id": "UK-444", "airline": "Vistara", "departure": "17:45", "price": 5100, "seats_available": 5},
    {"flight_id": "6E-890", "airline": "IndiGo", "departure": "21:00", "price": 3600, "seats_available": 2}
  ]
}
'''

data = json.loads(raw_api_response)

# Step 2 — Filter Unavailable Flights
available_flights = [
    flight for flight in data["flights"]
    if flight["seats_available"] >= 2
]

print(f"Available flights after filtering: {len(available_flights)}")

# Step 3 — Find the Best Deal
cheapest_flight = min(available_flights, key=lambda flight: flight["price"])

print(
    f"Best deal: {cheapest_flight['airline']} "
    f"({cheapest_flight['flight_id']}) at ₹{cheapest_flight['price']}"
)

# Step 4 — Build a Booking Summary
booking_summary = {
    "route": data["route"],
    "selected_flight_id": cheapest_flight["flight_id"],
    "airline": cheapest_flight["airline"],
    "departure": cheapest_flight["departure"],
    "price": cheapest_flight["price"],
    "status": "ready_to_book"
}

# Step 5 — Convert to JSON and Print
booking_summary_json = json.dumps(booking_summary, indent=2)

print("\nBooking Summary (JSON):")
print(booking_summary_json)