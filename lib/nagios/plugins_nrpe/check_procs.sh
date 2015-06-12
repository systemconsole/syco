#!/bin/bash

CRITICAL=0
WARNING=0
PROC=0
FILTER=0
EXITCODE=0
MEMWARN=0
MEMCRIT=0

function Usage {
        echo "
        This script looks at a command and its processes and calculates its CPU and memory usage

        OPTIONS:
        -p - The process name to look for
        -f - The optional filter to further filter between processes
        -w - The warning to use for the CPU percentage used
        -c - The critical to use for the CPU percentage used
        -m - The warning to use for the Memory percentage used
        -n - The critical to use for the Memory percentage used

        EXAMPLES:
                Check the usage for apache processes and alert warning if over 80% CPU utilised and critical if 90%
                ./check_cpu_proc.sh -p apache2 -w 80 -c 90

                Check the usage for nagios processes and alert warning if over 20% memory Utilised and critical if 30%
                ./check_cpu_proc.sh -p java -f eff -m 20 -n 30
"
        exit 3
}

while getopts "p:w:c:m:n:f:" OPTION
do
        case $OPTION in
                p)
                        PROC=$OPTARG
                  ;;
                f)
                        FILTER=$OPTARG
                  ;;

                w)
                        WARNING=$OPTARG
                  ;;

                c)
                        CRITICAL=$OPTARG
                  ;;

                m)
                        MEMWARN=$OPTARG
                  ;;

                n)
                        MEMCRIT=$OPTARG
                  ;;
        esac
done;

if [[ $PROC == 0 ]]; then
        echo "Must specify a process name"
        Usage
fi

PSOUTPUT=`ps aux | grep $PROC`

if [[ $FILTER != 0 ]]; then
        PSOUTPUT=`ps aux | grep $PROC | grep $FILTER`
fi

OIFS="${IFS}"
NIFS=$'\n'

IFS="${NIFS}"

OVERALCPU=0.0
OVERALMEM=0.0
OVERALRSS=0.0
OVERALVSZ=0.0
COUNT=0

for LINE in ${PSOUTPUT}; do
        CPU=$(echo $LINE | awk '{ print $3 }')
        COMMAND=$(echo $LINE | awk '{ print $11 }')
        MEM=$(echo $LINE | awk '{ print $4 }')
        RSS=$(echo $LINE | awk '{ print $6 }')
        VSZ=$(echo $LINE | awk '{ print $5 }')

        if [[ $COMMAND == *$PROC* ]]; then
                OVERALCPU=`echo "${OVERALCPU} + ${CPU}" | bc -l`
                OVERALMEM=`echo "${OVERALMEM} + ${MEM}" | bc -l`
                OVERALRSS=`echo "${OVERALRSS} + ${RSS}" | bc -l`
                OVERALVSZ=`echo "${OVERALVSZ} + ${VSZ}" | bc -l`
                COUNT=`echo "${COUNT} + 1" | bc -l`
                ACTCOMMAND=$COMMAND
        fi

done

if [ $WARNING != 0 ] || [ $CRITICAL != 0 ]; then
        if [ $WARNING == 0 ] || [ $CRITICAL == 0 ]; then
                echo "Must Specify both warning and critical"
                Usage
        fi

        #Work out CPU
        if [ `echo $OVERALCPU'>'$WARNING | bc -l` == 1 ]; then
                #echo $OVERALCPU'>'$WARNING
                #echo $OVERALCPU'>'$WARNING | bc -l
                EXITCODE=1

                if [ `echo $OVERALCPU'>'$CRITICAL | bc -l` == 1 ]; then
                        #echo $OVERALCPU'>'$CRITICAL
                        #echo $OVERALCPU'>'$CRITICAL | bc -l
                        EXITCODE=2
                fi
        fi
fi

if [ $MEMWARN != 0 ] || [ $MEMCRIT != 0 ]; then
        if [ $MEMWARN == 0 ] || [ $MEMCRIT == 0 ]; then
                echo "Must Specify both warning and critical"
                Usage
        fi

        #Work out Memory
        if [ `echo $OVERALMEM'>'$MEMWARN | bc -l` == 1 ]; then
                #echo $OVERALCPU'>'$WARNING
                #echo $OVERALCPU'>'$WARNING | bc -l
                EXITCODE=1

                if [ `echo $OVERALMEM'>'$MEMCRIT | bc -l` == 1 ]; then
                        #echo $OVERALCPU'>'$CRITICAL
                        #echo $OVERALCPU'>'$CRITICAL | bc -l
                        EXITCODE=2
                fi
        fi
fi

EXITTEXT="OK"

case "$EXITCODE" in
        1)
                EXITTEXT="WARNING"
        ;;

        2)
                EXITTEXT="CRITICAL"
        ;;

        3)
                EXITTEXT="UNKNOWN"
        ;;
esac


IFS="${OIFS}"

echo "${EXITTEXT} ${ACTCOMMAND} CPU: ${OVERALCPU}% MEM: ${OVERALMEM}% over ${COUNT} processes | proc=${COUNT} mem=${OVERALMEM}% cpu=${OVERALCPU}% rss=${OVERALRSS}KB vsz=${OVERALVSZ}KB"

exit $EXITCODE

