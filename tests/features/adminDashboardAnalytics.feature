Feature: Admin dashboard analytics

  As an administrator
  I want to view platform analytics
  So that I can monitor users, jobs, applications and transactions

  Scenario: Administrator views dashboard analytics
    Given analytics test records are available
    And the requester is logged in as an administrator
    When the requester retrieves the dashboard analytics
    Then the dashboard metrics and charts should be returned

  Scenario: Administrator views current-year revenue
    Given analytics test records are available
    And the requester is logged in as an administrator
    When the requester retrieves the dashboard analytics
    Then the current-year revenue should be calculated correctly

  Scenario: Non-administrator accesses dashboard analytics
    Given the requester is not logged in as an administrator
    When the requester retrieves the dashboard analytics
    Then access to the dashboard analytics should be denied