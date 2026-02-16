class A:
    def show(self):
        print("Class A")
class B:
    def show(self):
        print("Class B")
class C(A, B):
    pass
x = C()
x.show()

class Mother:
    def skills(self):
        print("Cooking")
class Father:
    def skills(self):
        print("Gardening")
class Child(Mother, Father):
    def skills(self):
        Mother.skills(self)
        Father.skills(self)
        print("Painting")
x = Child()
x.skills()


class Engine:
    def start(self):
        print("Engine starts")
class Wheels:
    def rotate(self):
        print("Wheels are rotating")
class Car(Engine, Wheels):
    def drive(self):
        self.start()
        self.rotate()
        print("Car is driving")
x = Car()
x.drive()

