"""
Belle Madame Salon Online Booking System
Database Utilities Module

This module provides database connection utilities and availability
calculation logic for the booking system.
"""

import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import os


class DatabaseManager:
    """
    Manages database connections and operations for the salon booking system.
    Designed to work with the existing salon_data.db schema.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. Defaults to salon_data.db in current directory.
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'salon_data.db')
        self.opening_hours = {
            0: (9, 19),  # Monday
            1: (9, 19),  # Tuesday
            2: (9, 19),  # Wednesday
            3: (9, 19),  # Thursday
            4: (9, 20),  # Friday
            5: (9, 20),  # Saturday
            6: (9, 19),  # Sunday
        }
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with foreign key support.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def close_connection(self, conn: sqlite3.Connection):
        """Close a database connection."""
        if conn:
            conn.close()
    
    # ========================================================================
    # SERVICE OPERATIONS
    # ========================================================================
    
    def get_all_services(self) -> List[Dict]:
        """
        Get all available services.
        
        Returns:
            List of service dictionaries with id, category, name, price, duration
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT id, category, name, price, duration 
                     FROM services 
                     ORDER BY category, name''')
        services = [dict(row) for row in c.fetchall()]
        conn.close()
        return services
    
    def get_service_by_id(self, service_id: int) -> Optional[Dict]:
        """
        Get a service by ID.
        
        Args:
            service_id: The service ID
        
        Returns:
            Service dictionary or None if not found
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT id, category, name, price, duration 
                     FROM services WHERE id = ?''', (service_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_services_by_category(self, category: str) -> List[Dict]:
        """
        Get services filtered by category.
        
        Args:
            category: Service category name
        
        Returns:
            List of service dictionaries
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT id, category, name, price, duration 
                     FROM services WHERE category = ? 
                     ORDER BY name''', (category,))
        services = [dict(row) for row in c.fetchall()]
        conn.close()
        return services
    
    def get_categories(self) -> List[str]:
        """
        Get all unique service categories.
        
        Returns:
            List of category names
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT DISTINCT category FROM services ORDER BY category')
        categories = [row[0] for row in c.fetchall()]
        conn.close()
        return categories
    
    # ========================================================================
    # STAFF OPERATIONS
    # ========================================================================
    
    def get_all_staff(self) -> List[Dict]:
        """
        Get all staff members.
        
        Returns:
            List of staff dictionaries with id and name
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name FROM staff ORDER BY name')
        staff = [dict(row) for row in c.fetchall()]
        conn.close()
        return staff
    
    def get_staff_by_id(self, staff_id: int) -> Optional[Dict]:
        """
        Get a staff member by ID.
        
        Args:
            staff_id: The staff ID
        
        Returns:
            Staff dictionary or None if not found
        """
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name FROM staff WHERE id = ?', (staff_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_staff_for_service(self, service_id: int) -> List[Dict]:
        """
        Get staff members who can perform a specific service.
        
        Args:
            service_id: The service ID
        
        Returns:
            List of staff dictionaries
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        # Check if staff_services mappings exist
        c.execute('SELECT COUNT(*) FROM staff_services WHERE service_id = ?', (service_id,))
        has_mappings = c.fetchone()[0] > 0
        
        if has_mappings:
            # Get staff assigned to this service
            c.execute('''SELECT s.id, s.name FROM staff s
                         JOIN staff_services ss ON s.id = ss.staff_id
                         WHERE ss.service_id = ?
                         ORDER BY s.name''', (service_id,))
        else:
            # No mappings, return all staff
            c.execute('SELECT id, name FROM staff ORDER BY name')
        
        staff = [dict(row) for row in c.fetchall()]
        conn.close()
        return staff
    
    # ========================================================================
    # BOOKING OPERATIONS
    # ========================================================================
    
    def create_booking(self, booking_data: Dict) -> int:
        """
        Create a new booking.
        
        Args:
            booking_data: Dictionary containing booking details
        
        Returns:
            ID of the newly created booking
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT INTO bookings 
                     (client_name, phone, service_id, staff_id, date, hour, duration, notes) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
            booking_data['client_name'],
            booking_data['phone'],
            booking_data['service_id'],
            booking_data['staff_id'],
            booking_data['date'],
            booking_data['hour'],
            booking_data['duration'],
            booking_data.get('notes', '')
        ))
        
        booking_id = c.lastrowid
        conn.commit()
        conn.close()
        return booking_id
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict]:
        """
        Get booking details by ID.
        
        Args:
            booking_id: The booking ID
        
        Returns:
            Booking dictionary with service and staff details
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT b.*, s.name as service_name, s.price, st.name as staff_name
                     FROM bookings b
                     JOIN services s ON b.service_id = s.id
                     JOIN staff st ON b.staff_id = st.id
                     WHERE b.id = ?''', (booking_id,))
        
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_bookings_for_date(self, booking_date: str) -> List[Dict]:
        """
        Get all bookings for a specific date.
        
        Args:
            booking_date: Date in YYYY-MM-DD format
        
        Returns:
            List of booking dictionaries
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT b.*, s.name as service_name, st.name as staff_name
                     FROM bookings b
                     JOIN services s ON b.service_id = s.id
                     JOIN staff st ON b.staff_id = st.id
                     WHERE b.date = ?
                     ORDER BY b.hour''', (booking_date,))
        
        bookings = [dict(row) for row in c.fetchall()]
        conn.close()
        return bookings
    
    def get_bookings_for_reminder(self, reminder_date: str) -> List[Dict]:
        """
        Get all bookings for a specific date (used for reminders).
        
        Args:
            reminder_date: Date in YYYY-MM-DD format
        
        Returns:
            List of booking dictionaries with client contact info
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT b.id, b.client_name, b.phone, b.date, b.hour, 
                            s.name as service_name, st.name as staff_name
                     FROM bookings b
                     JOIN services s ON b.service_id = s.id
                     JOIN staff st ON b.staff_id = st.id
                     WHERE b.date = ?''', (reminder_date,))
        
        bookings = [dict(row) for row in c.fetchall()]
        conn.close()
        return bookings
    
    # ========================================================================
    # AVAILABILITY CALCULATIONS
    # ========================================================================
    
    def get_opening_hours(self, booking_date: str) -> Optional[Tuple[int, int]]:
        """
        Get opening hours for a specific date.
        
        Args:
            booking_date: Date in YYYY-MM-DD format
        
        Returns:
            Tuple of (opening_hour, closing_hour) or None if closed
        """
        try:
            weekday = datetime.strptime(booking_date, '%Y-%m-%d').weekday()
            return self.opening_hours.get(weekday)
        except (ValueError, TypeError):
            return None
    
    def is_date_closed(self, booking_date: str) -> bool:
        """
        Check if the salon is closed on a specific date.
        
        Args:
            booking_date: Date in YYYY-MM-DD format
        
        Returns:
            True if closed, False if open
        """
        return self.get_opening_hours(booking_date) is None
    
    def get_booked_slots(self, staff_id: int, booking_date: str) -> List[Tuple[int, int]]:
        """
        Get all booked time slots for a staff member on a date.
        
        Args:
            staff_id: Staff member ID
            booking_date: Date in YYYY-MM-DD format
        
        Returns:
            List of tuples (start_hour, duration) for each booking
        """
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT hour, duration FROM bookings 
                     WHERE staff_id = ? AND date = ?''', (staff_id, booking_date))
        
        slots = [(row['hour'], row['duration']) for row in c.fetchall()]
        conn.close()
        return slots
    
    def is_slot_available(self, staff_id: int, booking_date: str, 
                          start_hour: float, duration: int) -> bool:
        """
        Check if a specific time slot is available.
        
        Args:
            staff_id: Staff member ID
            booking_date: Date in YYYY-MM-DD format
            start_hour: Start hour (can be decimal for half-hour slots)
            duration: Duration in hours
        
        Returns:
            True if slot is available, False if booked
        """
        booked_slots = self.get_booked_slots(staff_id, booking_date)
        slot_end = start_hour + duration
        
        for booked_hour, booked_duration in booked_slots:
            booked_end = booked_hour + booked_duration
            
            # Check for overlap
            if start_hour < booked_end and slot_end > booked_hour:
                return False
        
        return True
    
    def calculate_available_slots(self, staff_id: int, booking_date: str, 
                                   service_duration: int) -> List[str]:
        """
        Calculate all available time slots for a service on a given date.
        
        Args:
            staff_id: Staff member ID
            booking_date: Date in YYYY-MM-DD format
            service_duration: Duration of service in hours
        
        Returns:
            List of available time strings (e.g., ['09:00', '09:30', ...])
        """
        opening_hours = self.get_opening_hours(booking_date)
        
        if not opening_hours:
            return []
        
        opening_hour, closing_hour = opening_hours
        
        # Get booked slots
        booked_slots = self.get_booked_slots(staff_id, booking_date)
        
        # Calculate available slots in 30-minute intervals
        available_slots = []
        slot_duration = 0.5  # 30-minute intervals
        current_time = opening_hour
        
        while current_time + service_duration <= closing_hour:
            # Check if this slot conflicts with any booking
            is_available = True
            slot_end = current_time + service_duration
            
            for booked_hour, booked_duration in booked_slots:
                booked_end = booked_hour + booked_duration
                
                if current_time < booked_end and slot_end > booked_hour:
                    is_available = False
                    break
            
            if is_available:
                # Format as HH:MM
                hours = int(current_time)
                minutes = int((current_time - hours) * 60)
                time_str = f"{hours:02d}:{minutes:02d}"
                available_slots.append(time_str)
            
            current_time += slot_duration
        
        return available_slots
    
    def get_available_slots_filtered(self, staff_id: int, booking_date: str, 
                                      service_id: int) -> Dict:
        """
        Get available slots for a specific service with all validation.
        
        Args:
            staff_id: Staff member ID
            booking_date: Date in YYYY-MM-DD format
            service_id: Service ID
        
        Returns:
            Dictionary with slots and service details
        """
        service = self.get_service_by_id(service_id)
        
        if not service:
            return {'error': 'Service not found', 'slots': []}
        
        opening_hours = self.get_opening_hours(booking_date)
        
        if not opening_hours:
            return {
                'error': 'Salon is closed on this date',
                'slots': [],
                'closed': True
            }
        
        slots = self.calculate_available_slots(
            staff_id, 
            booking_date, 
            service['duration']
        )
        
        return {
            'date': booking_date,
            'staff_id': staff_id,
            'service': service,
            'opening_hours': opening_hours,
            'slots': slots
        }


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def init_sample_data(db_path: str = None):
    """
    Initialize sample data for testing purposes.
    This only adds data if tables are empty.
    
    Args:
        db_path: Path to database file
    """
    db = DatabaseManager(db_path)
    conn = db.get_connection()
    c = conn.cursor()
    
    # Check if services exist
    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        # All services from Belle Madame Salon menu
        services = [
            # GEL NAILS
            ('GEL NAILS', 'Lola Lee Gel Overlays', 250, 1),
            ('GEL NAILS', 'Lola Lee Gel Overlays Toes', 185, 1),
            ('GEL NAILS', 'Gel Tips', 285, 1.5),
            ('GEL NAILS', 'Gel Soft Tips', 300, 1.5),
            
            # ACRYLIC NAILS
            ('ACRYLIC NAILS', 'Acrylic Overlays', 280, 1),
            ('ACRYLIC NAILS', 'Acrylic Toes Overlays', 200, 1),
            ('ACRYLIC NAILS', 'Acrylic Tips', 320, 1.5),
            
            # NAIL ART
            ('NAIL ART', 'Stickers (Per Nail)', 10, 0.1),
            ('NAIL ART', 'Free Hand Art (Per Nail)', 25, 0.15),
            ('NAIL ART', 'Add French', 50, 0.1),
            ('NAIL ART', 'Soak Off', 50, 0.25),
            
            # PEDICURES
            ('PEDICURES', 'Basic Pedicure (30 min)', 150, 0.5),
            ('PEDICURES', 'Basic Pedi + Gel Paint', 250, 0.75),
            ('PEDICURES', 'Spa Pedicure (45 min)', 250, 0.75),
            ('PEDICURES', 'Spa Pedi + Gel Paint', 350, 1),
            ('PEDICURES', 'Deluxe Pedicure (1 hour)', 350, 1),
            ('PEDICURES', 'Deluxe Pedi + Gel Paint', 450, 1.25),
            
            # WEEKDAY SPECIALS
            ('WEEKDAY SPECIALS', 'Wash + Set (Weekend)', 159, 0.5),
            ('WEEKDAY SPECIALS', 'Wash Set + Treat (Weekday)', 220, 0.75),
            ('WEEKDAY SPECIALS', 'Pensioners (Mon-Thurs)', 139, 0.5),
            
            # WASH & SET
            ('WASH & SET', 'Wash & Set (Very Short/Side)', 159, 0.5),
            ('WASH & SET', 'Wash & Set (Short up to Bob)', 179, 0.5),
            ('WASH & SET', 'Wash & Set (Med to Mid Back)', 199, 0.75),
            ('WASH & SET', 'Wash & Set + Curls (Long)', 250, 1),
            
            # TREATMENTS
            ('TREATMENTS', 'Karseell', 125, 0.5),
            ('TREATMENTS', 'Botox (Non Chemical)', 110, 0.5),
            ('TREATMENTS', 'Kadus', 150, 0.5),
            
            # CHEMICALS
            ('CHEMICALS', 'Chemical Botox Wash & Set', 500, 2.5),
            ('CHEMICALS', 'Root Colour, Wash + Set', 350, 2),
            ('CHEMICALS', 'Add Treatment', 100, 0.5),
            ('CHEMICALS', 'Full Colour', 400, 2),
            ('CHEMICALS', 'Foils (Per Foil)', 20, 0.1),
            ('CHEMICALS', 'Toning', 100, 0.75),
            
            # CUTS
            ('CUTS', 'Trim up to 2cm', 50, 0.25),
            ('CUTS', 'Styled Cuts (incl Wash + Set)', 300, 1),
            ('CUTS', 'Long Cuts (incl Wash + Set)', 350, 1.25),
            
            # LASHES
            ('LASHES', 'Individuals', 350, 1.5),
            ('LASHES', 'Clusters', 200, 1),
            
            # MANICURES
            ('MANICURES', 'Manicure', 200, 0.5),
            ('MANICURES', 'Nail Prep, Buff & Shine', 100, 0.25),
            
            # FACIALS
            ('FACIALS', 'Deep Cleansing Facial (45 min)', 350, 0.75),
            ('FACIALS', 'Dermaplaning Facial (45 min)', 400, 0.75),
            
            # WAXING
            ('WAXING', 'Eyebrows', 60, 0.15),
            ('WAXING', 'Eyebrow Wax & Tint', 100, 0.25),
            ('WAXING', 'Upper Lip & Chin', 60, 0.15),
            ('WAXING', 'Full Face', 200, 0.5),
            ('WAXING', 'Underarms', 90, 0.25),
            ('WAXING', 'Full Legs', 150, 0.5),
            ('WAXING', 'Half Legs', 100, 0.35),
            ('WAXING', 'Full Arm', 100, 0.35),
            ('WAXING', 'Half Arm', 75, 0.25),
            ('WAXING', 'Hollywood', 500, 0.75),
            ('WAXING', 'Brazilian', 350, 0.5),
            ('WAXING', 'Bikini', 200, 0.35),
            ('WAXING', 'Vajacial (excl. wax)', 450, 0.75),
        ]
        
        c.executemany('INSERT INTO services (category, name, price, duration) VALUES (?, ?, ?, ?)', services)
        
        # Add sample staff
        staff_members = ['Sarah', 'Emma', 'Lisa', 'Nadia']
        for name in staff_members:
            c.execute('INSERT INTO staff (name) VALUES (?)', (name,))
        
        conn.commit()
        print("Sample data initialized successfully with all salon services")
    
    conn.close()


if __name__ == '__main__':
    # Initialize database with sample data
    init_sample_data()
    
    # Test the database
    db = DatabaseManager()
    
    print("\n=== Services ===")
    services = db.get_all_services()
    for s in services[:5]:
        print(f"  {s['category']}: {s['name']} - R{s['price']} ({s['duration']}h)")
    
    print("\n=== Staff ===")
    staff = db.get_all_staff()
    for s in staff:
        print(f"  {s['name']}")
    
    print("\n=== Available Slots (Today) ===")
    today = date.today().isoformat()
    if staff:
        slots = db.calculate_available_slots(staff[0]['id'], today, 1)
        print(f"  Available slots for {staff[0]['name']}: {slots[:5]}...")
