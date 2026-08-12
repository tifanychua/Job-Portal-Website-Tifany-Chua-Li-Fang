Feature: Job Seeker Interview Status Update Notifications
  As a Job Seeker
  I want to receive interview status update notifications on the website
  So that I can stay informed about the progress of my interviews throughout the recruitment process.

  Scenario: Receive notification when interview status is updated
    Given the job seeker has an ongoing interview process
    When the employer updates the interview status
    Then the system should display a notification to the job seeker indicating the updated interview status

  Scenario: View interview status notification details
    Given the job seeker has received an interview status notification
    When the job seeker clicks on the notification
    Then the system should display the interview details including company name, job position, interview date, and updated status

  Scenario: Mark interview status notification as read
    Given the job seeker has unread interview status notifications
    When the job seeker views the notification
    Then the system should mark the notification as read and update the notification count

  Scenario: No interview status updates available
    Given the job seeker has no interview status updates
    When the job seeker accesses the notification section
    Then the system should display a message indicating that no interview updates are available
