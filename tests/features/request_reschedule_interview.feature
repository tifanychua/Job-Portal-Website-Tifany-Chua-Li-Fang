Feature: Request Reschedule Interview
    As a Job Seeker
    I want to request to reschedule an interview
    So that I can propose a different date or time when I am unavailable.

    Scenario: Job seeker requests to reschedule an interview
    Given the job seeker has a scheduled interview
    When the job seeker selects a new preferred date and time
    And submits the reschedule request
    Then the reschedule request should be sent to the employer

    Scenario: Save reschedule request
    Given the job seeker has submitted a reschedule request
    When the system processes the request
    Then the reschedule request details should be saved in the database