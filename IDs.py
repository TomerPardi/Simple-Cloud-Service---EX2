# class that manages ID dictionary
class IDs:
    def __init__(self):
        self.__keys = dict()

    def add_client(self, id):
        self.__keys[id] = dict()

    def get_id_value(self, id):
        if id in self.__keys.keys():
            return self.__keys[id]

    def remove_id(self, id):
        if id in self.__keys.keys():
            self.__keys.pop(id)

    def get_size_of_sub_ids_dict(self, id):
        return len(self.__keys[id])

    # TODO: we have the same function at Data.py
    def add_pc(self,id, sub_id):
        paths = self.get_id_value(id)
        paths[sub_id] = set()

