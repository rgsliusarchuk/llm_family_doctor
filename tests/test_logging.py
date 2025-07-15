#!/usr/bin/env python
"""Test script to verify logging functionality."""
import csv
import datetime as dt
from pathlib import Path

def test_log_feedback():
    """Test the logging function."""
    feedback_log = Path("logs/doctor_feedback.csv")
    feedback_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Test data
    symptoms = "тест симптоми"
    status = "approved"
    response = "тест відповідь"
    
    try:
        with feedback_log.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [dt.datetime.now().isoformat(), symptoms, status, response]
            )
        print(f"✅ Successfully logged feedback to: {feedback_log.absolute()}")
        return True
    except Exception as e:
        print(f"❌ Error logging feedback: {e}")
        return False

if __name__ == "__main__":
    test_log_feedback() 