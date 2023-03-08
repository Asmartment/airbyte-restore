#!/bin/bash


DATE=`date +%m%d%Y`
#DATE="2023025"
CONF="airbyte-restore/airbyte-dev/airbyte-configuration"
GH_REPO="https://github.com/Asmartment/airbyte-restore"
SLACK_WEBHOOK="https://hooks.slack.com/services/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"
#AIRBYTE_HOST="ec2-44-193-9-158.compute-1.amazonaws.com"
AIRBYTE_HOST="localhost"
AIRBYTE_PORT="8000"




USAGE="Usage: `basename $0` < option > | --test-connections | --backup "

if [ $# -eq 0 ]; then
   echo "${USAGE}" >&2
   exit 1
fi



test_airbyte_conn() {
echo "verify airbyte service URL..."
nc -vz $AIRBYTE_HOST $AIRBYTE_PORT -w 2
if [ "$?" -ne 0 ]; then
 echo "Airbyte DEV instance http://$AIRBYTE_HOST:$AIRBYTE_PORT down"
	curl -X POST -H 'Content-type: application/json'  --data '{"text":"TEST MESSAGE: http://'"$AIRBYTE_HOST":$AIRBYTE_PORT' Airbyte DEV instance down"}' $SLACK_WEBHOOK
  exit 1
else
  echo "Connection to $SERVER on port $AIRBYTE_PORT succeeded"
  exit 0
fi
}

take_airbyte_backup() {
echo "starting backup..."
git clone $GH_REPO
mkdir -p $CONF/$DATE
cd $CONF/$DATE

echo "downloading backup..."
OCTAVIA="docker run -i --rm -v $(pwd):/home/octavia-project --network host --user $(id -u):$(id -g) airbyte/octavia-cli:0.40.32"
$OCTAVIA init
$OCTAVIA --airbyte-url http://$AIRBYTE_HOST:$AIRBYTE_PORT import all 
if [ "$?" -ne 0 ]; then
 echo "Airbyte DEV BACKUP FAILED"
	curl -X POST -H 'Content-type: application/json'  --data '{"text":"TEST MESSAGE: Airbyte DEV BACKUP FAILED"}' $SLACK_WEBHOOK
  exit 1
else
	echo "successfull download connections on $CONF/$DATE"
  
  git add .
  git commit -m "add airbyte backup connections $DATE"
  git push 
  if [ "$?" -eq 0 ]; then
	  rm -rf /home/airbyte/airbyte-restore
  fi


fi
}  

while test $# -gt 0; do
	 case "$1" in
    --backup)
		take_airbyte_backup  2>&1 | tee take-backup-$DATE.log
	    exit 0
      ;;
    --test-connections)
		test_airbyte_conn
	    exit 0
      ;;
    *)
	   echo "unkown option !!!"
	   echo ${USAGE}
      break
      ;;
  esac
done
