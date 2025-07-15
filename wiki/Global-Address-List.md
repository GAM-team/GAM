# Global Address List

As of mid-October 2024, Google deprecated the API that retrieved the Global Address List.

These commands are a work-around.

Display users/groups in GAL.
```
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:true" redirect csv ./UserGAL.csv print users fields name,gal
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:true" batch_size 25 redirect csv ./GroupGAL.csv print groups fields name,gal
```

Display users/groups not in GAL.
```
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:false" redirect csv ./UserNotGAL.csv print users fields name,gal
gam config csv_output_row_filter "includeInGlobalAddressList:boolean:false" batch_size 25 redirect csv ./GroupNotGAL.csv print groups fields name,gal
```
