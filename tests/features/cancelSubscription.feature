Feature: Cancel Employer Subscription

  As an Employer
  I want to cancel my current subscription plan
  So that I can stop the subscription from renewing after the current billing period.

  Scenario: Employer schedules subscription cancellation
    Given an employer has an active Stripe subscription
    When the employer cancels the subscription
    Then Stripe should schedule cancellation at period end
    And the cancellation flag should be saved
    And the employer should be redirected to the credit page

  Scenario: Cancellation requires an active subscription
    Given an employer has no Stripe subscription
    When the employer cancels the subscription
    Then no active subscription error should be returned

  Scenario: Stripe cancellation failure is handled
    Given an employer has an active Stripe subscription
    And Stripe fails to cancel the subscription
    When the employer cancels the subscription
    Then the Stripe cancellation error should be returned