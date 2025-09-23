- [Bulk Operations](#bulk-operations)
- [Bulk Operations With GAM 3.2 and Newer](#bulk-operations-with-gam-32-and-newer)
  - [Using CSV Files](#using-csv-files)
  - [Using A Text File to Batch Run GAM Commands](#using-a-text-file-to-batch-run-gam-commands)
  - [Determining How Many GAM Commands Run In Parallel](#determining-how-many-gam-commands-run-in-parallel)
- [Old OS-Specific Methods](#old-os-specific-methods)
  - [Bulk Operations on Windows](#bulk-operations-on-windows)
  - [Bulk Operations on Linux](#bulk-operations-on-linux)
- [Avoid prompts to update GAM](#avoid-prompts-to-update-gam)

# Bulk Operations

Sometimes you want to make changes to many accounts all at once.  Commands that relate to user's email settings support bulk operations.  So you can run:

```
gam all users imap on
```

to turn on IMAP for all users.  However, other commands deal with the specifics of a user's account, you probably don't want to update all of users with the same password.  You can use CSV files along with some command line magic to get GAM to perform bulk operations.

# Bulk Operations With GAM 3.2 and Newer
## Using CSV Files
If you have a CSV file of changes to be made or objects to change, GAM can read the CSV file and make the changes in bulk. The basic format of a GAM CSV command is:
```
gam csv <csv-filename> gam <regular command>
```
So let's say you have a CSV file called passwords.csv that looks like:
```
Email,Password
jsmith@acme.com,ChewieWookie
hsmith@acme.com,HansSolo
rsmith@acme.com,LukeSkywalker
```
you can run the command:
```
gam csv passwords.csv gam update user ~Email password ~Password
```
notice the arguments starting with ~. For these arguments, GAM substitutes in the value from the CSV row. So running this command would be equivalent to running the following:
```
gam update user jsmith@acme.com password ChewieWookie
gam update user hsmith@acme.com password HansSolo
gam update user rsmith@acme.com password LukeSkywalker
```
~ substitutions are case-sensitive so make sure you enter them exactly as they are in the CSV header.

Note also that you can use [shell pipes](https://en.wikipedia.org/wiki/Pipeline_(Unix)) and a special CSV file called - to dynamically create CSVs from one GAM command and take action on the results in another GAM command. Let's say for instance that you wanted to turn IMAP off for all accounts in and under the /Students OU. Try:
```
gam print users query "orgUnitPath='/Students'" | gam csv - gam update user ~primaryEmail imap off
```

or if you wanted to force every single user in the domain to change their password:
```
gam print users | gam csv - gam update user ~primaryEmail changepassword on
```

or if you wanted to prevent regular member users from leaving any of your Google Groups:
```
gam print groups | gam csv - gam update group ~Email who_can_leave_group ALL_MANAGERS_CAN_LEAVE
```

When GAM sees an argument named something like:

~Variable

it will replace the entire argument with the Variable column value from the CSV row.

\~\~Variable\~\~ is partial replacement. So if you used:

"/Students/\~\~Description\~\~" it should combine /Students/ with the variable in the Description column.

## Using A Text File to Batch Run GAM Commands
Sometimes you have a text file with a whole bunch of GAM commands you want to run in a batch. You can do this with the batch command:
```
gam batch <batch-filename>
```

the batch file should contain gam commands one per line. So if you have a batch file named create-users.txt that looks like:
```
gam create user larry@acme.com
gam create user moe@acme.com
gam create user curly@acme.com
```
and you ran:
```
gam batch create-users.txt
```
then the 3 users would be created. But what if we wanted to add them to a group also? Say our batch file looked like:
```
gam create user larry@acme.com
gam create user moe@acme.com
gam create user curly@acme.com
gam create group 3stooges@acme.com
gam update group 3stooges@acme.com add members users "larry moe curly"
```
our users will get created but adding them to the group may fail. Why? Because GAM is trying to add them to the group at the same time it's creating the users and the group. Thus the users and or the group may not exist in time for the users to get added to the group resulting in a "Not Found" kind of error.

We can use the "commit-batch" argument in our batch file to make sure GAM has run all commands above commit-batch in the file before continuing on. So if we change our create-users.txt to look like:

```
gam create user larry@acme.com
gam create user moe@acme.com
gam create user curly@acme.com
gam create group 3stooges@acme.com
commit-batch
gam update group 3stooges@acme.com add members users "larry moe curly"
```
then GAM will run our first 3 commands to create the users and groups but will wait until they're done running before continuing on to the last command that adds the users to the group.

## Determining How Many GAM Commands Run In Parallel
For both csv and batch commands, GAM will run multiple actions in parallel. By default, GAM starts 5 worker threads and can run 5 commands at a time. You can raise or lower this setting by setting an environment variable called GAM\_THREADS. Setting environment variables varies by your OS:
```
Windows DOS Shell:
set GAM_THREADS=10

Windows PowerShell:
$env:GAM_THREADS=10

Linux / OSX:
export GAM_THREADS=10
```
will tell GAM to run max 10 GAM commands in parallel.

Note that I don't recommend going much higher than 20 for GAM\_THREADS. You're likely to see issues with Google API quotas if you do.

# Old OS-Specific Methods
## Bulk Operations on Windows

The most powerful tool for bulk operations on Windows is [Microsoft's PowerShell](http://www.microsoft.com/windowsserver2003/technologies/management/powershell/download.mspx). Download and install PowerShell.  Once installed open it from the Start Menu or Start, Run, PowerShell.exe.

Let's take the following CSV file as an example, it contains 5 usernames and new passwords for them:

**password\_updates.csv**
```
username, password
jsmith, superduper23
gjones, rubberduckey15
pthompson, poodlepups21
icooley, iLuvCats67
rhanley, BigTrucka90
```

Now we can use some PowerShell scripting with GAM to do all the password changes.  Create another file (.ps1 files are PowerShell scripts):

**update\_passwords.ps1**
```
$list = Import-Csv password_updates.csv
foreach ($entry in $list)
  {
    .\gam.exe update user $($entry.username) password $($entry.password)
  }
```

this script will read in password\_updates.csv and for each line, execute our GAM command, replacing $($entry.username) with the username and $($entry.password) with the password (notice how the variable names are based on the headings in our password\_updates.csv file).

Here's another example to update a group.

**student\_group\_updates.csv**
```
username,action,usertype
jsmith,add,member
gjones,add,owner
pthompson,remove,
icooley,add,member
rhanley,add,owner
```

and our script:

**update\_student\_group.ps1**
```
$list = Import-Csv student_group_updates.csv
foreach ($entry in $list)
  {
    .\gam.exe update group students $($entry.action) $($entry.usertype) $($entry.username)
  }
```

since we've defined the action, we can both add and remove users with one run through.

## Bulk Operations on Linux

Recently I needed to create 300,000 Google Apps user accounts for a client as quickly as possible. The users were spread across multiple LDAP and non-LDAP authentication sources so [GCDS](http://support.google.com/a/bin/answer.py?hl=en&answer=106368) was out of the question and [Google's Bulk Upload Control Panel feature](http://support.google.com/a/bin/answer.py?hl=en&answer=40057) maxes out at a few thousand accounts. But GAM was up to the challenge. I was able to create the 300,000 accounts in less than 11 hours time using a single computer, GAM and a little bit of Linux Bash shell scripting. Here's the script along with some comments:

```
#!/bin/bash

gam_command() {
  OAUTHFILE=oauth.txt-admin$x python ~/bin/gam/gam.py create user "$email" firstname "$firstname" lastname "$lastname" password "$password"
  }

IFS=,
x=1
while read email firstname lastname password; do
  email=${email//\"/}
  firstname=${firstname//\"/}
  lastname=${lastname//\"/}
  gam_command $email $firstname $lastname $org $x &
  while (( $(jobs | wc -l) >= 20 )); do
    sleep 0.1
    jobs > /dev/null
    done
  x=$(($x+1))
  if [ $x -gt 20 ]
  then
    x=1
  fi
done < users.csv

wait
```

Comments:
```
OAUTHFILE=oauth.txt-admin$x python ~/bin/gam/gam.py create user "$email" firstname "$firstname" lastname "$lastname" password "$password"
```
This line is the actual GAM command that is run. Notice that the [OAUTHFILE is set to something like oauth.txt-admin1](OAuthKeyManagement), oauth.txt-admin2, etc on each run. This isn't strictly necessary but I recommend it when doing more than 5,000 commands or so. If you attempt this many API calls with a single Google Apps account, Google's servers will start rate limiting you and the script will take much longer to run through. Using multiple Google Apps Admin accounts splits the API calls up and keeps you from hitting Google quota limits.

```
while read email firstname lastname password; do
```
this line reads in the actual CSV file and sets the variables based on the entries in that row of the CSV. So if the format of your CSV columns differs, you should change these names as needed. After reading the variables in on this line, they can be referenced as $email, $firstname, etc.

```
  email=${email//\"/}
  firstname=${firstname//\"/}
  lastname=${lastname//\"/}
```
these lines clean up the variables somewhat removing quotes that might have been in the CSV file. Note also that if there were any commas in the actual CSV data (not just as delimiters, they should be escaped with a slash character.

```
gam_command $email $firstname $lastname $org $x &
```
this line calls the gam\_command function and passes it the needed variables. The & is very important here, it tells the script to start the gam\_command function passing it a row of the CSV data and then immediately continue on the script. This allows multiple GAM instances to be running at the same time. So instead of running 1 GAM command, waiting until it finishes and then starting the next, the script can run multiple GAM commands in parallel. This literally cuts down the script execution time by a factor of 20.

```
  while (( $(jobs | wc -l) >= 20 )); do
    sleep 0.1
    jobs > /dev/null
    done
```
running multiple GAM commands in parallel is good but trying to run 500 or 500,000 GAM commands all at once is going to bring your computer to it's knees! This portion of the script limits you to running 20 GAM commands at a time. If all 20 commands are still running, the script waits until one finishes to start another.

```
  x=$(($x+1))
  if [ $x -gt 20 ]
  then
    x=1
  fi
```
this is what rotates between our 20 administrators. $x will get incremented all the way up to 20 and then reset back to 1. This means that each of the 20 admins will create an equal number of users and keeps us from hitting quotas on the Google API servers.

```
done < users.csv

wait
```
done < users.csv reads in the CSV of users one at a time for our while loop. The wait command here simply tells the script to wait until all GAM processes end to stop running itself.

Your CSV file should look something like:

```
joe@example.com,Joe,Smith,p@ssw3rd
jill@example.com,Jill,Smith,s3cr3T
```

notice that there is no CSV header, this script doesn't use a header so if there is one, be sure to delete it before running.

If you're wondering how you're going to create 20 GAM Admins and authorize them all with GAM, you can do it fairly simple with a command like:

```
for i in {1..20}; do gam create user admin$i firstname Admin lastname "User $i" password Sup3rStr0ngP4ss admin on; OAUTHFILE=oauth.txt-admin$i gam info domain; done
```
this will use GAM to create the 20 admins and then walk you through setting up GAM for that admin. It'll still take a little while but it's quicker than making them all manually. Once you're done running your huge number of GAM commands, you can delete all your temp admins with a command like:

```
for i in {1..20}; do gam delete user admin$i; done
```

Need help with a custom GAM script like this or other Google Apps scripting? Try sending an email to the [GAM Discussion List](https://groups.google.com/forum/#!forum/google-apps-manager)

# Avoid prompts to update GAM
If you are running batch commands and want to avoid GAM checking for updates, create a blank text file called "noupdatecheck.txt" in the same folder as gam.exe or gam.py. This disables all update checks.