#!/usr/bin/env python3
"""
Belle Madame Salon Online Booking System
Production WSGI Entry Point

This file is used by production servers like Gunicorn.
"""
from app import app

if __name__ == "__main__":
    app.run()
