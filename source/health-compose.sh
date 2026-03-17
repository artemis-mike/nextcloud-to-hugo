#!/bin/sh

export $(cat .env | xargs)

if [ -z $CF_UPDATER_INTERVAL ]; then 
    CF_UPDATER_INTERVAL=30
fi

SECONDS_SINCE_LAST_RUN=$(expr $(date +%s) - $(cat lastRun.epoch))
THRESHOLD=$(expr $CF_UPDATER_INTERVAL \* 2)

if [ "$SECONDS_SINCE_LAST_RUN" -lt "$THRESHOLD" ]; then 
    exit 0; 
else
    kill 1;
fi
