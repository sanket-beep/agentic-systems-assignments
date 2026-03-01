class StudentMarks:
    def __init__(self, marks):
        self.marks = marks

    def last_three_avg(self):
        if len(self.marks) < 3:
            raise ValueError("Not enough marks to calculate average")
        last_three_marks = self.marks[-3:]
        average_marks = sum(last_three_marks) / len(last_three_marks)
        return average_marks
    
marks = input("Enter marks separated by space: ").split()
marks = [float(mark) for mark in marks]

Student1 = StudentMarks(marks)

print(Student1.last_three_avg())