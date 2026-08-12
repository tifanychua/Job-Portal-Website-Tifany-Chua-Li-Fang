Feature: Subscription Payment Processing
  As the system
  I want to process subscription payment events
  So that employer credits and subscription status remain correct.

  Scenario: Checkout completed updates Stripe identifiers
    Given a company exists for the Stripe customer
    When checkout completed is handled
    Then the company Stripe identifiers should be updated

  Scenario: Checkout completed without customer is ignored
    Given checkout data does not contain a customer
    When checkout completed is handled
    Then no company update should occur

  Scenario: Paid starter invoice adds starter credits
    Given a company exists with unused credits
    And Stripe returns a starter subscription
    When a paid invoice is handled
    Then the company should receive starter credits
    And the previous unused credits should become expired
    And a completed card payment should be saved

  Scenario: Paid business invoice adds business credits
    Given a company exists with unused credits
    And Stripe returns a business subscription
    When a paid invoice is handled
    Then the company should receive business credits

  Scenario: Paid enterprise invoice adds enterprise credits
    Given a company exists with unused credits
    And Stripe returns an enterprise subscription
    When a paid invoice is handled
    Then the company should receive enterprise credits

  Scenario: Duplicate completed invoice is ignored
    Given the invoice was already processed successfully
    When the duplicate paid invoice is handled
    Then company credits should not be updated again

  Scenario: Paid invoice without invoice ID is ignored
    Given a paid invoice does not contain an invoice ID
    When the paid invoice is handled
    Then no payment should be saved

  Scenario: Paid invoice without customer is ignored
    Given a paid invoice does not contain a customer
    When the paid invoice is handled
    Then no payment should be saved

  Scenario: Unknown subscription plan is ignored
    Given a company exists for the Stripe customer
    And Stripe returns an unknown subscription plan
    When a paid invoice is handled
    Then the company credits should remain unchanged

  Scenario: Failed invoice changes subscription status
    Given a company exists for the Stripe customer
    When a failed invoice is handled
    Then the company subscription status should become payment failed

  Scenario: Subscription update stores current status
    Given a company exists for the Stripe customer
    When a subscription update is handled
    Then the company subscription status and cancellation flag should be updated

  Scenario: Subscription deletion expires remaining credits
    Given a company exists with remaining credits
    When a subscription deletion is handled
    Then the subscription should be cancelled
    And remaining credits should become expired
