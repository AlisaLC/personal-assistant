#!/bin/bash
set -e

# Create the notes database first
createdb -U "$POSTGRES_USER" "$NOTES_DB"

# Create the webui database
createdb -U "$POSTGRES_USER" "$WEBUI_DB"

# Grant privileges on both databases
psql -U "$POSTGRES_USER" -d "$NOTES_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;"
psql -U "$POSTGRES_USER" -d "$WEBUI_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;"
