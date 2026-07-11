Feature: Interview Notification
    As a Job Seeker
    I want to receive interview schedule notifications
    So that I am informed about the interview date, time, and location.

    Scenario: Job seeker receives interview email notification
    Given the employer has successfully scheduled an interview
    When the interview details are saved
    Then the job seeker should receive an interview notification email

    Scenario: Interview notification email contains interview details
    Given the employer has scheduled an interview
    When the notification email is sent
    Then the email should contain the interview date, time, and interview location