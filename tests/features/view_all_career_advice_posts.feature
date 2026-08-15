Feature: View All Career Advice Posts

  As an Admin
  I want to view all career advice posts
  So that I can monitor and manage the available content

  Scenario: View list of all career advice posts
    Given the admin is logged into the admin dashboard
    When the admin accesses the career advice management section
    Then the system should display a list of all career advice posts available in the system

  Scenario: View career advice post details
    Given the admin is viewing the career advice post list
    When the admin selects a specific career advice post
    Then the system should display the complete post details
    And the details should include the title, content, author, publication date, and status

  Scenario: Filter career advice posts
    Given the admin is viewing the career advice management section
    When the admin filters the posts by publication status or date range
    Then the system should display only the career advice posts that match the selected criteria

  Scenario: No career advice posts available
    Given no career advice posts have been created in the system
    When the admin accesses the career advice management section
    Then the system should display a message indicating that no career advice posts are available