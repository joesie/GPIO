#!/bin/bash

PLUGINNAME=REPLACELBPPLUGINDIR
PATH="/sbin:/bin:/usr/sbin:/usr/bin:$LBHOMEDIR/bin:$LBHOMEDIR/sbin"

ENVIRONMENT=$(cat /etc/environment)
export $ENVIRONMENT

# Logfile
. $LBHOMEDIR/libs/bashlib/loxberry_log.sh
PACKAGE=${PLUGINNAME}
NAME=${PLUGINNAME}_MQTT
LOGDIR=$LBPLOG/${PLUGINNAME}



# Debug output
#STDERR=0
#DEBUG=0
if [[ ${LOGLEVEL} -eq 7 ]]; then
	LOGINF "Debugging is enabled! This will produce A LOT messages in your logfile!"
	STDERR=1
	DEBUG=1
fi

LOGSTART "gpio2mqtt"

case "$1" in
  start|restart)

	echo $HOSTNAME"/gpio/#" > $LBHOMEDIR/config/plugins/${PLUGINNAME}/mqtt_subscriptions.cfg
	
	if [ "$1" = "restart" ]; then
		LOGINF "Stopping gpio2mqtt..."
		pkill -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/gpio2mqtt.py" >> ${FILENAME} 2>&1
	fi

	if [ "$(pgrep -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/gpio2mqtt.py")" ]; then
		LOGINF "gpio2mqtt.py already running."
		LOGEND "gpio2mqtt"
		exit 0
	fi

	LOGINF "Starting gpio2mqtt..."
	$LBHOMEDIR/bin/plugins/${PLUGINNAME}/gpio2mqtt.py --logfile ${FILENAME} --loglevel ${LOGLEVEL} --configfile $LBHOMEDIR/config/plugins/${PLUGINNAME}/pluginconfig.json --lbhomedir $LBHOMEDIR > /dev/null 2>&1 &

	LOGEND "gpio2mqtt"
        exit 0
        ;;

  stop)

	LOGINF "Stopping gpio2mqtt..."
	pkill -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/gpio2mqtt.py" >> ${FILENAME} 2>&1

	if [ "$(pgrep -f "$LBHOMEDIR/bin/plugins/${PLUGINNAME}/gpio2mqtt.py")" ]; then
		LOGERR "gpio2mqtt.py could not be stopped."
	else
		LOGOK "gpio2mqtt.py stopped successfully."
	fi

	LOGEND "gpio2mqtt"
        exit 0
        ;;

  *)
        echo "Usage: $0 [start|stop|restart]" >&2
	LOGINF "No command given. Exiting."
	LOGEND "gpio2mqtt"
        exit 0
  ;;

esac

LOGEND "gpio2mqtt"
