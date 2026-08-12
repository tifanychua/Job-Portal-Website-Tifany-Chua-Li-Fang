Feature: Edit Career Advice Post

  As an Admin
  I want to edit career advice posts
  So that I can keep the information accurate and up to date

  Scenario: Edit an existing career advice post
    Given the admin is viewing the career advice management section
    When the admin selects an existing career advice post and updates its information
    Then the system should save the updated career advice post details

  Scenario: Update a published career advice post
    Given the admin has selected a published career advice post
    When the admin modifies and saves the post content
    Then the system should update the published post with the latest information
    And make the updated information available to job seekers

  Scenario: Validate edited career advice post information
    Given the admin is editing a career advice post
    When the admin submits the changes without the required information
    Then the system should display a validation message requesting the missing details
    And the changes should not be saved

  Scenario: Confirm successful career advice post update
    Given the admin has entered valid changes to a career advice post
    When the changes are saved successfully
    Then the system should display a confirmation message indicating that the post has been updated successfully