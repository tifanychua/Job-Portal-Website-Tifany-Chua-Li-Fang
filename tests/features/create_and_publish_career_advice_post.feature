Feature: Create and Publish Career Advice Post

  As an Admin
  I want to create and publish career advice posts
  So that I can provide useful career guidance to job seekers

  Scenario: Create a career advice post
    Given the admin is logged into the admin dashboard
    When the admin enters the career advice post details and submits the form
    Then the system should create a new career advice post
    And save the post information in the database

  Scenario: Publish a career advice post
    Given the admin has created a career advice post
    When the admin selects the publish option
    Then the system should update the post status to "Published"
    And make the post available for job seekers to view

  Scenario: Validate career advice post information
    Given the admin is creating a career advice post
    When the admin submits the post without the required information
    Then the system should display a validation message requesting the missing details
    And the career advice post should not be published

  Scenario: View published career advice posts
    Given the admin has successfully published a career advice post
    When the admin accesses the career advice management section
    Then the system should display the published post with its current status