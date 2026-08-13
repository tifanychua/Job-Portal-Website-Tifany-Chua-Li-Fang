Feature: View Subscription Plans

  Scenario: View available subscription plans
    Given the employer company exists
    When the employer opens the subscription plans page
    Then the system should display all available subscription plans

  Scenario: View subscription plan details
    Given the employer company exists
    When the employer opens the subscription plans page
    Then each subscription plan should display its price and number of job posting credits

  Scenario: View current subscription plan
    Given the employer currently has a business subscription
    When the employer opens the subscription plans page
    Then the business subscription should be identified as the current plan