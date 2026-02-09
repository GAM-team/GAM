# Secondary Calendars with no Owner

Here's a start on how to get information for non-owned secondary calendars

Save the CSV file that Google sent you as NoOwnerSecCals.csv

Get calendar description and summary for non-owned secondary calendars.
* There will be one row per calendar.
```
gam config num_threads 10 csv_output_header_force "calendarId,description,summary" redirect csv ./NOSC_Details.csv multiprocess redirect stderr - multiprocess csv NoOwnerSecCals.csv gam calendar "~Secondary calendar email" print settings fields description,summary
```

Get event counts for non-owned secondary calendars.
* There will be one row per calendar.
```
gam config num_threads 10 redirect csv ./NOSC_EventCounts.csv multiprocess redirect stderr - multiprocess csv NOSC_Details.csv gam calendar "~calendarId" print events countsonly addcsvdata description "~description" addcsvdata summary "~summary"
```

Get summary for non-owned secondary calendars - Contains details, counts, ACLs
* There will be one row per calendar/ACL combination
```
gam config num_threads 10 redirect csv ./NOSC_Summary.csv multiprocess redirect stderr - multiprocess csv NOSC_EventCounts.csv gam calendar "~calendarId" print acls noselfowner addcsvdata description "~description" addcsvdata summary "~summary" addcsvdata events "~events"
```

You can add an owner.
* Replace `admin@domain.com` with the super admin from: `gam oauth info`
```
gam config num_threads 10 redirect stdout ./Add_NOSC_Owner.txt multiprocess redirect stderr stdout csv NoOwnerSecCals.csv gam calendar "~Secondary calendar email" add acls owner admin@domain.com
```
After inspecting NOSC_Summary.csv, you can delete the calendars if desired.
* Replace `admin@domain.com` with the super admin from: `gam oauth info`
```
gam config num_threads 10 redirect stdout ./Delete_NOSC.txt multiprocess redirect stderr stdout csv NoOwnerSecCals.csv gam user admin@domain.com remove calendar "~Secondary calendar email"
``