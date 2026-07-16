Feature: Request Reschedule Interview Notification
    As an Employer
    I want to receive an email notification when a job seeker requests to reschedule an interview
    So that I can review the request and adjust the interview schedule accordingly.

    Scenario: Employer receives reschedule request notification
    Given a job seeker submits an interview reschedule request
    When the request is created successfully
    Then the employer should receive a notification about the request

    Scenario: Employer views reschedule request details
    Given the employer has received a reschedule request notification
    When the employer opens the notification
    Then the requested new interview date and time should be displayed