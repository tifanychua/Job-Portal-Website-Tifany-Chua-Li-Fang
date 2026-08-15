Feature: Employer Interview Notifications
  As an Employer
  I want to view interview notifications on the website
  So that I can stay informed about interview updates and take appropriate actions during the recruitment process.

  Scenario: Receive interview notification
    Given the employer has scheduled an interview with a candidate
    When the interview information is changed
    Then the system should display a notification to the employer regarding the interview update

  Scenario: View interview notification details
    Given the employer has received an interview notification
    When the employer clicks on the notification
    Then the system should display the interview details including candidate information, interview date, time, and status

  Scenario: Mark interview notification as read
    Given the employer has unread interview notifications
    When the employer views the notification
    Then the system should mark the notification as read and update the notification count

  Scenario: No interview notifications available
    Given the employer has no interview updates
    When the employer accesses the notification section
    Then the system should display a message indicating that no interview notifications are available
