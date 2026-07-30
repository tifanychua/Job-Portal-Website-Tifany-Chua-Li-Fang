Feature: Delete Experience

  Scenario: Successfully delete a work experience record
    Given a work experience record exists for the job seeker
    When the job seeker deletes the work experience record
    Then the system should redirect the job seeker to the Manage Experience page

  Scenario: Delete a non-existing work experience record
    Given the work experience record does not exist
    When the job seeker attempts to delete the work experience record
    Then the system should handle the request appropriately