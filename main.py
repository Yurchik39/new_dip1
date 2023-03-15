# Импортирование модулей:
import time

import requests

import VKLong.VKLong.object
from config import BOT_TOKEN
from db.database import *
from VKLong.VKLong import Bot

# Авторизация:
user_token = input("Введите user-token, который будет использоваться для поиска людей: ")

bot = Bot(token=BOT_TOKEN)
users_forms = {}


def search_users(user_id: int, city: int, sex: int) -> dict:
    """
    Ищет пользователей, учитывая настройки указанного пользователя
    :param user_id: Айди пользователя, который ищет других людей
    :param city: Город, в котором надо искать пользователей
    :param sex: Пол текущего пользователя
    """

    if sex == 1:
        sex = 2
    else:
        sex = 1

    try:
        response = requests.get(
            "https://api.vk.com/method/users.search",
            params={
                "count": 1000,
                "city": city,
                "sex": sex,
                "status": (1, 6),
                "age_from": 18,
                "access_token": user_token,
                "v": 5.131,
            },
        ).json()["response"]["items"]
    except KeyError:
        return None

    return response


def get_all_user_photos(user_id: int) -> dict:
    """
    Возвращает все фотографии указанного пользователя
    :param user_id: Пользователь, у которого надо найти все фотографии
    """
    response = requests.get(
        "https://api.vk.com/method/photos.getAll",
        params={
            "owner_id": user_id,
            "extended": 1,
            "count": 100,
            "skip_hidden": 1,
            "access_token": user_token,
            "v": 5.131,
        },
    ).json().get('response')

    return response


def get_user_vk(user_id: int) -> dict:
    try:
        response = requests.get(
            "https://api.vk.com/method/users.get",
            params={
                "fields": "city,sex",
                "access_token": user_token,
                "v": 5.131,
            },
        ).json()['response'][0]
    except KeyError:
        return None

    return response


# Получение обновлений:
@bot.get_updates
def on_update(event):
    # Если новое событие НЕ является сообщением:
    if event.type != "message_new":
        return

    message = VKLong.VKLong.object.message_new(event.response)
    user_id: int = message.from_id
    # Если сообщение НЕ из личных сообщений:
    if message.from_id > 2000000000:
        return
    text: str = message.text.lower()
    is_exists = is_user_exists(user_id)

    if not is_exists:
        register_user(user_id)
        commit_db()

    if text in ("поиск", "🔎 поиск"): 
        # Поиск новых пользователей
        finded_users_object = users_forms.get(user_id)
        if finded_users_object is not None:
            finded_users = finded_users_object["finded_users"]
        # 300 секунд = 5 минут
        if finded_users_object is None or finded_users_object["last_time"] + 300 < time.time():
            current_user_info = get_user_vk(user_id)

            city = current_user_info.get("city")
            if city is None:
                bot.answer(
                    "🤚 Упс! У вас в профиле не указан город!\n"
                    "\n"
                    "👉 Укажите город в профиле, что бы продолжить",
                )
                return
            else:
                city = city["id"]

            sex = current_user_info.get("sex")
            if sex is None:
                bot.answer(
                    "🤚 Упс! У вас в профиле не указан пол!\n"
                    "\n"
                    "👉 Укажите пол в профиле, что бы продолжить",
                )
                return

            finded_users = search_users(user_id, city, sex)

            if finded_users is None:
                bot.answer(
                    "🤚 Упс! Произошла неизвестная ошибка!\n"
                    "\n"
                    "👉 Попробуйте позже"
                )
                return

            users_forms[user_id] = {
                "finded_users": finded_users,
                "last_time": time.time()
            }

        for user_object in finded_users:
            if user_object["is_closed"]:
                continue

            finded_user_id = user_object['id']
            first_name = user_object['first_name']
            last_name = user_object['last_name']
            finded_link = f"vk.com/id{finded_user_id}"

            viewed_forms = get_user(user_id, "viewed_forms").split(",")
            viewed_forms = [int(i) for i in viewed_forms if i.isdigit()]
            if finded_user_id in viewed_forms:
                continue

            photos_object = get_all_user_photos(user_object["id"])
            if photos_object is None:
                continue

            if photos_object["count"] < 3:
                continue
 
            # Отправка фотографий и ссылок на пользователей:
            photo_dict = {}
            if photos_object["count"] > 100:
                photos_object["count"] = 100
            for i in range(photos_object["count"]):
                try:
                    photo_likes = photos_object["items"][i]["likes"]["count"]
                    photo_dict[
                        photo_likes
                    ] = f"photo{user_object['id']}_{photos_object['items'][i]['id']}"
                except KeyError:
                    break 

            if len(photo_dict) == 0:
                continue

            viewed_forms.append(finded_user_id)
            viewed_forms = [str(i) for i in viewed_forms]
            update_user(user_id, "viewed_forms", ','.join(viewed_forms))
            commit_db()

            attachment_list = ""

            for _ in range(3):
                attachment_list += f"{photo_dict[max(photo_dict)]},"
                photo_dict.pop(max(photo_dict))
 
            bot.answer(
                "👍 Найден подходящий профиль!\n"
                "\n"
                f"🏵 [id{finded_user_id}|{first_name} {last_name}]\n"
                f"Ссылка: {finded_link}",
                attachment=str(attachment_list),
            )
            break
    else:
        bot.answer(
            "👋 Привет! Добро пожаловать в VKinder!\n"
            "\n"
            '👉 Используй команду - "поиск", чтобы найти подходящего человека!',
        )

