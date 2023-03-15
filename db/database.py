import sqlite3

users_db = sqlite3.connect('db/users.db')
cur = users_db.cursor()

# Создание необходимых таблиц
cur.execute("""CREATE TABLE IF NOT EXISTS main
(
    user_id BIGINT,
    viewed_forms TEXT DEFAULT ""
)""")


def is_user_exists(user_id: int) -> bool:
    """
    Проверка на существование айди пользователя в БД
    :param user_id: Айди пользователя, которого надо проверить
    """
    result = cur.execute(
        f"SELECT user_id FROM main WHERE user_id={user_id}"
    ).fetchone()
    if result is not None:
        return True
    return False


def register_user(user_id: int):
    """
    Регистрация пользователя в БД
    :param user_id: Айди пользователя, которого надо зарегестрировать
    """
    cur.execute(
        "INSERT INTO main(user_id)"
        " VALUES (?)",
        (user_id,),
    )


def get_user(user_id: int, column: str) -> str:
    """
    Возвращает определенный столбец пользователя из БД
    :param user_id: Айди пользователя из БД
    :param column: Название столбца
    """
    result = cur.execute(
        f"SELECT {column} FROM main WHERE user_id = {user_id}"
    ).fetchone()[0]
    return result


def update_user(user_id: int, column: str, value: str):
    """
    Устанавливает значение для определененого столбца у пользователя из БД
    :param user_id: Айди пользователя из БД
    :param column: Название столбца
    :param value: Новое значение для этого столбца
    """
    cur.execute(
        f"UPDATE main SET {column} = ? WHERE user_id = ?",
        (value, user_id)
    )


def commit_db():
    """
    Сохраняет базу данных
    """
    users_db.commit()
