Feature: Save Career Advice Post as Draft

  As an Admin
  I want to save unfinished career advice posts as drafts
  So that I can continue editing them later

  Scenario: Save an unfinished career advice post as a draft
    Given the admin is creating a new career advice post
    When the admin selects the save as draft option
    Then the system should save the post with a "Draft" status

  Scenario: View saved draft career advice posts
    Given the admin has saved one or more draft career advice posts
    When the admin accesses the career advice management section
    Then the system should display the list of saved draft posts

  Scenario: Continue editing a draft career advice post
    Given the admin has a saved draft career advice post
    When the admin selects the draft post
    Then the system should display the draft content
    And allow the admin to continue editing it

  Scenario: Publish a draft career advice post
    Given the admin has completed editing a draft career advice post
    When the admin selects the publish option
    Then the system should change the post status from "Draft" to "Published"
    And make the post available to job seekers