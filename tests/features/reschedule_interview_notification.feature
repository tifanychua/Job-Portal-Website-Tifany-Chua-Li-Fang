Feature: Interview Reschedule Notification


Scenario: Send email notification when interview is rescheduled

    Given the employer has rescheduled an interview
    When the interview schedule is updated
    Then the system should send an email notification to the job seeker with the updated interview details



Scenario: Display updated interview information in email

    Given the job seeker receives a rescheduled interview notification
    When the job seeker opens the email
    Then the system should display the new interview date, time, and other relevant details



Scenario: No notification sent when interview is not changed

    Given the interview schedule remains unchanged
    When no rescheduling action is performed
    Then the system should not send any reschedule notification email