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

    # TODO: we have the same function at Data.py
    def add_pc(self,id, personal_path):
        paths = self.get_id_value(id)
        paths[personal_path] = set()