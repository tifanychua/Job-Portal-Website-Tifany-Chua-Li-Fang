Feature: Subscribe to Job Posting Credit Plan

  Scenario: Subscribe to job posting credit plan successfully
    Given the employer has selected a job posting credit plan
    When the employer completes the subscription payment successfully
    Then the system should activate the selected subscription plan
    And the system should add the plan credits to the employer's account balance

  Scenario: Subscription payment information is securely processed
    Given the employer is subscribing to a job posting credit plan
    When the employer proceeds to payment
    Then the system should process the payment securely through Stripe Checkout using card payment
    And the system should not directly expose or store sensitive card information

  Scenario: Subscription payment fails
    Given the employer has selected a job posting credit plan
    When the subscription payment is unsuccessful
    Then the system should mark the subscription payment as unsuccessful
    And the system should not add the plan credits to the employer's account balance

  Scenario: View updated credit balance after successful subscription
    Given the employer has successfully subscribed to a job posting credit plan
    When the employer views the credit management page
    Then the system should display the updated job posting credit balance

  Scenario: Existing Stripe customer subscribes to a plan
    Given the employer already has a Stripe customer account
    And the employer has selected a job posting credit plan
    When the employer proceeds with the subscription
    Then the system should reuse the existing Stripe customer for the subscription

  Scenario: New Stripe customer subscribes to a plan
    Given the employer does not have a Stripe customer account
    And the employer has selected a job posting credit plan
    When the employer proceeds with the subscription
    Then the system should create a Stripe customer for the employer
    And the Stripe customer ID should be saved to the employer account