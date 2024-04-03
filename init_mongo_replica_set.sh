#!/bin/bash

# Wait for MongoDB primary container to be ready
until docker exec mongodb_primary mongo --eval "printjson(db.serverStatus())" > /dev/null 2>&1; do
    echo "Waiting for MongoDB primary container to be ready..."
    sleep 2
done

# Execute rs.initiate() command to initialize the replica set
docker exec mongodb_primary mongo --eval "rs.initiate({
  _id: 'myReplicaSet',
  members: [
    { _id: 0, host: 'mongodb_primary:27017' },
    { _id: 1, host: 'mongodb_secondary_1:27017' },
    { _id: 2, host: 'mongodb_secondary_2:27017' }
  ]
})"
