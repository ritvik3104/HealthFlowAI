import json
from groq import Groq
from app.core.config import settings
from app.crud import crud_user, crud_appointment
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import pytz
import re

from .google_calendar_service import create_calendar_event
from .email_service import send_appointment_confirmation

client = None
if settings.GROQ_API_KEY:
    client = Groq(api_key=settings.GROQ_API_KEY)
else:
    print("Warning: GROQ_API_KEY not found in environment variables.")

# --- Enhanced In-Memory Cache for Conversation History ---
conversation_history: Dict[int, List[Dict[str, Any]]] = {}
conversation_context: Dict[int, Dict[str, Any]] = {}  # Store extracted context

# --- Agent Tools Definition ---

def find_all_doctors():
    """Finds all doctors in the system. Use this when the user asks for a recommendation."""
    db = SessionLocal()
    try:
        doctors = crud_user.get_users_by_role(db, role=UserRole.DOCTOR)
        if not doctors:
            return json.dumps({"error": "No doctors found in the system."})
        return json.dumps([{"id": doc.id, "full_name": doc.full_name} for doc in doctors])
    finally:
        db.close()

def find_doctor_by_name(doctor_name: str):
    """Finds a single doctor by their name."""
    db = SessionLocal()
    try:
        doctor = crud_user.get_doctor_by_name(db, name=doctor_name)
        if not doctor:
            return json.dumps({"error": f"No doctor found with a name like '{doctor_name}'."})
        return json.dumps({"id": doctor.id, "full_name": doctor.full_name})
    finally:
        db.close()

def check_patient_availability(patient_id: int, start_time: str):
    """Checks if the patient already has an appointment at the requested time."""
    db = SessionLocal()
    try:
        target_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        time_window_end = target_dt + timedelta(minutes=29)
        
        conflicting_appointment = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.start_time <= time_window_end,
            Appointment.end_time > target_dt
        ).first()
        
        if conflicting_appointment:
            return json.dumps({"is_available": False, "reason": "You already have another appointment scheduled at that time."})
        return json.dumps({"is_available": True})
    finally:
        db.close()

def get_available_slots(doctor_id: int, date_str: str):
    """
    Checks a specific doctor's schedule for a given date and returns all their available slots.
    """
    db = SessionLocal()
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        existing_appointments = crud_appointment.get_appointments_by_doctor_for_day(db, doctor_id=doctor_id, target_date=target_date)
        booked_slots = {appt.start_time.time() for appt in existing_appointments}
        available_slots = []
        current_slot = datetime.combine(target_date, datetime.min.time().replace(hour=9))
        end_of_workday = datetime.combine(target_date, datetime.min.time().replace(hour=17))
        while current_slot < end_of_workday:
            if current_slot.time() not in booked_slots:
                available_slots.append(current_slot.strftime("%H:%M"))
            current_slot += timedelta(minutes=30)
        if not available_slots:
            return json.dumps({"message": f"No available slots found for Dr. ID {doctor_id} on {date_str}."})
        return json.dumps({"available_slots": available_slots})
    finally:
        db.close()

def book_appointment(patient_id: int, doctor_id: int, start_time: str, notes: str):
    """Books an appointment, creates a Google Calendar event, and sends a confirmation email."""
    db = SessionLocal()
    try:
        appointment_start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        appointment_end_time = appointment_start_time + timedelta(minutes=30)
        appointment_schema = AppointmentCreate(
            patient_id=patient_id, doctor_id=doctor_id, start_time=appointment_start_time,
            end_time=appointment_end_time, notes=notes
        )
        crud_appointment.create_appointment(db, appointment=appointment_schema)
        
        patient = crud_user.get_user_by_id(db, user_id=patient_id)
        doctor = crud_user.get_user_by_id(db, user_id=doctor_id)
        
        if not patient or not doctor:
            return json.dumps({"success": False, "message": "Could not find patient or doctor."})

        summary = f"Appointment: {patient.full_name} with {doctor.full_name}"
        attendees = [patient.email, doctor.email]
        
        calendar_result = create_calendar_event(
            summary=summary, start_time=appointment_start_time, end_time=appointment_end_time,
            attendees=attendees, timezone="Asia/Kolkata"
        )
        
        send_appointment_confirmation(
            patient_email=patient.email, patient_name=patient.full_name,
            doctor_name=doctor.full_name, appointment_time=appointment_start_time.strftime("%A, %B %d, %Y at %I:%M %p")
        )
        
        if calendar_result.get("success"):
            calendar_link = calendar_result.get('link')
            # Format with markdown link syntax - many chat UIs support this
            return json.dumps({
                "success": True, 
                "message": f"Great! Your appointment is confirmed. You can [view the event here]({calendar_link})."
            })
        else:
            return json.dumps({
                "success": True, 
                "message": f"Appointment booked and email sent, but we couldn't create a calendar event: {calendar_result.get('error')}"
            })
    except Exception as e:
        return json.dumps({"success": False, "message": f"Failed to book appointment: {str(e)}"})
    finally:
        db.close()

# --- Tool Mapping and Execution ---
available_tools = {
    "find_all_doctors": find_all_doctors,
    "find_doctor_by_name": find_doctor_by_name,
    "check_patient_availability": check_patient_availability,
    "get_available_slots": get_available_slots,
    "book_appointment": book_appointment,
}

tools = [
    {"type": "function", "function": {"name": "find_all_doctors", "description": "Get a list of all available doctors. Use for general recommendations."}},
    {"type": "function", "function": {"name": "find_doctor_by_name", "description": "Get the ID of a specific doctor by their name.", "parameters": {"type": "object", "properties": {"doctor_name": {"type": "string"}}, "required": ["doctor_name"]}}},
    {"type": "function", "function": {"name": "check_patient_availability", "description": "Check if the patient already has a conflicting appointment at a specific time.", "parameters": {"type": "object", "properties": {"patient_id": {"type": "integer"}, "start_time": {"type": "string", "description": "The time to check in UTC ISO 8601 format."}}, "required": ["patient_id", "start_time"]}}},
    {"type": "function", "function": {"name": "get_available_slots", "description": "Check a specific doctor's schedule for all available slots on a given date.", "parameters": {"type": "object", "properties": {"doctor_id": {"type": "integer"}, "date_str": {"type": "string", "description": "The date in 'YYYY-MM-DD' format."}}, "required": ["doctor_id", "date_str"]}}},
    {"type": "function", "function": {"name": "book_appointment", "description": "Books a medical appointment.", "parameters": {"type": "object", "properties": {"patient_id": {"type": "integer"}, "doctor_id": {"type": "integer"}, "start_time": {"type": "string", "description": "The start time in UTC ISO 8601 format."}, "notes": {"type": "string"}}, "required": ["patient_id", "doctor_id", "start_time", "notes"]}}},
]

def parse_time_from_text(text: str, current_datetime: datetime) -> Dict[str, Any]:
    """
    Enhanced time parsing that handles relative dates and specific times.
    Returns parsed datetime in UTC and context information.
    """
    india_tz = pytz.timezone('Asia/Kolkata')
    current_india = current_datetime.astimezone(india_tz)
    
    text_lower = text.lower()
    
    # Time patterns
    time_patterns = [
        (r'(\d{1,2})\s*(?::(\d{2}))?\s*(am|pm)', 'specific_time'),
        (r'(\d{1,2})(?::(\d{2}))?\s*(?:o\'?clock)?(?:\s*(am|pm))?', 'time_casual')
    ]
    
    extracted_time = None
    for pattern, time_type in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3) if match.group(3) else None
            
            if period:
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            elif hour <= 8:  # Assume PM for times 1-8 without AM/PM
                hour += 12
                
            extracted_time = (hour, minute)
            break
    
    # Date patterns
    target_date = None
    if 'today' in text_lower:
        target_date = current_india.date()
    elif 'tomorrow' in text_lower:
        target_date = current_india.date() + timedelta(days=1)
    elif 'next week' in text_lower:
        target_date = current_india.date() + timedelta(days=7)
    else:
        # Check for specific weekdays
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(weekdays):
            if day in text_lower:
                days_ahead = i - current_india.weekday()
                if days_ahead <= 0:  # Target day is next week
                    days_ahead += 7
                target_date = current_india.date() + timedelta(days=days_ahead)
                break
    
    if not target_date:
        target_date = current_india.date()  # Default to today
        
    if extracted_time:
        hour, minute = extracted_time
        target_dt = india_tz.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute)))
        utc_dt = target_dt.astimezone(pytz.UTC)
        return {
            'datetime_utc': utc_dt.isoformat(),
            'date_str': target_date.strftime('%Y-%m-%d'),
            'time_str': f"{hour:02d}:{minute:02d}",
            'success': True
        }
    else:
        return {
            'date_str': target_date.strftime('%Y-%m-%d'),
            'success': False,
            'error': 'Could not extract specific time'
        }

def extract_booking_intent(text: str) -> Dict[str, Any]:
    """
    Analyzes user intent and extracts booking information.
    """
    text_lower = text.lower()
    
    # Intent classification
    booking_keywords = ['book', 'schedule', 'make appointment', 'reserve', 'set up']
    availability_keywords = ['available', 'free', 'open', 'doctors available', 'which doctors']
    question_keywords = ['what', 'when', 'available', 'free', 'check', 'show', 'list', 'which']
    
    is_booking_command = any(keyword in text_lower for keyword in booking_keywords)
    is_availability_query = any(keyword in text_lower for keyword in availability_keywords)
    is_question = any(keyword in text_lower for keyword in question_keywords) and not is_booking_command
    
    # Extract doctor name
    doctor_pattern = r'(?:dr\.?\s*|doctor\s+)([a-z]+(?:\s+[a-z]+)?)'
    doctor_match = re.search(doctor_pattern, text_lower)
    doctor_name = doctor_match.group(1).strip().title() if doctor_match else None
    
    return {
        'is_booking_command': is_booking_command,
        'is_question': is_question,
        'is_availability_query': is_availability_query,
        'doctor_name': doctor_name,
        'intent': 'book' if is_booking_command else 'availability' if is_availability_query else 'query' if is_question else 'unclear'
    }

def find_closest_slots(available_slots: List[str], requested_time: str, count: int = 3) -> List[str]:
    """
    Finds the closest available time slots to the requested time.
    """
    if not available_slots:
        return []
        
    try:
        requested_minutes = int(requested_time.split(':')[0]) * 60 + int(requested_time.split(':')[1])
        
        slots_with_distance = []
        for slot in available_slots:
            slot_minutes = int(slot.split(':')[0]) * 60 + int(slot.split(':')[1])
            distance = abs(slot_minutes - requested_minutes)
            slots_with_distance.append((slot, distance))
        
        # Sort by distance and return closest slots
        slots_with_distance.sort(key=lambda x: x[1])
        return [slot[0] for slot in slots_with_distance[:count]]
    except:
        return available_slots[:count]

def process_prompt(prompt: str, current_user: User):
    """
    Enhanced agentic workflow with perfect conversational memory and intelligent decision making.
    """
    if not client:
        return {"error": "Groq client is not configured."}

    current_time = datetime.now(pytz.UTC)
    user_id = current_user.id
    
    # Initialize conversation history and context if needed
    if user_id not in conversation_history:
        conversation_history[user_id] = []
        conversation_context[user_id] = {}
    
    messages = conversation_history[user_id]
    context = conversation_context[user_id]

    # Add system message only once at the start
    if not messages:
        if current_user.role == UserRole.DOCTOR:
            # Doctor-specific logic would go here
            pass
        else:  # Patient
            system_prompt = f"""You are an intelligent medical appointment assistant. You are conversational, direct, and decisive.

CRITICAL RULES:
- Patient ID is ALWAYS {user_id}
- Current time: {current_time.isoformat()} (UTC)
- Current India time: {current_time.astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M')}
- User timezone: Asia/Kolkata
- NEVER explain your internal process or reasoning
- Be natural and conversational like a human assistant
- ALWAYS understand common date references:
  * "today" = current date
  * "tomorrow" = current date + 1 day
  * "next [weekday]" = next occurrence of that weekday
- When asked about doctor availability for a date, ALWAYS:
  1. Use find_all_doctors() to get all doctors
  2. For each doctor, use get_available_slots() to check their schedule
  3. Present doctors who have available slots

WORKFLOW FOR AVAILABILITY QUERIES:
- "doctors available tomorrow" → Get all doctors, check each one's availability for tomorrow's date
- Don't ask for clarification on obvious date references
- Present results showing which doctors have openings and their available times

WORKFLOW FOR BOOKING:
1. Extract complete booking info (doctor, date, time)
2. Check patient availability first using check_patient_availability
3. If patient free, book immediately
4. If requested time unavailable, suggest 3 closest alternatives"""

            messages.append({"role": "system", "content": system_prompt})
    
    # Add user message
    messages.append({"role": "user", "content": prompt})
    
    # Enhanced context extraction and storage
    time_info = parse_time_from_text(prompt, current_time)
    intent_info = extract_booking_intent(prompt)
    
    # Update conversation context
    if intent_info.get('doctor_name'):
        context['last_doctor'] = intent_info['doctor_name']
    if time_info.get('success'):
        context['last_requested_time'] = time_info
        context['last_date'] = time_info['date_str']
        context['last_time'] = time_info['time_str']
    
    # Enhanced context extraction and storage
    time_info = parse_time_from_text(prompt, current_time)
    intent_info = extract_booking_intent(prompt)
    
    # Update conversation context
    if intent_info.get('doctor_name'):
        context['last_doctor'] = intent_info['doctor_name']
    if time_info.get('success'):
        context['last_requested_time'] = time_info
        context['last_date'] = time_info['date_str']
        context['last_time'] = time_info['time_str']
    
    # Calculate tomorrow's date for context
    tomorrow_date = (current_time.astimezone(pytz.timezone('Asia/Kolkata')).date() + timedelta(days=1)).strftime('%Y-%m-%d')
    today_date = current_time.astimezone(pytz.timezone('Asia/Kolkata')).date().strftime('%Y-%m-%d')
    
    # Store extracted context for the LLM to use
    context_summary = f"""
CONVERSATION CONTEXT:
- Intent: {intent_info.get('intent', 'unclear')}
- Is booking command: {intent_info.get('is_booking_command', False)}
- Is question: {intent_info.get('is_question', False)}
- Doctor mentioned: {context.get('last_doctor', 'None')}
- Today's date: {today_date}
- Tomorrow's date: {tomorrow_date}
- Last requested date: {context.get('last_date', 'None')}
- Last requested time: {context.get('last_time', 'None')}
- Time parsed successfully: {time_info.get('success', False)}

SMART DATE UNDERSTANDING:
- If user says "tomorrow", use date: {tomorrow_date}
- If user says "today", use date: {today_date}
- For availability queries about a date, get ALL doctors first, then check each doctor's schedule

Use this context to understand the user's request and take appropriate action."""

    messages.append({"role": "system", "content": context_summary})
    
    # Tool execution loop with enhanced logic
    max_iterations = 6
    for iteration in range(max_iterations):
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192",
                tools=tools,
                tool_choice="auto",
                temperature=0.1  # Lower temperature for more consistent responses
            )
            
            response_message = chat_completion.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                # No more tool calls, return final response
                messages.append(response_message)
                conversation_history[user_id] = messages
                conversation_context[user_id] = context
                return {"response": response_message.content}

            messages.append(response_message)
            
            # Process tool calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_tools.get(function_name)
                
                if not function_to_call:
                    continue
                    
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Auto-inject patient_id for relevant functions
                    if function_name in ['book_appointment', 'check_patient_availability']:
                        function_args['patient_id'] = current_user.id
                    
                    # Execute the function
                    function_response = function_to_call(**function_args)
                    
                    # Parse response to update context
                    try:
                        response_data = json.loads(function_response)
                        
                        # Update context based on tool results
                        if function_name == 'find_doctor_by_name' and 'id' in response_data:
                            context['last_doctor_id'] = response_data['id']
                        elif function_name == 'get_available_slots' and 'available_slots' in response_data:
                            context['last_available_slots'] = response_data['available_slots']
                        elif function_name == 'book_appointment':
                            # Clear context after successful booking
                            context.clear()
                    except json.JSONDecodeError:
                        pass
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response
                    })
                    
                except Exception as e:
                    error_message = json.dumps({"error": f"Tool execution failed: {str(e)}"})
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": error_message
                    })
        
        except Exception as e:
            # Handle API errors gracefully
            conversation_history[user_id] = messages
            conversation_context[user_id] = context
            return {"error": f"API error: {str(e)}"}
    
    # If we hit max iterations, get final response
    try:
        final_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.1
        )
        final_response = final_completion.choices[0].message
        messages.append(final_response)
        conversation_history[user_id] = messages
        conversation_context[user_id] = context
        return {"response": final_response.content}
    except Exception as e:
        return {"error": f"Final completion failed: {str(e)}"}

def clear_conversation_history(user_id: int):
    """Clear conversation history for a specific user."""
    if user_id in conversation_history:
        del conversation_history[user_id]
    if user_id in conversation_context:
        del conversation_context[user_id]

def get_conversation_summary(user_id: int) -> Dict[str, Any]:
    """Get a summary of the current conversation context."""
    return {
        'context': conversation_context.get(user_id, {}),
        'message_count': len(conversation_history.get(user_id, []))
    }








