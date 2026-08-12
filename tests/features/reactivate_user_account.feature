Feature: Reactivate User Account

  As an Admin
  I want to reactivate user accounts
  So that eligible users can regain access to the platform

  Scenario: Reactivate a suspended user account
    Given the admin is viewing a suspended user account
    When the admin selects the reactivate option
    Then the system should change the user's account status to "Active"
    And restore the user's access to the platform

  Scenario: Reactivate a deactivated user account
    Given the admin is viewing a deactivated user account
    When the admin selects the reactivate option
    Then the system should change the user's account status to "Active"
    And allow the user to log in again

  Scenario: Confirm successful account reactivation
    Given the admin has selected a user account for reactivation
    When the reactivation process is completed successfully
    Then the system should display a confirmation message indicating that the user account has been successfully reactivated

  Scenario: Record account reactivation activity
    Given the admin has reactivated a user account
    When the account status is updated
    Then the system should record the reactivation activity
    And the record should include the user information, admin action, and date of change