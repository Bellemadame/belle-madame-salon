#!/bin/bash
# Belle Madame Salon - Quick Start for space.minimax.io

echo "=========================================="
echo "Belle Madame Salon Booking System"
echo "=========================================="

# Install dependencies
echo "Installing dependencies..."
pip install flask python-dotenv gunicorn

# Initialize database if needed
if [ ! -f "salon_data.db" ]; then
    echo "Creating database..."
    python -c "
import sqlite3
conn = sqlite3.connect('salon_data.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY, category TEXT, name TEXT, price REAL, duration INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, client_name TEXT, phone TEXT, service_id INTEGER, staff_id INTEGER, date TEXT, hour INTEGER, duration INTEGER, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS staff_services (staff_id INTEGER, service_id INTEGER, PRIMARY KEY(staff_id, service_id))''')

# Add staff
staff = ['Sarah', 'Emma', 'Lisa', 'Nadia']
for name in staff:
    c.execute('INSERT OR IGNORE INTO staff (name) VALUES (?)', (name,))

# Add services
services = [
    ('GEL NAILS', 'Lola Lee Gel Overlays', 250, 1),
    ('GEL NAILS', 'Lola Lee Gel Overlays Toes', 185, 1),
    ('GEL NAILS', 'Gel Tips', 285, 1.5),
    ('GEL NAILS', 'Gel Soft Tips', 300, 1.5),
    ('ACRYLIC NAILS', 'Acrylic Overlays', 280, 1),
    ('ACRYLIC NAILS', 'Acrylic Toes Overlays', 200, 1),
    ('ACRYLIC NAILS', 'Acrylic Tips', 320, 1.5),
    ('NAIL ART', 'Stickers (Per Nail)', 10, 0.1),
    ('NAIL ART', 'Free Hand Art (Per Nail)', 25, 0.15),
    ('NAIL ART', 'Add French', 50, 0.1),
    ('NAIL ART', 'Soak Off', 50, 0.25),
    ('PEDICURES', 'Basic Pedicure (30 min)', 150, 0.5),
    ('PEDICURES', 'Basic Pedi + Gel Paint', 250, 0.75),
    ('PEDICURES', 'Spa Pedicure (45 min)', 250, 0.75),
    ('PEDICURES', 'Spa Pedi + Gel Paint', 350, 1),
    ('PEDICURES', 'Deluxe Pedicure (1 hour)', 350, 1),
    ('PEDICURES', 'Deluxe Pedi + Gel Paint', 450, 1.25),
    ('WEEKDAY SPECIALS', 'Wash + Set (Weekend)', 159, 0.5),
    ('WEEKDAY SPECIALS', 'Wash Set + Treat (Weekday)', 220, 0.75),
    ('WEEKDAY SPECIALS', 'Pensioners (Mon-Thurs)', 139, 0.5),
    ('WASH & SET', 'Wash & Set (Very Short/Side)', 159, 0.5),
    ('WASH & SET', 'Wash & Set (Short up to Bob)', 179, 0.5),
    ('WASH & SET', 'Wash & Set (Med to Mid Back)', 199, 0.75),
    ('WASH & SET', 'Wash & Set + Curls (Long)', 250, 1),
    ('TREATMENTS', 'Karseell', 125, 0.5),
    ('TREATMENTS', 'Botox (Non Chemical)', 110, 0.5),
    ('TREATMENTS', 'Kadus', 150, 0.5),
    ('CHEMICALS', 'Chemical Botox Wash & Set', 500, 2.5),
    ('CHEMICALS', 'Root Colour, Wash + Set', 350, 2),
    ('CHEMICALS', 'Add Treatment', 100, 0.5),
    ('CHEMICALS', 'Full Colour', 400, 2),
    ('CHEMICALS', 'Foils (Per Foil)', 20, 0.1),
    ('CHEMICALS', 'Toning', 100, 0.75),
    ('CUTS', 'Trim up to 2cm', 50, 0.25),
    ('CUTS', 'Styled Cuts (incl Wash + Set)', 300, 1),
    ('CUTS', 'Long Cuts (incl Wash + Set)', 350, 1.25),
    ('LASHES', 'Individuals', 350, 1.5),
    ('LASHES', 'Clusters', 200, 1),
    ('MANICURES', 'Manicure', 200, 0.5),
    ('MANICURES', 'Nail Prep, Buff & Shine', 100, 0.25),
    ('FACIALS', 'Deep Cleansing Facial (45 min)', 350, 0.75),
    ('FACIALS', 'Dermaplaning Facial (45 min)', 400, 0.75),
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
for category, name, price, duration in services:
    c.execute('INSERT OR IGNORE INTO services (category, name, price, duration) VALUES (?, ?, ?, ?)', (category, name, price, duration))

conn.commit()
conn.close()
print('Database created with 49 services!')
"
fi

echo ""
echo "=========================================="
echo "Starting server..."
echo "=========================================="
echo ""

# Start with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
