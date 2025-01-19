class DataStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataStore, cls).__new__(cls)
            cls._instance.value = [0, 100]
        return cls._instance

    def __init__(self):
        if self._instance is None:
            self._instance = super(DataStore, self).__new__(self)
            self._instance.value = 0

    def set_value(self, values: list[int]):
        self.value = values

    def get_value(self):
        return self.value
