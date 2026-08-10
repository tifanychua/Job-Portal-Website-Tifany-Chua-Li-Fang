Feature: Job Seeker Application Status Notifications
  As a Job Seeker
  I want to receive notifications on the website whenever my application status changes
  So that I can remain informed throughout the recruitment process.

  Scenario: Receive notification when application status is updated
    Given the job seeker has submitted a job application
    When the employer updates the application status
    Then the system should display a notification to the job seeker indicating the updated application status

  Scenario: View application status notification details
    Given the job seeker has received an application status notification
    When the job seeker clicks on the notification
    Then the system should redirect the job seeker to the application details page showing the updated status

  Scenario: Mark application status notification as read
    Given the job seeker has unread application status notifications
    When the job seeker views the notification
    Then the system should mark the notification as read and update the notification count
