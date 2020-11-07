#!/bin/bash
source venv/bin/activate
while true; do
  flask db upgrade
  if [[ "$?" == "0" ]]; then
    break
  fi
  echo Upgrade command failed, retrying in 5 secs...
  sleep 5
done
flask db upgrade
exec gunicorn -b :5000 montara:app
