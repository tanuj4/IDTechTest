#!/bin/sh
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
exec gunicorn --bind 0.0.0.0:5000 "app:create_app('production')"
