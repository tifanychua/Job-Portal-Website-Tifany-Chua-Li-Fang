Feature: Employer Job Expiry Notification
  As an Employer
  I want to receive notifications before my job postings expire
  So that I can take appropriate action to maintain recruitment continuity.

  Scenario: Employer receives a notification three days before job expiry
    Given an active job will expire in three days
    When the system checks job expiry notifications
    Then a three day expiry notification should be created
    And the notification should link to manage jobs
    And the notification should be unread

  Scenario: Employer receives a notification on the job expiry date
    Given an active job expires today
    When the system checks job expiry notifications
    Then an expiry today notification should be created

  Scenario: Notification contains the job title
    Given an active job will expire in three days
    When the system checks job expiry notifications
    Then the expiry notification message should contain the job title

  Scenario: Duplicate three day notification is not created
    Given an active job will expire in three days
    And the three day expiry notification already exists
    When the system checks job expiry notifications
    Then another three day expiry notification should not be created

  Scenario: Inactive job does not create expiry notification
    Given an inactive job will expire in three days
    When the system checks job expiry notifications
    Then no expiry notification should be created

  Scenario: Job without expiry date does not create notification
    Given an active job does not have an expiry date
    When the system checks job expiry notifications
    Then no expiry notification should be created

  Scenario: Job expiring outside the notification period does not create notification
    Given an active job will expire in five days
    When the system checks job expiry notifications
    Then no expiry notification should be created

  Scenario: Expiry notification belongs to the correct employer
    Given an active job will expire in three days
    When the system checks job expiry notifications
    Then the expiry notification should belong to the job company
