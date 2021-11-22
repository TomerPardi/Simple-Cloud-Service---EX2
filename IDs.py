class IDs:
    def __init__(self):
        self.__number_of_clients = 1
        self.__keys = dict()

    def add_client(self, id, sock):
        self.__keys[id] = self.__number_of_clients
        self.__number_of_clients += 1

    def get_id_value(self, id):
        if id in self.__keys.keys():
            return self.__keys[id]
        return 0

    def remove_id(self, id):
        if id in self.__keys.keys():
            self.__keys.pop(id)
