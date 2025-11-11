import pandas as pd

data = [
    ("Tell me my exam hall", "get_exam_hall"),
    ("Where is my exam hall?", "get_exam_hall"),
    ("What is my exam room?", "get_exam_hall"),
    ("Which hall am I sitting in?", "get_exam_hall"),
    ("Can you tell me where my exam will be?", "get_exam_hall"),
    ("I want to know my exam hall", "get_exam_hall"),
    ("Where do I have to go for my exam?", "get_exam_hall"),
    ("Find my hall for the exam", "get_exam_hall"),
    ("In which room is my exam scheduled?", "get_exam_hall"),
    ("Please tell my exam hall", "get_exam_hall"),
    ("Where is my seat for the maths exam?", "get_seat_location"),
    ("Tell me my bench for physics", "get_seat_location"),
    ("What is my seat number?", "get_seat_location"),
    ("Find my seating arrangement?", "get_seat_location"),
    ("Where will I sit for chemistry?", "get_seat_location"),
    ("Show me my seat number", "get_seat_location"),
    ("Where is my bench in the exam hall?", "get_seat_location"),
    ("Tell me my seat in hall 3", "get_seat_location"),
    ("What seat have I been given?", "get_seat_location"),
    ("I forgot my seat number", "get_seat_location"),
    ("When is my next exam?", "get_exam_schedule"),
    ("Tell me my exam timetable", "get_exam_schedule"),
    ("Which exam do I have today?", "get_exam_schedule"),
    ("When is the English paper?", "get_exam_schedule"),
    ("Show me my exam dates", "get_exam_schedule"),
    ("What exam do I have tomorrow?", "get_exam_schedule"),
    ("What exam do I have tomorrow?", "get_exam_schedule"),
    ("When will I write the physics exam?", "get_exam_schedule"),
    ("Give me my exam schedule", "get_exam_schedule"),
    ("How many benches are in hall 2?", "get_hall_info"),
    ("Tell me the capacity of hall 5", "get_hall_info"),
    ("Show me all the classrooms", "get_hall_info"),
    ("Which hall has the most benches?", "get_hall_info"),
    ("List all available exam halls", "get_hall_info"),
    ("How many students can sit in hall 3?", "get_hall_info"),
    ("Give me information about hall 1", "get_hall_info"),
    ("Show hall details", "get_hall_info"),
    ("Tell me the total benches in classroom A", "get_hall_info"),
    ("How big is hall 4?", "get_hall_info"),
]


df = pd.DataFrame(data, columns=["text", "intent"])
df.to_csv("exam_queries.csv", index=False)
print("Dataset saved as exam_queries.csv ✅")
