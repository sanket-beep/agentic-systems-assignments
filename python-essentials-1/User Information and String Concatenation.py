first_name = input("Enter your first name: ")
last_name = input("Enter your last name: ")

age_input = input("Enter your age: ")

try:
    age = int(age_input)

    if age < 0:
        print("Age cannot be negative")
    else:
        full_name = first_name + " " + last_name
        print("Full Name: " + full_name)
        
        age_next_year = age + 1
        print("You will be " + str(age_next_year) + " next year")
        
except ValueError:
    print("Invalid age input")