Feature: View Application Status
As a Job Seeker
I want to monitor the status of my applications
So that I remain informed throughout the recruitment process.

Scenario: Job seeker views application status
    Given the job seeker has submitted job applications
    When the job seeker opens the application status page
    Then the system should display the current status of each application

Scenario: Job seeker views updated application status
    Given an employer has updated an application status
    When the job seeker views the application details
    Then the updated application status should be displayed