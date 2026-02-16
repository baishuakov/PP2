class Person:
    def __init__(self, fname, lname):
        self.firstname = fname
        self.lastname = lname

    def printname(self):
        print(self.firstname, self.lastname)

class Student(Person):
    def __init__(self, fname, lname):
        super().__init__(fname, lname)

x = Student("Mike", "Olsen")
x.printname()

class Person:
    def __init__(self, name):
        self.name = name
    def greet(self):
        print("Hello, my name is", self.name)
class Student(Person):
    def __init__(self, name, grade):
        super().__init__(name) 
        self.grade = grade      
    def greet(self):
        print(f"Hello, my name is {self.name} and I am in grade {self.grade}")
x = Student("Mike", 10)
x.greet()

