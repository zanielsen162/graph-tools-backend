
class StructType:
    def __init__(self, value, label):
        self.value = value
        self.label = label

class Struct:
    def __init__(self, free, structure, size, amount):
        self.free = free
        self.structure = structure
        self.size = size
        self.amount = amount