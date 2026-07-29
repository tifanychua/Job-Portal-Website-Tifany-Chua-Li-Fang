Feature: Reject company registration

  Scenario: Reject an invalid company registration
    Given the administrator is reviewing a pending company registration request
    When the administrator rejects the registration request
    Then the system should update the company status to "Rejected"
    And the company should not be allowed to access employer features