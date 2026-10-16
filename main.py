import json
from abc import ABC, abstractmethod
from pathlib import Path
database = "school_data.json"
data = {"students": [], "teachers" : []}
if Path(database).exists():
    with open(database,'r') as f:
        content = f.read()
        if content:
            data = json.loads(content)
def save():
    with open(database,'w') as f:
        json.dump(data,f,indent=4)

class Persons(ABC):
    @abstractmethod
    def get_roles(self):
        pass
    @abstractmethod
    def register(self):
        pass
    @abstractmethod
    def show_details(self):
        pass
    @staticmethod
    def vaildate_email(email):
        if '@' in email and "." in email:
            return True
        else:
            return False
        

class Student(Persons):
    def get_roles(self):
        return Student
    def register(self):
        name = input("Tell your name:- ")
        age = int (input("Tell age :- "))
        email = input("Tell your mail:- ")
        roll_no = int (input ("Tell you roll no. :- "))
        if not Persons.vaildate_email(email):
            print("Invail email")
            return 
        for i in data["students"]:
            if i['roll_no'] == roll_no:
                print("Student is already exist")
                return 
        data['students'].append({ "name" : name,
                                 "age":age,
                                 "email":email,
                                "roll_no":roll_no,
                                "grades" : {}
                                })
        save()
        print(f"Student {name} is registered")



    def show_details(self):
        roll_no = int(input("Tell roll no. :- "))
        for i in data["students"]:
            if i["roll_no"]==roll_no:
                grades=i["grades"]
                avg = sum(grades.values()) / len(grades) if grades else 0

                print(f"\n Name : {i["name"]}")
                print(f"\n Age : {i["age"]}")
                print(f"\n Grades : {i["grades"]}")
                print(f"\n Avg : {avg:.1f}")
                return


    def add_grades(self):
        roll_no = int(input("Tell you roll no. :- "))
        subject = input("Subject:- ")
        marks = float(input("Marks:- "))
        for i in data["students"]:
            if i["roll_no"]==roll_no:
                i["grades"][subject]=marks
                save()
                print("Grade add successfully")
                return
        print("Student is found")







class Teacher(Persons):
    def get_roles(self):
        return Teacher
    def register(self):
        name = input("Tell your name:- ")
        age = int (input("Tell age :- "))
        email = input("Tell your mail:- ")
        emp_id = int (input ("Tell you emp id no. :- "))
        subject = input("Tell your subject name:- ")
        if not Persons.vaildate_email(email):
            print("Invail email")
            return
        for i in data["teachers"]:
                    if i['emp_id'] == emp_id:
                        print("Teacher is already exist")
                        return 
        data['teachers'].append({ "name" : name,
                                 "age":age,
                                 "email":email,
                                 "emp_id":emp_id,
                                 "subject":subject,
                                        })
        save()
        print(f"Teachers {name} is registered")


    def show_details(self):
        emp_id = int(input("Tell emp id. :- "))
        for i in data["teachers"]:
            if i["emp_id"]==emp_id:
                        print(f"\n Name : {i["name"]}")
                        print(f"\n Emp-id : {i["emp_id"]}")
                        print(f"\n Subject : {i["subject"]}")
                        return
        print("Teacher is found")
    
stud=Student()
tech=Teacher()





print("Press 1  to register a student")
print("Press 2 to register a teacher")
print("Press 3 to show student grades")
print("Press 4 to show student details")
print("Press 5 to show teacher details")

choice = int(input("Tell your choice:- "))
if choice == 1:
    stud.register()
elif choice == 2:
    tech.register()
elif choice == 3:
    stud.add_grades()
elif choice == 4:
    stud.show_details()
elif choice == 5:
    tech.show_details()