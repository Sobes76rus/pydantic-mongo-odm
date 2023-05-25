#!/bin/bash

mongodb=`getent hosts ${MONGO} | awk '{ print $0 }'`
port=${PORT:-27017}

if [ -z "${MONGO}"]
then mongodb=$1
fi

if [ -z "${PORT}" ]
then port=$2
fi

echo "Waiting for startup.."
variable=`mongosh --host ${mongodb} --port ${port} --eval 'quit(db.runCommand({ ping: 1 }).ok ? 0 : 2)'`
echo ${var}
until mongosh ${mongodb}:${port} --eval 'quit(db.runCommand({ ping: 1 }).ok ? 0 : 2)' &>/dev/null; do
  printf '.'
  sleep 1
done

echo "Started..."
mongosh --host ${mongodb} --port ${port} <<EOF
var config = {
    "_id": "${RS:-$3}",
    "members": [
        {
            "_id": 0,
            "host": "localhost:27017",
        },
    ]
};
rs.initiate(config, { force: true });
rs.status();
EOF
