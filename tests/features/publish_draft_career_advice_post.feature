Feature: Publish Draft Career Advice Post

  As an Admin
  I want to publish a completed draft career advice post
  So that job seekers can access and view the post.

  Scenario: Publish a completed draft career advice post
    Given the admin has a completed draft career advice post
    When the admin selects the publish option
    Then the post status should be updated from "Draft" to "Published"

  Scenario: Save the published career advice post
    Given the admin has published a valid draft career advice post
    When the system processes the publishing request
    Then the updated post status should be saved in the database

  Scenario: Make the published post available to job seekers
    Given the career advice post has been successfully published
    When a job seeker accesses the career advice section
    Then the published post should be displayed and available for viewing

  Scenario: Validate draft content before publishing
    Given the admin is attempting to publish a draft career advice post
    When the draft is missing required information
    Then the system should display a validation message
    And the post should remain in "Draft" status

  Scenario: Confirm successful publication
    Given the admin has selected the publish option for a valid draft
    When the publishing process is completed successfully
    Then the system should display a successful publication confirmation message