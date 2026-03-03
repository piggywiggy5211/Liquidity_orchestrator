from testcontainers.postgres import PostgresContainer


def main():
    print("Инициализация контейнера PostgreSQL...")
    with PostgresContainer("postgres:15-alpine") as postgres:
        print("✅ Контейнер успешно запущен!")
        print(f"🔗 Строка подключения: {postgres.get_connection_url()}")


if __name__ == "__main__":
    main()
