Feature: Stripe Webhook
  As the system
  I want to process Stripe webhook events
  So that subscription and payment changes are handled automatically.

  Scenario: Valid checkout completed webhook
    Given a valid Stripe webhook secret is configured
    And Stripe returns a checkout completed event
    When the Stripe webhook is processed
    Then the checkout completed handler should be called
    And the webhook response should confirm receipt

  Scenario: Valid invoice paid webhook
    Given a valid Stripe webhook secret is configured
    And Stripe returns an invoice paid event
    When the Stripe webhook is processed
    Then the invoice paid handler should be called

  Scenario: Valid invoice failed webhook
    Given a valid Stripe webhook secret is configured
    And Stripe returns an invoice failed event
    When the Stripe webhook is processed
    Then the invoice failed handler should be called

  Scenario: Valid subscription updated webhook
    Given a valid Stripe webhook secret is configured
    And Stripe returns a subscription updated event
    When the Stripe webhook is processed
    Then the subscription updated handler should be called

  Scenario: Valid subscription deleted webhook
    Given a valid Stripe webhook secret is configured
    And Stripe returns a subscription deleted event
    When the Stripe webhook is processed
    Then the subscription deleted handler should be called

  Scenario: Unknown webhook event
    Given a valid Stripe webhook secret is configured
    And Stripe returns an unknown event
    When the Stripe webhook is processed
    Then no subscription handler should be called
    And the webhook response should confirm receipt

  Scenario: Webhook secret is missing
    Given the Stripe webhook secret is missing
    When the Stripe webhook is processed expecting an error
    Then the webhook should return a configuration error

  Scenario: Stripe payload is invalid
    Given a valid Stripe webhook secret is configured
    And Stripe rejects the webhook payload
    When the Stripe webhook is processed expecting an error
    Then the webhook should return invalid payload

  Scenario: Stripe signature is invalid
    Given a valid Stripe webhook secret is configured
    And Stripe rejects the webhook signature
    When the Stripe webhook is processed expecting an error
    Then the webhook should return invalid signature
