Feature: Send Interview Cancellation Notification

    As a Job Seeker
    I want to receive an email notification when an interview is cancelled
    So that I can be informed about the cancellation and adjust my schedule accordingly.


    Scenario: Send email notification when interview is cancelled
        Given the employer has cancelled a scheduled interview
        When the interview status is updated to "Cancelled"
        Then the system should send a cancellation email notification to the job seeker


    Scenario: Display cancelled interview details in email
        Given the job seeker has received an interview cancellation email
        When the job seeker opens the email
        Then the system should display the cancelled interview details and cancellation information


    Scenario: No cancellation email sent when interview is not cancelled
        Given the interview status is not "Cancelled"
        When no cancellation action is performed
        Then the system should not send any cancellation email notification