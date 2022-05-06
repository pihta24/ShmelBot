import re
import os

from flask_cors import CORS
from pymongo import MongoClient
from models.User import User
from flask import Flask, json, request, abort
from vk_api import VkApi
from vk_api.utils import get_random_id
import random
from base64 import b64encode
from hashlib import sha256
from hmac import HMAC
from urllib.parse import parse_qsl, urlencode

VK_ACCESS_KEY = os.environ.get("VK_ACCESS_KEY")
VK_TOKEN = os.environ.get("VK_TOKEN")
VK_SECURE_KEY = os.environ.get("VK_SECURE_KEY")

phrases = ["Представь шмеля", "Видишь шмеля?",
           "Вжжжжжж", "Я шмель",
           "Где шмель?", "Вы видите шмеля?",
           "Шмель-шмель", "Пьяный шмель",
           "Веселый шмель", "Крутой шмель",
           "Уставший шмель"]

app = Flask(__name__)
CORS(app)

vk = VkApi(token=VK_TOKEN)
vk_api = vk.get_api()
mongo_client = MongoClient(os.environ.get("DB_CONNECTION_STRING"))


def is_valid(query: dict, secret: str) -> bool:
    """
    Check VK Apps signature
    :param dict query: Словарь с параметрами запуска
    :param str secret: Секретный ключ приложения ("Защищённый ключ")
    :returns: Результат проверки подписи
    :rtype: bool
    """
    if not query.get("sign"):
        return False
    vk_subset = sorted(filter(lambda key: key.startswith("vk_"), query))
    if not vk_subset:
        return False
    ordered = {k: query[k] for k in vk_subset}
    hash_code = b64encode(HMAC(secret.encode(),
                               urlencode(ordered, doseq=True).encode(),
                               sha256).digest()).decode("utf-8")
    if hash_code[-1] == "=":
        hash_code = hash_code[:-1]
    fixed_hash = hash_code.replace('+', '-').replace('/', '_')
    return query.get("sign") == fixed_hash


@app.route('/callback/vk/', methods=["POST"])
def vk():
    data = json.loads(request.data.decode())
    if data["secret"] == VK_ACCESS_KEY:
        if data["type"] == "confirmation":
            if data["group_id"] == 204539742:
                return "f72bf7bc"
        elif data['type'] == 'message_new':
            message = data["object"]["message"]
            if message["peer_id"] < 2000000000:
                if message["text"].lower() == "шмель":
                    vk_api.messages.send(message=random.choice(phrases),
                                         user_id=message["from_id"],
                                         random_id=get_random_id())
                elif message["text"].lower() == "баланс":
                    vk_api.messages.send(message="Баланс: "
                                                 f"{User.get(message['from_id'], vk_api, mongo_client).balance} "
                                                 "мёда",
                                         user_id=message["from_id"],
                                         random_id=get_random_id())
                elif message["text"].lower() == "профиль":
                    user = User.get(message['from_id'], vk_api, mongo_client)
                    vk_api.messages.send(message=
                                         f"Баланс: {user.balance} мёда\n"
                                         f"Был(а) шмелём {user.was_shmel} раз",
                                         user_id=message["from_id"],
                                         random_id=get_random_id())
            else:
                chat_id = message["peer_id"] - 2000000000
                if message["text"].lower() == "шмель":
                    vk_api.messages.send(message=random.choice(phrases),
                                         chat_id=chat_id,
                                         random_id=get_random_id())
                elif message["text"].lower() == "шмель баланс":
                    vk_api.messages.send(message="Баланс:"
                                                 f" {User.get(message['from_id'], vk_api, mongo_client).balance}"
                                                 " мёда",
                                         chat_id=chat_id,
                                         random_id=get_random_id())
                elif message["text"].lower() == "шмель профиль":
                    user = User.get(message['from_id'], vk_api, mongo_client)
                    vk_api.messages.send(message=f"Профиль пользователя {user.name}\n"
                                                 f"Баланс: {user.balance} мёда\n"
                                                 f"Был(а) шмелём {user.was_shmel} раз",
                                         chat_id=chat_id,
                                         random_id=get_random_id())
                elif re.match("[бв]ж{2,}", message["text"].lower()):
                    User.get(message['from_id'], vk_api, mongo_client).was_shmel += 1
                    vk_api.messages.send(message=f"{User.get(message['from_id'], vk_api, mongo_client).name}"
                                                 + " теперь шмель",
                                         chat_id=chat_id,
                                         random_id=get_random_id())
                if "action" in message.keys():
                    if message["action"]["type"] == "chat_invite_user" or\
                            message["action"]["type"] == "chat_invite_user_by_link":
                        vk_api.messages.send(message="Приветствуем нового шмеля в нашей беседе",
                                             chat_id=chat_id,
                                             random_id=get_random_id())
                    elif message["action"]["type"] == "chat_kick_user":
                        vk_api.messages.send(message="Мы потеряли одного из наших шмелей :(",
                                             chat_id=chat_id,
                                             random_id=get_random_id())
    return "ok"


@app.route("/api/balance/", methods=["GET", "POST"])
def balance():
    launch_params = dict(parse_qsl(request.headers.get("Authorization").replace("Bearer ", ""), keep_blank_values=True))
    if not is_valid(launch_params, VK_SECURE_KEY):
        abort(403)
    user = User.get(int(launch_params["vk_user_id"]), vk_api, mongo_client)
    if request.method == "GET":
        try:
            return str(user.balance)
        except Exception:
            return "error"
    elif request.method == "POST":
        try:
            user.balance = int(request.data)
            return "ok"
        except Exception:
            return "error"
    return ""


@app.route("/api/click/", methods=["POST"])
def click():
    launch_params = dict(parse_qsl(request.headers.get("Authorization").replace("Bearer ", ""), keep_blank_values=True))
    if not is_valid(launch_params, VK_SECURE_KEY):
        abort(403)
    user = User.get(int(launch_params["vk_user_id"]), vk_api, mongo_client)
    try:
        user.balance += 1
        return str(user.balance)
    except Exception:
        return "error"


if __name__ == '__main__':
    app.run()
