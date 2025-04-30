rm -rf meteor_detect_class
cp -r ../meteor_detect_class .
docker stop ms-detect
docker rm ms-detect

if [ ! -d "mount-detection" ]; then
    mkdir mount-detection
fi
if [ ! -d "mount-detection/csv-out" ]; then
    mkdir mount-detection/csv-out
fi
if [ ! -d "mount-detection/spec-out" ]; then
    mkdir mount-detection/spec-out
fi
if [ ! -d "mount-detection/log-out" ]; then
    mkdir mount-detection/log-out
fi

docker build -t ms-detect-img -f Dockerfile-Detection .

#docker run --name ms-detect \
#    -v "$(pwd)"/mount-detection:/home/meteor/Documents/meteor-detection/ \
#    -it --rm ms-detect-img

docker run --name ms-detect \
    -v "$(pwd)"/mount-detection:/home/meteor/Documents/meteor-detection/ \
    -d --restart=always \
    ms-detect-img

rm -rf meteor_detect_class