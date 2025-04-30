# PLS ACTIVE VIRTUAL ENVIRONMENT BEFORE RUNNING THIS SCRIPT (NON DOCKER)

DOCKER_MODE=false

for arg in "$@"; do
    if [ "$arg" == "--docker" ]; then
        DOCKER_MODE=true
    fi
done

if [ "$DOCKER_MODE" == true ]; then
    echo "Docker-Modus ist aktiviert"
    LOG_FILE_PATH="/home/meteor/Documents/meteor-detection/log-out/log.txt"
    pip freeze > /home/meteor/Documents/meteor-detection/log-out/requirements-backup.txt
else
    echo "Docker-Modus ist deaktiviert"
    LOG_FILE_PATH="log.txt"
fi

while true; do

    current_time=$(date "+%Y.%m.%d-%H.%M.%S")

    echo
    echo "RESTART PRIME DETECTION at $current_time"

    echo "\n" >> $LOG_FILE_PATH
    echo "RESTART PRIME DETECTION at $current_time" >> $LOG_FILE_PATH
    python prime_detection.py >> $LOG_FILE_PATH 2>&1

    current_time=$(date "+%Y.%m.%d-%H.%M.%S")
    echo "CRASHED... at $current_time"
    sleep 3

done