Feature: Deduct Job Posting Credit

  Scenario: Deduct one credit when employer publishes a job post
    Given the employer has available job posting credits
    When the employer successfully publishes a job post
    Then the system should deduct one credit from the employer's credit balance

  Scenario: Prevent job posting when employer has insufficient credits
    Given the employer has no available job posting credits
    When the employer attempts to publish a job post
    Then the system should prevent the publication and display a message indicating insufficient credits

  Scenario: Record credit deduction transaction
    Given one credit has been deducted after a job post is published
    When the admin views the credit usage records
    Then the system should display the credit deduction details including employer information job post details and transaction date