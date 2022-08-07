import json


class Database:
    pass


class JsonDatabase(Database):

    def __init__(self, filename):
        self.filename = filename
        try:
            with open(filename, 'r') as f:
                self.data = json.loads(f.read())
        except FileNotFoundError:
            self.data = {}

    def get(self, position_id):
        if position_id not in self.data:
            self.data[position_id] = {}
        return self.data[position_id]

    def set(self, position_id, moves):
        self.data[position_id] = moves

    def save(self):
        data = json.dumps({k: v for k, v in self.data.items() if v})
        with open(self.filename, 'w') as f:
            f.write(data)
