Feature: Manage Employer Subscription
  As an Employer
  I want to cancel, resume, and manage my subscription payment method
  So that I can control my subscription.

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

  Scenario: Employer resumes scheduled subscription
    Given an employer has a Stripe subscription scheduled for cancellation
    When the employer resumes the subscription
    Then Stripe should remove scheduled cancellation
    And the cancellation flag should be cleared
    And the employer should be redirected after resuming

  Scenario: Resume requires a subscription
    Given an employer has no Stripe subscription
    When the employer resumes the subscription
    Then no subscription error should be returned

  Scenario: Employer opens Stripe payment method portal
    Given an employer has a Stripe customer
    When the employer manages the payment method
    Then a Stripe billing portal session should be created
    And the employer should be redirected to the Stripe billing portal

  Scenario: Payment method management requires Stripe customer
    Given an employer has no Stripe customer
    When the employer manages the payment method
    Then Stripe customer not found should be returned

  Scenario: Stripe billing portal failure is handled
    Given an employer has a Stripe customer
    And Stripe fails to create the billing portal
    When the employer manages the payment method
    Then the Stripe billing portal error should be returned
