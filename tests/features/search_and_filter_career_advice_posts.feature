Feature: Search and Filter Career Advice Posts

  As a Job Seeker
  I want to search and filter career advice posts
  So that I can quickly find relevant advice

  Scenario: Search career advice posts by keyword
    Given the job seeker is viewing the career advice section
    When the job seeker enters a keyword in the search bar
    Then the system should display career advice posts that match the keyword

  Scenario: Filter career advice posts by category
    Given the job seeker is viewing the career advice section
    When the job seeker selects a specific category filter
    Then the system should display only career advice posts that belong to the selected category

  Scenario: Apply multiple criteria to career advice posts
    Given the job seeker is viewing the career advice section
    When the job seeker applies multiple search and filter criteria
    Then the system should display career advice posts that match all selected criteria

  Scenario: No matching career advice posts found
    Given the job seeker has entered search criteria or applied filters
    When no career advice posts match the selected criteria
    Then the system should display a message indicating that no relevant career advice posts are available

  Scenario: Clear search and filter criteria
    Given the job seeker has applied search criteria or filters
    When the job seeker clears all search and filter options
    Then the system should display all available career advice posts