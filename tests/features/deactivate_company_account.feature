Feature: Deactivate Company Account

  As an Admin,
  I want to deactivate companies that violate platform policies,
  so that the integrity and security of the recruitment platform are maintained.


  Scenario: Deactivate a company account
    Given the administrator is viewing a verified company account
    When the administrator deactivates the company account
    Then the system should update the company status to "Deactivated"
    And the company should no longer have access to employer features


  Scenario: View deactivated company accounts
    Given one or more company accounts have been deactivated
    When the administrator views the company management page
    Then the system should display all deactivated company accounts along with their deactivation reasons