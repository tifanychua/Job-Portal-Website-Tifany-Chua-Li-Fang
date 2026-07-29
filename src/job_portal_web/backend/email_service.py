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


async def send_employer_interview_notification(
    email,
    employer_name,
    candidate_name,
    position,
    status,
    reason=None,
    requested_date=None,
    requested_time=None,
):

    reschedule_text = ""

    if status == "Reschedule Requested":

        reschedule_text = f"""

Requested New Interview Date:
{requested_date}


Requested New Interview Time:
{requested_time}

"""

    reason_text = ""

    if reason:

        reason_text = f"""

Reason:
{reason}

"""

    message = MessageSchema(
        subject=f"Interview Update - {status}",
        recipients=[email],
        body=f"""

Dear {employer_name},


The interview status has been updated by the candidate.


Candidate:
{candidate_name}


Position:
{position}


Status:
{status}


{reschedule_text}


{reason_text}


Please login to JobConnect to view the interview details.


Regards,

JobConnect Team

""",
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)

    await fm.send_message(message)


async def send_interview_rescheduled_email(
    email,
    name,
    interview,
    company_address,
):

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
        subject="Interview Rescheduled - JobConnect",
        recipients=[email],
        body=f"""

Dear {name},

Your interview has been rescheduled by the employer.

Interview Stage:
{interview.stage}

New Interview Date:
{interview.date}

New Interview Time:
{interview.time}

Duration:
{interview.duration}

Interview Type:
{interview.interviewType}

{location_text}

Please attend the interview according to the updated schedule.

Regards,

JobConnect Team

""",
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)

    await fm.send_message(message)


async def send_interview_cancelled_email(
    email,
    name,
    position,
):

    message = MessageSchema(
        subject="Interview Cancelled - JobConnect",
        recipients=[email],
        body=f"""

Dear {name},

We regret to inform you that your scheduled interview has been cancelled by the employer.

Position:
{position}

We sincerely apologize for any inconvenience caused.

You may continue applying for other opportunities through JobConnect.

Regards,

JobConnect Team

""",
        subtype=MessageType.plain,
    )

    fm = FastMail(conf)

    await fm.send_message(message)
