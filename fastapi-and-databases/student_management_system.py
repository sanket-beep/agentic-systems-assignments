from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text
from sqlalchemy import CheckConstraint

# Database connection (replace with your details)
engine = create_engine('mysql+pymysql://username:password@localhost/student_db', echo=True)

# Create metadata and connect
meta = MetaData()
conn = engine.connect()

# Drop table if exists (for clean demo)
conn.execute(text("DROP TABLE IF EXISTS students"))

# Define students table with constraints
students = Table(
    'students', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),
    Column('age', Integer, nullable=False),
    Column('city', String(255), nullable=True),
    CheckConstraint('age >= 18', name='check_age_18_plus')
)

# Create table
meta.create_all(engine)
print("Students table created successfully.")

# Insert 3 student records (including Rahul, one under 20 for delete test)
insert_stmt = students.insert()
data = [
    {'name': 'Rahul', 'age': 19, 'city': 'Delhi'},
    {'name': 'Priya', 'age': 22, 'city': 'Mumbai'},
    {'name': 'Amit', 'age': 25, 'city': None}
]
conn.execute(insert_stmt, data)
conn.commit()
print("Inserted 3 student records.")

# Fetch all students
select_all = students.select()
result = conn.execute(select_all)
students_data = result.fetchall()
print("\nAll students:")
for row in students_data:
    print(row)
print("")

# Update city of student whose name = "Rahul"
update_stmt = students.update().where(students.c.name == 'Rahul').values(city='Bangalore')
conn.execute(update_stmt)
conn.commit()
print("Updated Rahul's city to 'Bangalore'.")

# Fetch all after update
result = conn.execute(select_all)
print("All students after update:")
for row in result.fetchall():
    print(row)
print("")

# Delete student whose age < 20 (deletes Rahul)
delete_stmt = students.delete().where(students.c.age < 20)
conn.execute(delete_stmt)
conn.commit()
print("Deleted students with age < 20.")

# Fetch final students
result = conn.execute(select_all)
print("Final students (after delete):")
for row in result.fetchall():
    print(row)

conn.close()