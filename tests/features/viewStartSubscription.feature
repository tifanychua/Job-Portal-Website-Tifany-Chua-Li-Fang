Feature: View and Start Subscription Plan
  As an Employer
  I want to view and select a subscription plan
  So that I can purchase job posting credits.

  Scenario: Employer views subscription plans
    Given an employer company exists
    When the employer opens the subscription plans page
    Then the system should display all available subscription plans

  Scenario: Current subscription plan is identified
    Given an employer company has a business subscription
    When the employer opens the subscription plans page
    Then the business plan should be identified as the current plan

  Scenario: Employer starts a valid subscription
    Given an employer company has no Stripe subscription
    And the starter Stripe price is configured
    When the employer starts the starter subscription
    Then Stripe Checkout should be created using card payment
    And the employer should be redirected to Stripe Checkout

  Scenario: Stripe customer is created when company has no customer ID
    Given an employer company has no Stripe customer
    And the starter Stripe price is configured
    When the employer starts the starter subscription
    Then a Stripe customer should be created
    And the Stripe customer ID should be saved to the company

  Scenario: Existing Stripe customer is reused
    Given an employer company already has a Stripe customer
    And the starter Stripe price is configured
    When the employer starts the starter subscription
    Then the existing Stripe customer should be used

  Scenario: Invalid subscription plan is rejected
    Given an employer company exists
    When the employer starts an invalid subscription plan
    Then plan not found should be returned

  Scenario: Missing Stripe price ID is rejected
    Given an employer company exists
    And the starter Stripe price is not configured
    When the employer starts the starter subscription
    Then Stripe price configuration error should be returned

  Scenario: Existing subscription cannot start another first subscription
    Given an employer company already has a Stripe subscription
    And the starter Stripe price is configured
    When the employer starts the starter subscription
    Then the employer should be redirected back to subscription plans
