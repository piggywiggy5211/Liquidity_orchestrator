-- Initial database setup for Liquidity Orchestrator

-- Service 1: Liquidity Orchestrator
CREATE USER orchestrator WITH PASSWORD 'orchestrator_pass';
CREATE DATABASE liquidity_orchestrator;
GRANT ALL PRIVILEGES ON DATABASE liquidity_orchestrator TO orchestrator;

-- To add new services, follow the pattern above:
-- CREATE USER new_service_user WITH PASSWORD 'password';
-- CREATE DATABASE new_service_db;
-- GRANT ALL PRIVILEGES ON DATABASE new_service_db TO new_service_user;
