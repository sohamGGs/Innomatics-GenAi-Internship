from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import math

app = FastAPI(title="Grand Stay Hotel Booking")

# ==========================================
# 🛑 DATA SETUP & MOCK DATABASE
# ==========================================
# Q2 Setup: Create a rooms list
rooms = [
    {"id": 1, "room_number": "101", "type": "Single", "price_per_night": 2000, "floor": 1, "is_available": True},
    {"id": 2, "room_number": "102", "type": "Double", "price_per_night": 3500, "floor": 1, "is_available": False},
    {"id": 3, "room_number": "201", "type": "Deluxe", "price_per_night": 5000, "floor": 2, "is_available": True},
    {"id": 4, "room_number": "202", "type": "Suite", "price_per_night": 8000, "floor": 2, "is_available": True},
    {"id": 5, "room_number": "301", "type": "Double", "price_per_night": 3600, "floor": 3, "is_available": False},
    {"id": 6, "room_number": "302", "type": "Suite", "price_per_night": 8500, "floor": 3, "is_available": True},
]

# Q4 Setup: Create bookings list and counter
bookings = []
booking_counter = 1

# ==========================================
# 🛠️ PYDANTIC MODELS (Q6, Q9, Q11)
# ==========================================
# Q6 & Q9: BookingRequest model with early_checkout
class BookingRequest(BaseModel):
    guest_name: str = Field(..., min_length=2)
    room_id: int = Field(..., gt=0)
    nights: int = Field(..., gt=0, le=30)
    phone: str = Field(..., min_length=10)
    meal_plan: str = Field(default="none")
    early_checkout: bool = Field(default=False)

# Q11: NewRoom model
class NewRoom(BaseModel):
    room_number: str = Field(..., min_length=1)
    type: str = Field(..., min_length=2)
    price_per_night: int = Field(..., gt=0)
    floor: int = Field(..., gt=0)
    is_available: bool = Field(default=True)

# ==========================================
# 🧠 HELPER FUNCTIONS (Q7, Q9, Q10)
# ==========================================
# Q7: Helper to find room
def find_room(room_id: int):
    for room in rooms:
        if room["id"] == room_id:
            return room
    return None

# Q7 & Q9: Helper to calculate cost with meal plans and discounts
def calculate_stay_cost(price_per_night: int, nights: int, meal_plan: str, early_checkout: bool):
    base_cost = price_per_night * nights
    meal_cost = 0
    
    if meal_plan.lower() == "breakfast":
        meal_cost = 500 * nights
    elif meal_plan.lower() == "all-inclusive":
        meal_cost = 1200 * nights
        
    subtotal = base_cost + meal_cost
    discount = 0
    
    if early_checkout:
        discount = int(subtotal * 0.10) # 10% discount
        
    total_cost = subtotal - discount
    return {"base_cost": base_cost, "meal_cost": meal_cost, "discount": discount, "total_cost": total_cost}

# Q10: Filter helper logic
def filter_rooms_logic(room_type=None, max_price=None, floor=None, is_available=None):
    filtered = rooms
    if room_type is not None:
        filtered = [r for r in filtered if r["type"].lower() == room_type.lower()]
    if max_price is not None:
        filtered = [r for r in filtered if r["price_per_night"] <= max_price]
    if floor is not None:
        filtered = [r for r in filtered if r["floor"] == floor]
    if is_available is not None:
        filtered = [r for r in filtered if r["is_available"] == is_available]
    return filtered

# ==========================================
# 🚀 API ROUTES (FIXED ROUTES FIRST)
# ==========================================

# Q1: Home Route
@app.get("/")
def read_root():
    return {"message": "Welcome to Grand Stay Hotel"}

# Q2: GET all rooms
@app.get("/rooms")
def get_rooms():
    available_count = sum(1 for r in rooms if r["is_available"])
    return {"total": len(rooms), "available_count": available_count, "rooms": rooms}

# Q5: GET rooms summary (MUST be above /rooms/{room_id})
@app.get("/rooms/summary")
def get_rooms_summary():
    available_rooms = [r for r in rooms if r["is_available"]]
    occupied_rooms = [r for r in rooms if not r["is_available"]]
    
    prices = [r["price_per_night"] for r in rooms]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    
    type_breakdown = {}
    for r in rooms:
        type_breakdown[r["type"]] = type_breakdown.get(r["type"], 0) + 1
        
    return {
        "total_rooms": len(rooms),
        "available_count": len(available_rooms),
        "occupied_count": len(occupied_rooms),
        "cheapest_price": min_price,
        "most_expensive_price": max_price,
        "type_breakdown": type_breakdown
    }

# Q10: GET filtered rooms
@app.get("/rooms/filter")
def filter_rooms(
    type: Optional[str] = None, 
    max_price: Optional[int] = None, 
    floor: Optional[int] = None, 
    is_available: Optional[bool] = None
):
    filtered = filter_rooms_logic(type, max_price, floor, is_available)
    return {"total_found": len(filtered), "rooms": filtered}

# Q16: GET rooms search
@app.get("/rooms/search")
def search_rooms(keyword: str = Query(..., description="Search room number or type")):
    keyword_lower = keyword.lower()
    matches = [
        r for r in rooms 
        if keyword_lower in r["room_number"].lower() or keyword_lower in r["type"].lower()
    ]
    if not matches:
        return {"message": f"No rooms found matching '{keyword}'"}
    return {"total_found": len(matches), "rooms": matches}

# Q17: GET rooms sort
@app.get("/rooms/sort")
def sort_rooms(sort_by: str = "price_per_night", order: str = "asc"):
    if sort_by not in ["price_per_night", "floor", "type"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by parameter")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order parameter")
        
    is_reverse = True if order == "desc" else False
    sorted_rooms = sorted(rooms, key=lambda x: x[sort_by], reverse=is_reverse)
    return {"sort_by": sort_by, "order": order, "rooms": sorted_rooms}

# Q18: GET rooms pagination
@app.get("/rooms/page")
def paginate_rooms(page: int = Query(1, ge=1), limit: int = Query(2, ge=1, le=10)):
    total = len(rooms)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "rooms": rooms[start:end]
    }

# Q20: GET rooms browse (Combined Search, Sort, Pagination)
@app.get("/rooms/browse")
def browse_rooms(
    keyword: Optional[str] = None,
    sort_by: str = "price_per_night",
    order: str = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=10)
):
    # 1. Filter
    result = rooms
    if keyword:
        kw = keyword.lower()
        result = [r for r in result if kw in r["room_number"].lower() or kw in r["type"].lower()]
        
    # 2. Sort
    if sort_by in ["price_per_night", "floor", "type"] and order in ["asc", "desc"]:
        is_reverse = True if order == "desc" else False
        result = sorted(result, key=lambda x: x[sort_by], reverse=is_reverse)
        
    # 3. Paginate
    total = len(result)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    paginated_result = result[start : start + limit]
    
    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "rooms": paginated_result
    }

# Q4: GET all bookings
@app.get("/bookings")
def get_bookings():
    return {"total": len(bookings), "bookings": bookings}

# Q15: GET active bookings
@app.get("/bookings/active")
def get_active_bookings():
    active = [b for b in bookings if b["status"] in ["confirmed", "checked_in"]]
    return {"total_active": len(active), "bookings": active}

# Q19: GET bookings search
@app.get("/bookings/search")
def search_bookings(guest_name: str):
    matches = [b for b in bookings if guest_name.lower() in b["guest_name"].lower()]
    return {"total_found": len(matches), "bookings": matches}

# Q19: GET bookings sort
@app.get("/bookings/sort")
def sort_bookings(sort_by: str = "total_cost", order: str = "asc"):
    if sort_by not in ["total_cost", "nights"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by parameter")
    is_reverse = True if order == "desc" else False
    sorted_b = sorted(bookings, key=lambda x: x[sort_by], reverse=is_reverse)
    return {"bookings": sorted_b}

# ==========================================
# 🔄 POST, PUT, DELETE ROUTES
# ==========================================

# Q11: POST add new room
@app.post("/rooms", status_code=status.HTTP_201_CREATED)
def add_room(room_data: NewRoom):
    for r in rooms:
        if r["room_number"] == room_data.room_number:
            raise HTTPException(status_code=400, detail="Room number already exists")
            
    new_id = max([r["id"] for r in rooms]) + 1 if rooms else 1
    new_room = room_data.dict()
    new_room["id"] = new_id
    rooms.append(new_room)
    return new_room

# Q8 & Q9: POST create a booking
@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(req: BookingRequest):
    global booking_counter
    room = find_room(req.room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room["is_available"]:
        raise HTTPException(status_code=400, detail="Room is currently occupied")
        
    room["is_available"] = False # Mark unavailable
    
    cost_details = calculate_stay_cost(room["price_per_night"], req.nights, req.meal_plan, req.early_checkout)
    
    new_booking = {
        "booking_id": booking_counter,
        "guest_name": req.guest_name,
        "room_details": room,
        "nights": req.nights,
        "meal_plan": req.meal_plan,
        "early_checkout": req.early_checkout,
        "discount_applied": cost_details["discount"],
        "total_cost": cost_details["total_cost"],
        "status": "confirmed" # Q14 requirement
    }
    
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

# Q14: POST check-in workflow
@app.post("/checkin/{booking_id}")
def checkin_guest(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "checked_in"
            return {"message": "Check-in successful", "booking": b}
    raise HTTPException(status_code=404, detail="Booking not found")

# Q15: POST check-out workflow
@app.post("/checkout/{booking_id}")
def checkout_guest(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "checked_out"
            # Mark room available again
            room = find_room(b["room_details"]["id"])
            if room:
                room["is_available"] = True
            return {"message": "Check-out successful", "booking": b}
    raise HTTPException(status_code=404, detail="Booking not found")

# ==========================================
# 🔻 VARIABLE ID ROUTES (MUST BE AT THE BOTTOM)
# ==========================================

# Q3: GET room by ID
@app.get("/rooms/{room_id}")
def get_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

# Q12: PUT update room
@app.put("/rooms/{room_id}")
def update_room(room_id: int, price_per_night: Optional[int] = None, is_available: Optional[bool] = None):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    if price_per_night is not None:
        room["price_per_night"] = price_per_night
    if is_available is not None:
        room["is_available"] = is_available
        
    return room

# Q13: DELETE room
@app.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    room = find_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room["is_available"]:
        raise HTTPException(status_code=400, detail="Cannot delete an occupied room")
        
    rooms.remove(room)
    return {"message": f"Room {room['room_number']} deleted successfully"}