Feature: Change Subscription Plan

  Scenario: Employer changes to another valid subscription plan
    Given the employer currently uses the starter plan
    And an active Stripe subscription exists
    When the employer changes to the business plan
    Then Stripe should modify the subscription to the business plan
    And proration should be applied to the plan change
    And the employer should be redirected while the plan change is processing

  Scenario: Employer cannot change to the current subscription plan
    Given the employer currently uses the starter plan
    When the employer changes to the starter plan
    Then the employer should be redirected back to subscription plans

  Scenario: Employer changes plan without an active Stripe subscription
    Given the employer currently uses the starter plan without a Stripe subscription
    When the employer changes to the business plan
    Then starting a Stripe subscription first should be required

  Scenario: Employer changes to an invalid subscription plan
    Given the employer currently uses the starter plan
    When the employer changes to an invalid plan
    Then plan not found should be returned