Feature: Accept Interview Notification
    As an Employer
    I want to receive an email notification when a job seeker accepts an interview invitation
    So that I can confirm the interview acceptance and proceed with the recruitment process.

    Scenario: Job seeker receives interview email notification
    Given the employer has successfully scheduled an interview
    When the interview details are saved
    Then the job seeker should receive an interview notification email

    Scenario: Interview notification email contains interview details
    Given the employer has scheduled an interview
    When the notification email is sent
    Then the email should contain the interview date, time, and interview location