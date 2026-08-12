Feature: Employer New Application Notifications
  As an Employer
  I want to receive notifications on the website when new job applications are submitted
  So that I can respond to candidates promptly.

  Scenario: Receive notification when a new application is submitted
    Given the employer has posted an active job vacancy
    When a job seeker submits an application for the vacancy
    Then the system should display a notification to the employer indicating a new application has been received

  Scenario: View new application notification details
    Given the employer has received a new application notification
    When the employer clicks on the notification
    Then the system should redirect the employer to the applications page for that applicant

  Scenario: Notification count updates after viewing application
    Given the employer has unread application notifications
    When the employer views the new application
    Then the system should mark the notification as read and update the notification count
