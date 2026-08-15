Feature: View Career Advice Posts

  As a Job Seeker
  I want to view career advice posts
  So that I can gain useful guidance for my career development

  Scenario: View available career advice posts
    Given the job seeker is logged into the system
    When the job seeker accesses the career advice section
    Then the system should display a list of available published career advice posts

  Scenario: View career advice post details
    Given the job seeker is viewing the career advice post list
    When the job seeker selects a career advice post
    Then the system should display the complete post details
    And the details should include the title, content, author, and publication date

  Scenario: Search or filter career advice posts
    Given the job seeker is viewing the career advice section
    When the job seeker searches by keyword or applies a category filter
    Then the system should display career advice posts that match the selected criteria

  Scenario: No career advice posts available
    Given no career advice posts have been published in the system
    When the job seeker accesses the career advice section
    Then the system should display a message indicating that no career advice posts are available