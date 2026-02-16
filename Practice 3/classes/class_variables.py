class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model
car1 = Car("Toyota", "Corolla")
print(car1.brand)
print(car1.model)

class Student:
    def __init__(self, name, gpa):
        self.name = name
        self.gpa = gpa
student1 = Student("Neymar", "3.7")
student2 = Student("Messi", "4")
print(student1.name)
print(student1.gpa)
print(student2.name)
print(student2.gpa)
del student1.name

class Person:
    lastname = ""
    def __init__(self, name):
        self.name = name
p1 = Person("Linus")
p2 = Person("Emil")
Person.lastname = "Refsnes"#When you modify a class property, it affects all objects:
print(p1.lastname)
print(p2.lastname)

class Person:
    def __init__(self, name):
        self.name = name
p1 = Person("Tobias")
p1.age = 25
p1.city = "Oslo"
print(p1.name)
print(p1.age)
print(p1.city)