#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available

WAITFORIT_cmdname=${0##*/}

echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

wait_for() {
    local host="$1"
    local port="$2"
    local timeout="${WAITFORIT_TIMEOUT:-15}"
    local start_ts=$(date +%s)
    while :
    do
        if nc -z "$host" "$port"; then
            end_ts=$(date +%s)
            echoerr "$WAITFORIT_cmdname: $host:$port is available after $((end_ts - start_ts)) seconds"
            return 0
        fi
        sleep 1
        if [[ $(($(date +%s) - start_ts)) -ge $timeout ]]; then
            echoerr "$WAITFORIT_cmdname: timeout occurred after waiting $timeout seconds for $host:$port"
            return 1
        fi
    done
}

WAITFORIT_QUIET=0
while [[ $# -gt 0 ]]
do
    case "$1" in
        -q | --quiet)
        WAITFORIT_QUIET=1
        shift 1
        ;;
        --)
        shift
        break
        ;;
        *)
        break
        ;;
    esac
done

hostport=(${1//:/ })
host="${hostport[0]}"
port="${hostport[1]}"
shift

wait_for "$host" "$port" || exit 1

exec "$@"