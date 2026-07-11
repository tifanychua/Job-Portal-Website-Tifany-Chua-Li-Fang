from fastapi_mail import FastMail, MessageSchema, MessageType
from .email_config import conf


async def send_interview_email(email, name, interview, company_address):

    location_text = ""

    if interview.interviewType == "online":

        location_text = f"""
Meeting Link:
{interview.meetingLink}
"""

    elif interview.interviewType == "physical":

        location_text = f"""
Company Address:
{company_address}
"""

    message = MessageSchema(
        subject="Interview Scheduled - JobConnect",
        recipients=[email],
        body=f"""

Dear {name},

Your interview has been scheduled.

Interview Stage:
{interview.stage}

Date:
{interview.date}

Time:
{interview.time}

Duration:
{interview.duration}

Interview Type:
{interview.interviewType}

{location_text}

Regards,
JobConnect Team

""",
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)

    await fm.send_message(message)
