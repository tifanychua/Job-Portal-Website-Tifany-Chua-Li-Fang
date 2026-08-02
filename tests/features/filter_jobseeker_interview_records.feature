Feature: Filter Job Seeker Interview Records


Scenario: Filter interview records by status

Given the job seeker has interview records with different statuses
When the job seeker selects an interview status filter
Then the system should display only interview records matching the selected status



Scenario: View all interview records without applying status filter

Given the job seeker is viewing the interview records page
When the job seeker does not select any status filter
Then the system should display all interview records



Scenario: No interview records found for selected status

Given the job seeker applies a status filter
When no interview records match the selected status
Then the system should display a "No interview records found" message