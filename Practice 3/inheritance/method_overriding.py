class Animal:
    def sound(self):
        print("Some sound")
class Dog(Animal):
    def sound(self):
        print("Woof")
a = Animal()
a.sound()
d = Dog()
d.sound()

class Vehicle:
    def move(self):
        print("Vehicle moves")
class Car(Vehicle):
    def move(self):
        print("Car drives")
v = Vehicle()
v.move()
c = Car()
c.move()

class Person:
    def greet(self):
        print("Hello!")
class Student(Person):
    def greet(self):
        super().greet()
        print("I am a student.")
x = Student()
x.greet()

