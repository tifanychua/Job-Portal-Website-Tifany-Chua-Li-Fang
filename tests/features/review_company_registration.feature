Feature: Review company registration requests

  Scenario: View pending company registration requests
    Given there are one or more pending company registration requests
    When the administrator opens the Company Verification page
    Then the system should display all pending company registration requests


  Scenario: View company registration details
    Given the administrator is viewing a pending company registration request
    When the administrator selects a company
    Then the system should display the company's registration information and supporting documents


  Scenario: No pending company registration requests
    Given there are no pending company registration requests
    When the administrator opens the Company Verification page
    Then the system should display a "No pending company registration requests" message