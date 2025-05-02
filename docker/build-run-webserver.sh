rm -rf meteor_webserver
#cp -r ../ meteor_webserver
rsync -a --exclude='docker' ../ meteor_webserver/
rm -rf meteor_webserver/meteor_detect_class
docker stop ms-webserver
docker rm ms-webserver

if [ ! -d "mount-detection/csv-out" ]; then
    echo "Directory mount-detection/csv-out not exists. Exiting."
    echo "Please start the detection script first."
    exit 1
fi

if [ ! -d "mount-webserver" ]; then
    mkdir mount-webserver
fi
if [ ! -d "mount-webserver/log-out" ]; then
    mkdir mount-webserver/log-out
fi

docker build -t ms-webserver-img -f Dockerfile-Webserver .

docker run --name ms-webserver \
    -v "$(pwd)"/mount-detection:/home/meteor/Documents/meteor-detection/ \
    -v "$(pwd)"/mount-webserver:/home/meteor/Documents/meteor-webserver/ \
    -p 5000:5000 \
    -d --restart=always \
    ms-webserver-img

rm -rf meteor_webserver