"""
* Authors: Tomer Pardilov and Yoav Otmazgin
* Class to handle ID dictionary
* Linux OS support only
"""


class IDs:
    def __init__(self):
        self.__keys = dict()

    def add_client(self, id):
        self.__keys[id] = dict()

    def remove_id(self, id):
        if id in self.__keys.keys():
            self.__keys.pop(id)

    def get_size_of_sub_ids_dict(self, id):
        return len(self.__keys[id])

    def get_size_of_sub_id_set(self, id, sub_id):
        set = self.__keys[id][sub_id]
        return len(set)

    def get_id_dict(self, id):
        return self.__keys[id]

    def get_sub_id_set(self, id, sub_id):
        return self.__keys[id][sub_id]

    def add_pc(self,id, sub_id):
        paths = self.__keys[id]
        paths[sub_id] = []