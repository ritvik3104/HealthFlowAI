import requests
from app.core.config import settings

def send_appointment_confirmation(patient_email: str, patient_name: str, doctor_name: str, appointment_time: str):
    """
    Sends a confirmation email to the patient using the Mailgun API.
    """
    if not all([settings.MAILGUN_API_KEY, settings.MAILGUN_DOMAIN, settings.FROM_EMAIL]):
        print("Warning: Mailgun settings are incomplete. Skipping email.")
        return {"success": False, "message": "Email service not configured."}

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
            auth=("api", settings.MAILGUN_API_KEY),
            data={"from": f"Appointment Bot <{settings.FROM_EMAIL}>",
                  "to": [patient_email],
                  "subject": "Your Appointment Confirmation",
                  "html": f"""
                  <html>
                      <body>
                          <h3>Appointment Confirmed!</h3>
                          <p>Dear {patient_name},</p>
                          <p>This is a confirmation that your appointment with <strong>{doctor_name}</strong> has been successfully booked.</p>
                          <p><strong>Time:</strong> {appointment_time}</p>
                          <p>Thank you for using our service.</p>
                      </body>
                  </html>
                  """})
        
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        print(f"Email sent to {patient_email}. Status: {response.status_code}")
        return {"success": True, "message": "Confirmation email sent."}

    except requests.exceptions.RequestException as e:
        print(f"Error sending email via Mailgun: {e}")
        return {"success": False, "message": str(e)}

