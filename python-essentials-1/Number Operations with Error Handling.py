try:
    num1_input = input("Enter the first number: ")
    num2_input = input("Enter the second number: ")

    num1 = int(num1_input)
    num2 = int(num2_input)

    print(f"Sum: {num1 + num2}")

    try:
        print(f"Division: {num1 / num2}")
    except ZeroDivisionError:
        print("Cannot divide by zero")

except ValueError:
    print("Invalid input")