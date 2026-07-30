Feature: Delete Education

  Scenario: Successfully delete an education record
    Given an education record exists for the job seeker
    When the job seeker deletes the education record
    Then the system should redirect the job seeker to the Manage Education page

  Scenario: Delete a non-existing education record
    Given the education record does not exist
    When the job seeker attempts to delete the education record
    Then the system should handle the request appropriately