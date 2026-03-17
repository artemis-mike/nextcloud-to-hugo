#!/bin/sh

export $(cat .env | xargs)

if [ -z $INTERVAL ]; then 
    INTERVAL=30
fi

SECONDS_SINCE_LAST_RUN=$(expr $(date +%s) - $(cat lastRun.epoch))
THRESHOLD=$(expr $INTERVAL \* 2)

if [ "$SECONDS_SINCE_LAST_RUN" -lt "$THRESHOLD" ]; then 
    exit 0; 
else
    kill 1;
fi
