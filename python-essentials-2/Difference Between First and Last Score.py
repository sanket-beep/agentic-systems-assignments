class StudentPerformance:
    def __init__(self, scores):
        self.scores = scores
        
    def score_difference(self):
        if not self.scores:
            raise ValueError("Not enough scores to calculate difference")
        first_score = self.scores[0]
        last_score = self.scores[-1]
        return last_score - first_score
    
scores = input("Enter scores separated by space: ").split()
scores = [float(score) for score in scores]

student = StudentPerformance(scores)
print(f"Difference between last and first score is: {student.score_difference()}")