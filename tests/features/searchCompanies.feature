Feature: Search Companies

  Scenario: Search companies by company name
    Given the job seeker is viewing the company search section
    When the job seeker searches for company name "ABC Technology"
    Then the system should display companies that match the entered company name

  Scenario: Search companies by keyword
    Given the job seeker is viewing the company search section
    When the job seeker searches for keyword "Technology"
    Then the system should display companies that match the entered keyword

  Scenario: Company search is case insensitive
    Given the job seeker is viewing the company search section
    When the job seeker searches using lowercase company name
    Then the matching company should still be displayed

  Scenario: Company search supports partial company name
    Given the job seeker is viewing the company search section
    When the job seeker searches using a partial company name
    Then companies containing the partial company name should be displayed

  Scenario: Search results contain only matching companies
    Given multiple active companies exist
    When the job seeker searches for "Technology"
    Then companies unrelated to the search keyword should not be displayed

  Scenario: Inactive companies are not displayed in search results
    Given an inactive company matches the search keyword
    When the job seeker searches for that company
    Then the inactive company should not be displayed

  Scenario: View company details from search results
    Given the job seeker has received company search results
    When the job seeker selects a company from the search results
    Then the system should provide access to the selected company's details

  Scenario: Company search result contains company information
    Given the job seeker has received company search results
    When the matching company is displayed
    Then the search result should contain company name industry location and available job count

  Scenario: No matching companies found
    Given the job seeker has entered a company name or keyword
    When no companies match the search criteria
    Then the system should return an empty company result

  Scenario: No matching companies can display an empty state
    Given no companies match the current search
    When the company search page is rendered
    Then the page should have no company cards available

  Scenario: Clear company search
    Given the job seeker has entered search criteria
    When the job seeker clears the search field
    Then the system should display the default company listing

  Scenario: Search with leading and trailing spaces
    Given the job seeker is viewing the company search section
    When the job seeker searches with spaces around the keyword
    Then the spaces should be ignored when searching

  Scenario: Empty search keyword
    Given the job seeker is viewing the company search section
    When the job seeker submits an empty search
    Then the system should display the default company listing

  Scenario: Search result provides company details link
    Given the job seeker has received company search results
    When the company search result is prepared
    Then each company result should contain its company ID