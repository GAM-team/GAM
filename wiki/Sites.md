# Sites

The Classic Sites API no longer functions, the following commands are deprecated as of 7.04.00:
```
gam [<UserTypeEntity>] create site
gam [<UserTypeEntity>] update site
gam [<UserTypeEntity>] info site
gam [<UserTypeEntity>] print sites
gam [<UserTypeEntity>] show sites
gam [<UserTypeEntity>] create siteacls
gam [<UserTypeEntity>] update siteacls
gam [<UserTypeEntity>] delete siteacls
gam [<UserTypeEntity>] info siteacls
gam [<UserTypeEntity>] show siteacls
gam [<UserTypeEntity>] print siteacls
gam [<UserTypeEntity>] print siteactivity
```

You can list new sites for all users with the following command:
```
gam config auto_batch_min 1 num_threads 10 redirect csv ./NewSites.csv multiprocess redirect stderr - multiprocess all users print filelist fields id,name,mimetype filepath showmimetype gsite
```
