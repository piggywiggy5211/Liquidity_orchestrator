-- This initialization script runs when the PostgreSQL container is created for the first time.
-- The default database specified by POSTGRES_DB is already created by the postgres image.
-- You can use this file to create additional databases and users for future microservices.

-- Example for adding a new service database:
-- CREATE DATABASE another_service_db;
-- GRANT ALL PRIVILEGES ON DATABASE another_service_db TO myuser;
