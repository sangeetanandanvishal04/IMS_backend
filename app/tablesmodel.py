from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP, text, Date
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    role = Column(String, nullable=False)  # Role of the user (e.g., 'student', 'professor')

class OTP(Base):
    __tablename__ = 'otps'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, ForeignKey('users.email'))
    otp = Column(String, nullable=False)

class Student(Base):
    __tablename__ = 'students'

    roll_number = Column(String,primary_key= True, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    second_name = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)
    registration_number = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    admission_class = Column(String, nullable=True)
    date_of_admission = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    current_semester = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    mother_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    percentage_attendance = Column(String, nullable=True)
    
    @property
    def name(self):
        return f"{self.first_name} {self.second_name}"

    user = relationship("User", backref="student")

class Professor(Base):
    __tablename__ = 'professors'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    cabin_number = Column(Integer, nullable=False)
    father_name = Column(String, nullable=False)
    mother_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    about_me = Column(String, nullable=True)

    user = relationship("User", backref="professor")

class Section(Base):
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_name = Column(String, nullable=False)
    department = Column(String, nullable=False)

class Lecture(Base):
    __tablename__ = 'lectures'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject = Column(String, index=True)
    professor_id = Column(Integer, ForeignKey('professors.id'))
    section_id = Column(Integer, ForeignKey('sections.id'))

    professor = relationship("Professor", backref="lectures")
    section = relationship("Section", backref="lectures")

class Attendance(Base):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_roll_number = Column(String, ForeignKey('students.roll_number'))
    lecture_id = Column(Integer, ForeignKey('lectures.id'))
    present = Column(Boolean, default=False)
    date = Column(Date, server_default=text('now()'))

    lecture = relationship("Lecture", backref="attendance")
    student = relationship("Student", backref="attendance")

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
    roll_no = Column(String, nullable=False)
    subject_name = Column(String, nullable=False)
    c1 = Column(String, nullable=False)
    c2 = Column(String, nullable=False)
    c3 = Column(String, nullable=False)
    total = Column(String, nullable=False)
    gpa = Column(String, nullable=False)
    credits = Column(String, nullable=False)

#Time table for exam
class DateSheet(Base):
    __tablename__ = 'date_sheet'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    current_semester = Column(String, nullable=False)
    date_of_exam = Column(String, index=True)
    day_of_exam = Column(String, index=True)
    subject = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    time = Column(String, nullable=False)

#Time table for regular classes complete please
class Timetable(Base):
    __tablename__ = 'timetable'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    semester = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)  
    day = Column(String, index=True)
    time = Column(String)
    subject = Column(String) 
    section = Column(String, nullable=True)

#complete this frontend
class Holiday(Base):
    __tablename__ = 'holidays'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, index=True)
    day = Column(String, index=True)
    name = Column(String, index=True)

class Notes(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title1 = Column(String, nullable=False)
    content1 = Column(String, nullable=False)
    title2 = Column(String, nullable=False)
    content2 = Column(String, nullable=False)