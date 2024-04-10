#!/bin/bash

CheckIfMongorestInstalled() {
    command -v mongorestore > /dev/null 2>&1;
}

echo "Enter your MongoDB Username:"
read username
echo "Enter the hostname of your MongoDB Cluster (e.g.: mycluster-shard00-00.mongodb.net):"
read hostname
echo "Enter the dataset you want. If you are using the Atlas free tier, use a smalldataset (10K docs)"
echo "smalldataset1 contains tags array and embeddings while smalldataset2 doesn't"
echo "Options - [smalldataset1, smalldataset2, largedataset]: "
read dataset



if ! CheckIfMongorestInstalled; then 
    echo 'Error: mongorestore is not installed.' >&2
else
    case ${dataset} in 
        'largedataset') archive='archive_lyrics.gzip';;   
        'smalldataset1') archive='archive_lyrics_small1.gzip';;
        'smalldataset2') archive='archive_lyrics_small2.gzip';;
    esac 
    echo "Starting data restore into your cluster: $archive"
    mongorestore -u $username --numInsertionWorkersPerCollection=16 --drop --gzip "mongodb+srv://$hostname/?retryWrites=true&w=majority&appName=LyricsDemo" --archive=./dataset/$archive
fi  
