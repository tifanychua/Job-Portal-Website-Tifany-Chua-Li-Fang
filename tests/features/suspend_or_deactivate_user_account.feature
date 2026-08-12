Feature: Suspend or Deactivate User Account

  As an Admin
  I want to suspend or deactivate user accounts
  So that I can prevent misuse of the platform

  Scenario: Suspend a user account
    Given the admin is viewing the user management section
    When the admin selects an active user account and chooses the suspend option
    Then the system should change the user's account status to "Suspended"
    And restrict the user's access to the platform

  Scenario: Deactivate a user account
    Given the admin is viewing the user management section
    When the admin selects an active user account and chooses the deactivate option
    Then the system should change the user's account status to "Deactivated"
    And prevent the user from accessing the platform features

  Scenario: Restore a suspended or deactivated account
    Given a user account has been suspended or deactivated
    When the admin chooses to reactivate the user account
    Then the system should change the account status to "Active"
    And allow the user to access the platform again

  Scenario: Record account status changes
    Given the admin has suspended or deactivated a user account
    When the account status is updated
    Then the system should record the account status change
    And the record should include the user information, action performed, and date of change