Feature: Preview and Change Subscription Plan
  As an Employer
  I want to preview and change my subscription plan
  So that I know the amount charged before confirming the change.

  Scenario: Employer previews a valid plan change
    Given the employer currently uses the starter plan
    And an active Stripe subscription exists
    When the employer previews the business plan
    Then the preview should display the business plan information
    And Stripe amounts should be converted from cents
    And the saved card should be displayed

  Scenario: Proration credit is calculated
    Given the employer currently uses the starter plan
    And an active Stripe subscription exists
    When the employer previews the business plan with an unused subscription credit
    Then the negative proration adjustment should be returned

  Scenario: Invalid preview plan is rejected
    Given the employer currently uses the starter plan
    When the employer previews an invalid plan
    Then plan not found should be returned

  Scenario: Employer cannot preview the current plan
    Given the employer currently uses the starter plan
    When the employer previews the starter plan
    Then current plan preview should be rejected

  Scenario: Preview requires an active Stripe subscription
    Given the employer currently uses the starter plan without a Stripe subscription
    When the employer previews the business plan
    Then missing Stripe subscription should be returned

  Scenario: Preview requires a Stripe subscription item
    Given the employer currently uses the starter plan
    And a Stripe subscription without items exists
    When the employer previews the business plan
    Then missing subscription item should be returned

  Scenario: Employer changes to another valid plan
    Given the employer currently uses the starter plan
    And an active Stripe subscription exists
    When the employer changes to the business plan
    Then Stripe should modify the subscription with proration
    And the employer should be redirected while the plan change is processing

  Scenario: Employer cannot change to the same plan
    Given the employer currently uses the starter plan
    When the employer changes to the starter plan
    Then the employer should be redirected back to subscription plans

  Scenario: Plan change requires Stripe subscription
    Given the employer currently uses the starter plan without a Stripe subscription
    When the employer changes to the business plan
    Then starting a Stripe subscription first should be required
