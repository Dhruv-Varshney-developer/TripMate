"""
Invoice Generation Module for TripMate

Handles the generation of invoices for completed bookings
"""

from typing import Dict, Optional
import os
from datetime import datetime

class InvoiceGenerator:
    """
    Generates invoices for travel bookings
    """
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize the invoice generator
        
        Args:
            template_path: Path to the invoice template file (optional)
        """
        self.template_path = template_path
        self.output_dir = os.path.join(os.getcwd(), "invoices")
        
        # Create invoices directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate(self, booking_details: Dict) -> str:
        """
        Generate an invoice based on booking details
        
        Args:
            booking_details: Dictionary containing booking information
            
        Returns:
            Path to the generated invoice file
        """
        # Generate a unique invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create the invoice file path
        invoice_path = os.path.join(self.output_dir, f"{invoice_number}.txt")
        
        # In a real implementation, this would use a template engine
        # and create a PDF or HTML invoice
        with open(invoice_path, 'w') as f:
            f.write(f"INVOICE #{invoice_number}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # Write customer details
            if "customer" in booking_details:
                f.write("CUSTOMER DETAILS:\n")
                customer = booking_details.get("customer", {})
                f.write(f"Name: {customer.get('name', 'N/A')}\n")
                f.write(f"Email: {customer.get('email', 'N/A')}\n")
                f.write(f"Phone: {customer.get('phone', 'N/A')}\n\n")
            
            # Write booking details
            f.write("BOOKING DETAILS:\n")
            f.write(f"Booking ID: {booking_details.get('booking_id', 'N/A')}\n")
            f.write(f"Travel Type: {booking_details.get('travel_type', 'N/A')}\n")
            
            # If it's a flight booking
            if booking_details.get('travel_type') == 'flight':
                flight = booking_details.get('flight', {})
                f.write(f"Airline: {flight.get('airline', 'N/A')}\n")
                f.write(f"Flight Number: {flight.get('flight_number', 'N/A')}\n")
                f.write(f"From: {flight.get('departure', 'N/A')}\n")
                f.write(f"To: {flight.get('destination', 'N/A')}\n")
                f.write(f"Departure Date: {flight.get('departure_date', 'N/A')}\n")
                f.write(f"Departure Time: {flight.get('departure_time', 'N/A')}\n")
                f.write(f"Arrival Date: {flight.get('arrival_date', 'N/A')}\n")
                f.write(f"Arrival Time: {flight.get('arrival_time', 'N/A')}\n")
            
            # Write payment details
            f.write("\nPAYMENT DETAILS:\n")
            f.write(f"Total Amount: {booking_details.get('total_amount', 'N/A')}\n")
            f.write(f"Payment Method: {booking_details.get('payment_method', 'N/A')}\n")
            f.write(f"Payment Status: {booking_details.get('payment_status', 'Pending')}\n\n")
            
            f.write("=" * 50 + "\n")
            f.write("Thank you for using TripMate for your travel needs!\n")
        
        return invoice_path 