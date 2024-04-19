docker exec -it mongodb_primary mongo --eval "rs.initiate({
 _id: \"myReplicaSet\",
 members: [
   {_id: 0, host: \"mongodb_primary\"},
   {_id: 1, host: \"mongodb_secondary_1\"},
   {_id: 2, host: \"mongodb_secondary_2\"}
 ]
})"