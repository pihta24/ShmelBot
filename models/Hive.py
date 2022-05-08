from typing import Optional

from vk_api.vk_api import VkApiMethod
from pymongo import MongoClient


class Hive:
    def __init__(self, vk_id: int, vk_api: VkApiMethod, mongo_client: MongoClient):
        self.__id = None
        self.__vk_api = vk_api
        self.__mongo_client = mongo_client
        self.vk_id = vk_id
    
    @property
    def title(self) -> Optional[str]:
        hive = self.__vk_api.messages.getConversationsById(peer_ids=self.vk_id)
        if not hive:
            return None
        return hive["items"][0]["chat_settings"]["title"]
    
    @property
    def balance(self) -> int:
        return self.__mongo_client["users"]["hives"].find_one({"_id": self.__id})["balance"]
    
    @balance.setter
    def balance(self, value: int) -> None:
        self.__mongo_client["users"]["hives"].update_one({"_id": self.__id}, {"$set": {"balance": value}})
        
    @property
    def members(self):
        return self.__mongo_client["users"]["hives"].find_one({"_id": self.__id})["members"]
    
    def add_member(self, value):
        self.__mongo_client["users"]["hives"].update_one({"_id": self.__id}, {"$addToSet": {"members": value}})
    
    def del_member(self, value):
        self.__mongo_client["users"]["hives"].update_one({"_id": self.__id}, {"$pull": {"members": value}})
    
    @staticmethod
    def get(vk_id: int, vk_api: VkApiMethod, mongo_client: MongoClient, user_id=None):
        hive = mongo_client["users"]["hives"].find_one({"vk_id": vk_id})
        hive_model = Hive(vk_id, vk_api, mongo_client)
        if hive is None:
            hive_model.__id = mongo_client["users"]["hives"].insert_one(
                {
                    "vk_id": vk_id,
                    "members": [] if not user_id else [user_id],
                    "balance": 0,
                }
            ).inserted_id
        else:
            hive_model.__id = hive["_id"]
            hive_model.add_member(user_id)
        return hive_model
