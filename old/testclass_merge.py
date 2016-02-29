__author__ = 'Kristy'
class Animal():
    @staticmethod
    def makewoof(int):
        return 'woof'*int

    @staticmethod
    def makebowow(int):
        return 'bowow'* int

    bark= {1:makewoof, 0:makebowow}

    def __init__(self, age):
        self.age= age
        self.name='tiertier'
        self.sound = Animal.bark[self.age % 2].__get__(self)




a = Animal(10)
print(a.sound(5))
b = Animal(21)
print(b.sound(2))

