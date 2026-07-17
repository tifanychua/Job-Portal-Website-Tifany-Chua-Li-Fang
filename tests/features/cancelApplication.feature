Feature: Withdraw Job Application
As a Job Seeker
I want to withdraw my application before the recruitment process is completed
So that I can manage my job search effectively.

  Scenario: Job seeker withdraws a submitted application
    Given the job seeker has submitted a job application
    When the job seeker selects the withdraw application option
    Then the application status should be updated to "Cancelled"

  Scenario: Save withdrawn application status
    Given the job seeker has withdrawn an application
    When the withdrawal request is processed
    Then the updated application status should be saved in the database