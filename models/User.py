import random
from typing import Optional

from vk_api.vk_api import VkApiMethod
from pymongo import MongoClient

from utils import photos


class User:
    def __init__(self, vk_id: int, vk_api: VkApiMethod, mongo_client: MongoClient):
        self.__id = None
        self.__vk_api = vk_api
        self.__mongo_client = mongo_client
        self.vk_id = vk_id

    @property
    def id(self):
        return self.__id
    
    @property
    def name_gen(self) -> Optional[str]:
        user = self.__vk_api.users.get(user_ids=[self.vk_id], name_case='gen')
        if not user:
            return None
        return user[0]["first_name"]
    
    @property
    def picture(self) -> str:
        return self.__mongo_client["users"]["users"].find_one({"_id": self.__id})["picture"]
    
    @property
    def hives_count(self):
        return self.__mongo_client["users"]["hives"].count_documents({"members": self.__id})
    
    @property
    def balance(self) -> int:
        return self.__mongo_client["shmelcoin"]["balances"].find_one({"user_id": self.__id})["balance"]

    @balance.setter
    def balance(self, value: int) -> None:
        self.__mongo_client["shmelcoin"]["balances"].update_one({"user_id": self.__id}, {"$set": {"balance": value}})
    
    @property
    def was_shmel(self) -> int:
        return self.__mongo_client["users"]["users"].find_one({"_id": self.__id})["was_shmel"]
    
    @was_shmel.setter
    def was_shmel(self, value: int) -> None:
        self.__mongo_client["users"]["users"].update_one({"_id": self.__id}, {"$set": {"was_shmel": value}})
    
    @staticmethod
    def get(vk_id: int, vk_api: VkApiMethod, mongo_client: MongoClient):
        user = mongo_client["users"]["users"].find_one({"vk_id": vk_id})
        user_model = User(vk_id, vk_api, mongo_client)
        if user is None:
            user_model.__id = mongo_client["users"]["users"].insert_one(
                {
                    "vk_id": vk_id,
                    "was_shmel": 0,
                    "picture": random.choice(photos),
                }
            ).inserted_id
            mongo_client["shmelcoin"]["balances"].insert_one({"user_id": user_model.__id, "balance": 0})
        else:
            user_model.__id = user["_id"]
        return user_model
