try:
    name = input("Enter your name: ")
    age_input = input("Enter your age: ")
    
    age = int(age_input)
    
    if age < 0:
        print("Age cannot be negative")
    else:
        print(f"Hello {name}")
        
        if age < 13:
            print("You are a Child")
        elif 13 <= age <= 17:
            print("You are a Teenager")
        elif 18 <= age <= 59:
            print("You are an Adult")
        else:  # age >= 60
            print("You are a Senior Citizen")
        
        if age >= 18:
            print("You are eligible to vote")
        else:
            print("You are not eligible to vote")

except ValueError:
    print("Invalid age input")