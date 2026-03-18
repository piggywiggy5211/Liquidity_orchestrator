-- Initial database setup for Liquidity Orchestrator

-- Service 1: Liquidity Orchestrator
CREATE USER orchestrator WITH PASSWORD 'orchestrator_pass';
CREATE DATABASE liquidity_orchestrator OWNER orchestrator;
GRANT ALL PRIVILEGES ON DATABASE liquidity_orchestrator TO orchestrator;

-- Service 2:
