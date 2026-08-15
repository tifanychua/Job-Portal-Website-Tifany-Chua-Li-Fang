Feature: Job Seeker Application History
  As a Job Seeker
  I want to view my application history
  So that I can monitor the progress and status of each application.

  Scenario: View submitted job applications
    Given the job seeker has submitted one or more job applications
    When the job seeker accesses the application history section
    Then the system should display a list of all submitted job applications

  Scenario: View application status details
    Given the job seeker is viewing the application history list
    When the job seeker selects a specific application
    Then the system should display the application details including job position, company information, submission date, and current application status

  Scenario: Track application progress
    Given the job seeker has submitted a job application
    When the employer updates the application status
    Then the system should update and display the latest application status in the job seeker's application history

  Scenario: No application history available
    Given the job seeker has not submitted any job applications
    When the job seeker accesses the application history section
    Then the system should display a message indicating that no application records are available
