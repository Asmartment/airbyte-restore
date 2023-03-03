# repository for airbyte backup/restore process

this repository works with 3 instances DEV/STG/PROD

each instance has 3 folders:

airbyte-restore -> airbyte-"instance" -----> airbyte-configuration ( backups connections for airbyte using octavia-cli ) \
                                       |---> scripts ( airbyte-backup-connections.sh / airbyte_restore.sh )
                                       |---> yaml-files ( yaml files for docker airbyte images )
                                     
                                     

