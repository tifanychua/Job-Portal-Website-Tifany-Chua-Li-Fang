Feature: Search Interview Records


Scenario: Search interview records by keyword

    Given the employer has existing interview records with job seekers
    When the employer enters a relevant keyword in the search bar
    Then the system should display interview records that match the keyword



Scenario: Search interview records with no matching results

    Given the employer enters a keyword that does not match any interview record
    When the search is performed
    Then the system should display a "No interview records found" message



Scenario: Clear interview search

    Given the employer has performed an interview record search
    When the employer clears the search keyword
    Then the system should display all interview records again