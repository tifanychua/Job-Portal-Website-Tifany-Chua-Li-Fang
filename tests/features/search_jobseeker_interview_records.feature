Feature: Search Job Seeker Interview Records


Scenario: Search interview records by keyword

Given the job seeker has existing interview records
When the job seeker enters a relevant keyword in the search bar
Then the system should display interview records that match the keyword



Scenario: Search interview records with no matching results

Given the job seeker enters a keyword that does not match any interview record
When the search is performed
Then the system should display a "No interview records found" message



Scenario: Clear interview search

Given the job seeker has performed an interview record search
When the job seeker clears the search keyword
Then the system should display all interview records again