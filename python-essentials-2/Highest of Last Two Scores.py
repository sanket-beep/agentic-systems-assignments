class StudentScores:
    def __init__(self, scores):
        self.scores = scores

    def highest_score(self):
        if len(self.scores) < 2:
            raise ValueError("Not enough scores to determine highest")
        last_two_scores = self.scores[-2:]
        return max(last_two_scores)
    
scores = input("Enter scores separated by space: ").split()
scores = [float(score) for score in scores]

student1 = StudentScores(scores)

print(f"Highest score among last two is: {student1.highest_score()}")