"""
Belle Madame Salon Online Booking System
SMS Reminder Module

This module handles automated SMS reminders for upcoming appointments.
It can be run as a standalone script or scheduled via cron/task scheduler.
"""

import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Try to import Twilio (optional dependency)
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Warning: Twilio not installed. SMS features will be simulated.")


class SMSManager:
    """
    Manages SMS sending operations for booking confirmations and reminders.
    Supports Twilio and can be extended to other providers.
    """
    
    def __init__(self):
        """Initialize SMS manager with credentials from environment."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if self.account_sid and self.auth_token and TWILIO_AVAILABLE:
            self.client = Client(self.account_sid, self.auth_token)
            self.is_configured = True
        else:
            self.client = None
            self.is_configured = False
            if not TWILIO_AVAILABLE:
                print("Note: Install Twilio with 'pip install twilio' to enable SMS")
            else:
                print("Warning: Twilio credentials not configured. SMS will be logged only.")
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for Twilio API.
        
        Args:
            phone: Raw phone number input
        
        Returns:
            E.164 formatted phone number
        """
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Convert local South African numbers to international format
        if cleaned.startswith('0'):
            cleaned = '+27' + cleaned[1:]
        elif not cleaned.startswith('+'):
            cleaned = '+27' + cleaned
        
        return cleaned
    
    def send_sms(self, to: str, message: str) -> Dict:
        """
        Send an SMS message.
        
        Args:
            to: Recipient phone number
            message: SMS message content
        
        Returns:
            Dictionary with success status and details
        """
        formatted_phone = self.format_phone_number(to)
        
        if self.is_configured and self.client:
            try:
                msg = self.client.messages.create(
                    body=message,
                    from_=self.phone_number,
                    to=formatted_phone
                )
                return {
                    'success': True,
                    'message_id': msg.sid,
                    'status': msg.status
                }
            except TwilioException as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            # Log message for debugging when not configured
            print(f"\n[SMS SIMULATION] To: {formatted_phone}")
            print(f"Message: {message}\n")
            return {
                'success': True,
                'simulated': True,
                'message': 'SMS simulated (not configured)'
            }


def generate_confirmation_message(client_name: str, service_name: str, 
                                   date_str: str, hour: int, 
                                   staff_name: str = None) -> str:
    """
    Generate a booking confirmation message.
    
    Args:
        client_name: Client's name
        service_name: Name of the booked service
        date_str: Booking date (YYYY-MM-DD)
        hour: Start hour (24-hour format)
        staff_name: Name of staff member (optional)
    
    Returns:
        Formatted confirmation message
    """
    # Parse date for nicer formatting
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %d %B %Y')
    except ValueError:
        formatted_date = date_str
    
    time_str = f"{hour:02d}:00"
    
    message = f"Hi {client_name}! Your booking at Belle Madame Salon is confirmed.\n\n"
    message += f"Service: {service_name}\n"
    message += f"Date: {formatted_date}\n"
    message += f"Time: {time_str}"
    
    if staff_name:
        message += f"\nStaff: {staff_name}"
    
    message += "\n\nReply CANCEL to cancel your appointment."
    
    return message


def generate_reminder_message(client_name: str, service_name: str,
                               date_str: str, hour: int) -> str:
    """
    Generate a 24-hour reminder message.
    
    Args:
        client_name: Client's name
        service_name: Name of the booked service
        date_str: Booking date (YYYY-MM-DD)
        hour: Start hour (24-hour format)
    
    Returns:
        Formatted reminder message
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %d %B')
    except ValueError:
        formatted_date = date_str
    
    time_str = f"{hour:02d}:00"
    
    message = f"Reminder: Hi {client_name}, you have an appointment at Belle Madame Salon tomorrow!\n\n"
    message += f"Service: {service_name}\n"
    message += f"Time: {time_str}\n\n"
    message += "We look forward to seeing you!"
    
    return message


def send_confirmation_sms(phone: str, client_name: str, service_name: str,
                          date: str, hour: int, staff_name: str = None) -> Dict:
    """
    Send a booking confirmation SMS.
    
    Args:
        phone: Client's phone number
        client_name: Client's name
        service_name: Booked service name
        date: Booking date
        hour: Start hour
        staff_name: Staff member name
    
    Returns:
        SMS send result dictionary
    """
    sms_manager = SMSManager()
    message = generate_confirmation_message(client_name, service_name, date, hour, staff_name)
    return sms_manager.send_sms(phone, message)


def send_reminder_sms(phone: str, client_name: str, service_name: str,
                       date: str, hour: int) -> Dict:
    """
    Send a 24-hour reminder SMS.
    
    Args:
        phone: Client's phone number
        client_name: Client's name
        service_name: Booked service name
        date: Booking date
        hour: Start hour
    
    Returns:
        SMS send result dictionary
    """
    sms_manager = SMSManager()
    message = generate_reminder_message(client_name, service_name, date, hour)
    return sms_manager.send_sms(phone, message)


def process_reminders(db_path: str = None) -> Dict:
    """
    Process reminders for all appointments tomorrow.
    
    Args:
        db_path: Path to the database file
    
    Returns:
        Dictionary with processing results
    """
    from database import DatabaseManager
    
    db = DatabaseManager(db_path)
    
    # Calculate tomorrow's date
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    # Get all bookings for tomorrow
    bookings = db.get_bookings_for_reminder(tomorrow)
    
    results = {
        'date': tomorrow,
        'total_bookings': len(bookings),
        'sent': 0,
        'failed': 0,
        'details': []
    }
    
    print(f"\n{'='*60}")
    print(f"Processing reminders for {tomorrow}")
    print(f"Found {len(bookings)} bookings")
    print(f"{'='*60}\n")
    
    for booking in bookings:
        client_name = booking['client_name']
        phone = booking['phone']
        service_name = booking['service_name']
        hour = booking['hour']
        
        result = send_reminder_sms(phone, client_name, service_name, tomorrow, hour)
        
        status = 'SENT' if result['success'] else 'FAILED'
        results['details'].append({
            'client': client_name,
            'phone': phone[:4] + '****',  # Mask phone for privacy
            'service': service_name,
            'time': f"{hour:02d}:00",
            'status': status
        })
        
        if result['success']:
            results['sent'] += 1
            print(f"  [✓] {client_name} - {service_name} at {hour:02d}:00")
        else:
            results['failed'] += 1
            print(f"  [✗] {client_name} - {service_name} at {hour:02d}:00 - {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {results['sent']} sent, {results['failed']} failed")
    print(f"{'='*60}\n")
    
    return results


def run_scheduler():
    """
    Run the reminder scheduler in a continuous loop.
    Checks for appointments every hour.
    
    Note: For production, consider using a proper task scheduler
    like Celery, APScheduler, or cron jobs.
    """
    import time
    
    print("Starting SMS Reminder Scheduler...")
    print("Press Ctrl+C to stop\n")
    
    check_interval = 3600  # Check every hour
    
    while True:
        try:
            # Process reminders for tomorrow
            results = process_reminders()
            
            # Wait for next check
            print(f"Next check in {check_interval // 60} minutes...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            break
        except Exception as e:
            print(f"Error in scheduler: {e}")
            time.sleep(60)  # Wait 1 minute on error before retrying


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Send appointment reminders')
    parser.add_argument('--remind', action='store_true', 
                       help='Send reminders for tomorrow appointments')
    parser.add_argument('--scheduler', action='store_true',
                       help='Run continuous reminder scheduler')
    parser.add_argument('--db', type=str, 
                       help='Path to database file')
    
    args = parser.parse_args()
    
    if args.scheduler:
        run_scheduler()
    elif args.remind:
        process_reminders(args.db)
    else:
        # Default: send a test message
        print("Sending test confirmation message...")
        result = send_confirmation_sms(
            phone='+27711234567',  # Replace with test number
            client_name='Test Client',
            service_name='Wash & Set',
            date=date.today().isoformat(),
            hour=14,
            staff_name='Sarah'
        )
        print(f"Result: {result}")
