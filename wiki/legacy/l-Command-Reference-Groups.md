# GAM Group Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam **create** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email) [\<GroupAttributes\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Group-Attributes)

## gam **update** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)
* [admincreated true|false]
* [email [\<EmailAddress\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#email-address)]
* [\<GroupAttributes\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Group-Attributes)

## gam **info** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)
* [nousers]
* [noaliases]
* [groups]

## gam **update** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)
 **add** | **update** | **sync**  
 owner|member|manager  
 {user [\<email address\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email) |
 group [\<group address\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email) |org \<org name\> |
 file \<file name\> | all users}

## gam **update** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email) clear
* [owner]
* [manager]
* [member]

## gam **update** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)
 remove {user [\<email address\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email) |
 group [\<group address\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email) | org \<org name\> |
 file \<file name\> | all users}

## gam **delete** group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)

## gam [\<who\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#who) **delete** group

## gam print groups
* [domain \<domain\>]
* [member [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email)]
* [maxresults \<results\>]
* [name]
* [description]
* [admincreated]
* [id]
* [aliases]
* [members]
* [owners]
* [managers]
* [settings]
* [todrive]
* [delimiter \<delimchar\>]
* [fields \<list,of,fields\>]

## gam print group-members
* [group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email)]
* [domain \<domain\>]
* [member [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email)]
* [fields \<list,of,fields\>]
* [membernames]
* [todrive]