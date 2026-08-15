Feature: Job Seeker Unread Notifications
  As a job seeker
  I want to view notifications in a separate Unread section
  So that I can quickly identify which notifications I have not read.

  Scenario: View all notifications
    Given the job seeker has both read and unread notifications
    When the job seeker opens the All section
    Then the system should display both read and unread notifications

  Scenario: View unread notifications
    Given the job seeker has both read and unread notifications
    When the job seeker opens the Unread section
    Then the system should display only unread notifications
    And read notifications should not appear in the Unread section

  Scenario: Display unread notifications clearly
    Given the job seeker is viewing the notification list
    When the list contains unread notifications
    Then unread notifications should be visually distinguishable from read notifications

  Scenario: Mark an unread notification as read
    Given the job seeker is viewing the Unread section
    And an unread notification is displayed
    When the job seeker opens the notification
    Then the system should mark the notification as read
    And remove it from the Unread section
    And keep it available in the All section

  Scenario: Update unread notification count
    Given the job seeker has unread notifications
    When an unread notification is marked as read
    Then the unread notification count should decrease by one

  Scenario: Preserve notification status after refresh
    Given the job seeker has opened an unread notification
    And the notification has been marked as read
    When the job seeker refreshes the notification page
    Then the notification should remain marked as read
    And it should not reappear in the Unread section

  Scenario: No unread notifications available
    Given the job seeker has no unread notifications
    When the job seeker opens the Unread section
    Then the system should display a message indicating that there are no unread notifications

  Scenario: Receive a new unread notification
    Given the job seeker has received a new notification
    When the notification appears in the system
    Then the notification should initially be marked as unread
    And the unread notification count should increase by one
