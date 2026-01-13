"""
Belle Madame Salon Online Booking System
Flask Backend Application

This module handles all API endpoints for the online booking system,
including service/staff listing, availability checking, and booking creation.
Integrates with the existing salon_data.db SQLite database.
"""

from flask import Flask, render_template, request, jsonify, g
from datetime import datetime, date, timedelta
from functools import wraps
import sqlite3
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Use absolute path for database based on app location
app_dir = os.path.dirname(os.path.abspath(__file__))
app.config['DATABASE'] = os.path.join(app_dir, os.getenv('DATABASE_PATH', 'salon_data.db'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'belle-madame-secret-key')

# Salon opening hours configuration
OPENING_HOURS = {
    0: (9, 19),   # Monday
    1: (9, 19),   # Tuesday
    2: (9, 19),   # Wednesday
    3: (9, 19),   # Thursday
    4: (9, 20),   # Friday
    5: (9, 20),   # Saturday
    6: (9, 19),   # Sunday
}


def get_db():
    """
    Get database connection for current request context.
    Uses SQLite with foreign key support enabled.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_database():
    """
    Initialize database connection and ensure tables exist.
    This connects to the existing salon_data.db used by the desktop app.
    """
    conn = get_db()
    c = conn.cursor()
    
    # Ensure required tables exist (they should from desktop app)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY, category TEXT, name TEXT, price REAL, duration INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, client_name TEXT, phone TEXT, service_id INTEGER, staff_id INTEGER, date TEXT, hour INTEGER, duration INTEGER, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS staff_services (staff_id INTEGER, service_id INTEGER, PRIMARY KEY(staff_id, service_id))''')
    
    conn.commit()
    return conn


def validate_phone(phone):
    """
    Validate phone number format.
    Accepts South African formats: 0711234567, +27711234567, 071 123 4567
    """
    # Remove all whitespace and dashes
    cleaned = re.sub(r'[\s\-]', '', phone)
    # South African phone patterns
    pattern = r'^(?:\+?27|0)?[0-9]{9,10}$'
    return bool(re.match(pattern, cleaned))


def validate_date(booking_date):
    """Validate that booking date is not in the past."""
    try:
        parsed_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        return parsed_date >= date.today()
    except (ValueError, TypeError):
        return False


def check_availability(db, staff_id, booking_date, start_hour, duration):
    """
    Check if a time slot is available for booking.
    
    Args:
        db: Database connection
        staff_id: ID of the staff member
        booking_date: Date of booking (YYYY-MM-DD format)
        start_hour: Start hour of the appointment
        duration: Duration in hours
    
    Returns:
        bool: True if slot is available, False otherwise
    """
    c = db.cursor()
    
    # Get all existing bookings for this staff member on this date
    c.execute('''SELECT hour, duration FROM bookings 
                 WHERE staff_id = ? AND date = ?''', (staff_id, booking_date))
    existing_bookings = c.fetchall()
    
    # Check for overlaps
    booking_end = start_hour + duration
    
    for existing_hour, existing_duration in existing_bookings:
        existing_end = existing_hour + existing_duration
        
        # Check if new booking overlaps with existing booking
        # Overlap occurs if: new_start < existing_end AND new_end > existing_start
        if start_hour < existing_end and booking_end > existing_hour:
            return False
    
    return True


def get_opening_hours(booking_date):
    """
    Get opening hours for a specific date.
    
    Args:
        booking_date: Date to check
    
    Returns:
        tuple: (opening_hour, closing_hour) or None if closed
    """
    try:
        weekday = datetime.strptime(booking_date, '%Y-%m-%d').weekday()
        return OPENING_HOURS.get(weekday)
    except (ValueError, TypeError):
        return None


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render the main booking page."""
    return render_template('booking.html')


@app.route('/api/config')
def get_config():
    """Get salon configuration (opening hours, etc.)."""
    return jsonify({
        'opening_hours': OPENING_HOURS,
        'currency': 'R',
        'business_name': 'Belle Madame Salon'
    })


@app.route('/api/services', methods=['GET'])
def get_services():
    """
    Get all available services.
    
    Returns:
        JSON array of services with id, name, price, duration, category
    """
    db = get_db()
    c = db.cursor()
    c.execute('''SELECT id, category, name, price, duration FROM services ORDER BY category, name''')
    services = [dict(row) for row in c.fetchall()]
    return jsonify(services)


@app.route('/api/staff', methods=['GET'])
def get_staff():
    """
    Get all staff members, optionally filtered by service.
    
    Query Parameters:
        service_id: Filter staff who can perform this service
    
    Returns:
        JSON array of staff members
    """
    db = get_db()
    c = db.cursor()
    service_id = request.args.get('service_id', type=int)
    
    if service_id:
        # Get staff who can perform this service
        c.execute('''SELECT s.id, s.name FROM staff s
                     JOIN staff_services ss ON s.id = ss.staff_id
                     WHERE ss.service_id = ?''', (service_id,))
        
        # If no staff_services mappings exist, return all staff
        if c.fetchone() is None:
            c.execute('SELECT id, name FROM staff ORDER BY name')
    else:
        c.execute('SELECT id, name FROM staff ORDER BY name')
    
    staff = [dict(row) for row in c.fetchall()]
    return jsonify(staff)


@app.route('/api/slots', methods=['GET'])
def get_available_slots():
    """
    Get available time slots for a specific date, staff, and service duration.
    
    Query Parameters:
        date: Booking date (YYYY-MM-DD)
        staff_id: Staff member ID
        service_id: Service ID (to get duration)
    
    Returns:
        JSON array of available time slots
    """
    db = get_db()
    c = db.cursor()
    
    booking_date = request.args.get('date')
    staff_id = request.args.get('staff_id', type=int)
    service_id = request.args.get('service_id', type=int)
    
    # Validate required parameters
    if not all([booking_date, staff_id, service_id]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Get service duration
    c.execute('SELECT duration FROM services WHERE id = ?', (service_id,))
    service = c.fetchone()
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    
    duration = service['duration']
    
    # Get opening hours for this date
    opening_hours = get_opening_hours(booking_date)
    if not opening_hours:
        return jsonify({'error': 'Salon is closed on this date'}), 400
    
    opening_hour, closing_hour = opening_hours
    
    # Get existing bookings for this staff member on this date
    c.execute('''SELECT hour, duration FROM bookings 
                 WHERE staff_id = ? AND date = ?''', (staff_id, booking_date))
    bookings = c.fetchall()
    
    # Calculate available slots (30-minute intervals)
    available_slots = []
    slot_duration = 0.5  # 30-minute slots
    
    current_time = opening_hour
    
    while current_time + duration <= closing_hour:
        # Check if this slot conflicts with any existing booking
        is_available = True
        slot_end = current_time + duration
        
        for booking_hour, booking_duration in bookings:
            booking_end = booking_hour + booking_duration
            
            # Check for overlap
            if current_time < booking_end and slot_end > booking_hour:
                is_available = False
                break
        
        if is_available:
            # Format time as HH:MM
            hours = int(current_time)
            minutes = int((current_time - hours) * 60)
            time_str = f"{hours:02d}:{minutes:02d}"
            available_slots.append(time_str)
        
        current_time += slot_duration
    
    return jsonify({
        'date': booking_date,
        'staff_id': staff_id,
        'service_duration': duration,
        'slots': available_slots
    })


@app.route('/api/book', methods=['POST'])
def create_booking():
    """
    Create a new booking.
    
    Request Body (JSON):
        client_name: Client's full name
        phone: Contact phone number
        service_id: Selected service ID
        staff_id: Selected staff ID
        date: Booking date (YYYY-MM-DD)
        hour: Start hour (e.g., 14 for 14:00)
        notes: Optional booking notes
    
    Returns:
        JSON response with booking confirmation or error
    """
    db = get_db()
    c = db.cursor()
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['client_name', 'phone', 'service_id', 'staff_id', 'date', 'hour']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate phone format
    if not validate_phone(data['phone']):
        return jsonify({'error': 'Invalid phone number format. Please use South African format (e.g., 0711234567 or +27711234567)'}), 400
    
    # Validate date is not in the past
    if not validate_date(data['date']):
        return jsonify({'error': 'Cannot book appointments in the past'}), 400
    
    # Validate hour is within opening hours
    opening_hours = get_opening_hours(data['date'])
    if not opening_hours:
        return jsonify({'error': 'Salon is closed on this date'}), 400
    
    # Get service duration
    c.execute('SELECT duration FROM services WHERE id = ?', (data['service_id'],))
    service = c.fetchone()
    if not service:
        return jsonify({'error': 'Service not found'}), 400
    
    duration = service['duration']
    start_hour = int(data['hour'])
    
    # Check if start time + duration fits within opening hours
    if start_hour + duration > opening_hours[1]:
        return jsonify({'error': 'Selected time does not fit within operating hours'}), 400
    
    # Check availability (race condition protection)
    if not check_availability(db, data['staff_id'], data['date'], start_hour, duration):
        return jsonify({'error': 'Sorry, this time slot is no longer available. Please select another time.'}), 409
    
    try:
        # Insert booking
        c.execute('''INSERT INTO bookings 
                     (client_name, phone, service_id, staff_id, date, hour, duration, notes) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
            data['client_name'],
            data['phone'],
            data['service_id'],
            data['staff_id'],
            data['date'],
            start_hour,
            duration,
            data.get('notes', '')
        ))
        booking_id = c.lastrowid
        db.commit()
        
        # Get booking details for confirmation
        c.execute('''SELECT b.*, s.name as service_name, s.price, st.name as staff_name
                     FROM bookings b
                     JOIN services s ON b.service_id = s.id
                     JOIN staff st ON b.staff_id = st.id
                     WHERE b.id = ?''', (booking_id,))
        booking = dict(c.fetchone())
        
        # Send confirmation SMS (in production, this would be async)
        try:
            from sms_utils import send_confirmation_sms
            send_confirmation_sms(
                phone=data['phone'],
                client_name=data['client_name'],
                service_name=booking['service_name'],
                date=booking['date'],
                hour=start_hour,
                staff_name=booking['staff_name']
            )
        except ImportError:
            # SMS module not available, log for debugging
            app.logger.info(f"SMS confirmation would be sent to {data['phone']}")
        
        return jsonify({
            'success': True,
            'message': 'Booking confirmed successfully!',
            'booking': {
                'id': booking_id,
                'client_name': booking['client_name'],
                'service_name': booking['service_name'],
                'date': booking['date'],
                'hour': f"{start_hour:02d}:00",
                'staff_name': booking['staff_name'],
                'price': booking['price']
            }
        })
        
    except sqlite3.IntegrityError as e:
        db.rollback()
        return jsonify({'error': 'Database error. Please try again.'}), 500


@app.route('/api/bookings/check', methods=['POST'])
def check_booking_availability():
    """
    Check if a specific time slot is available without creating a booking.
    Used for real-time availability updates.
    
    Request Body (JSON):
        staff_id: Staff member ID
        date: Booking date (YYYY-MM-DD)
        hour: Start hour
        duration: Duration in hours
    
    Returns:
        JSON with availability status
    """
    db = get_db()
    data = request.get_json()
    
    is_available = check_availability(
        db,
        data.get('staff_id'),
        data.get('date'),
        data.get('hour', 0),
        data.get('duration', 1)
    )
    
    return jsonify({'available': is_available})


if __name__ == '__main__':
    # Run the Flask app
    with app.app_context():
        # Initialize database on startup
        init_database()
    
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'True').lower() == 'true'
    )
