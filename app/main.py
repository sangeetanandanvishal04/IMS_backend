from fastapi import FastAPI,status,HTTPException,Depends
from .database import get_db,engine
from sqlalchemy.orm import Session
from . import schemas,tablesmodel,utils,oAuth2
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import difflib
from typing import Optional

app = FastAPI()

#origins = ["www.youtube.com", "www.google.com"]
origins=["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tablesmodel.Base.metadata.create_all(bind = engine)

@app.get("/")
def root():
    return {"message" : "Welcome to my API...."}

""" {
    "email": "email@iiita.ac.in",
    "password": "password",
    "role": "student"
} """
@app.post("/signup", response_model=schemas.UserOut)
async def create_user(user:schemas.UserCreate,db: Session = Depends(get_db)):
    
    user_found = db.query(tablesmodel.User).filter(tablesmodel.User.email==user.email).first()

    if user_found:
       raise HTTPException(status_code=status.HTTP_302_FOUND, detail="Email already exists")
    
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = tablesmodel.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user   

""" {
    "email": "email@iiita.ac.in",
    "password": "password"
} """
@app.post("/login")
async def loginPage(user_credentials:schemas.UserLogin ,db: Session = Depends(get_db)):

    user = db.query(tablesmodel.User).filter(tablesmodel.User.email==user_credentials.email).first()

    if not user:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")
    
    access_token = oAuth2.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "Bearer"}

""" {
    "old_password": "password",
    "new_password": "vishal04",
    "confirm_password": "vishal04"
} """
#Change Password
@app.post("/change-password")
async def change_password(password_data: schemas.PasswordChange,db: Session = Depends(get_db),current_user: tablesmodel.User = Depends(oAuth2.get_current_user)):
    
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="UnAuthorized to perform")

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="New password and confirm password do not match")

    if not utils.verify(password_data.old_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Old password is incorrect")

    hashed_password = utils.hash(password_data.new_password)
    current_user.password = hashed_password
    db.commit()

    return {"message": "Password updated successfully"}


#http://127.0.0.1:8000/forgot-password/email@iiita.ac.in
#forget password logic
@app.post("/forgot-password/{email}")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(tablesmodel.User).filter(tablesmodel.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")

    otp = utils.generate_otp()

    db_otp = tablesmodel.OTP(email=email, otp=otp)
    db.add(db_otp)
    db.commit()

    utils.send_email(email, otp)

    return {"message": "OTP sent successfully"}

@app.post("/resend-otp/{email}")
async def resend_otp(email: str, db: Session = Depends(get_db)):
    user = db.query(tablesmodel.User).filter(tablesmodel.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email does not exist")

    db.query(tablesmodel.OTP).filter(tablesmodel.OTP.email==email).delete(synchronize_session=False)
    db.commit()

    otp = utils.generate_otp()

    db_otp = tablesmodel.OTP(email=email, otp=otp)
    db.add(db_otp)
    db.commit()

    utils.send_email(email, otp)

    return {"message": "OTP resend successfully"}

""" {
    "email": "email@iiita.ac.in",
    "otp": "5294"
} """
@app.post("/otp-verification")
async def reset_password(otp_data: schemas.OTP, db: Session = Depends(get_db)):
    user = db.query(tablesmodel.User).filter(tablesmodel.User.email == otp_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    otp_record = db.query(tablesmodel.OTP).filter(tablesmodel.OTP.email == otp_data.email).first()
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP not found")
    
    if otp_data.otp != otp_record.otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")
    
    db.delete(otp_record)
    db.commit()

    return {"message": "OTP is correct"}

""" {
    "email": "email@iiita.ac.in",
    "new_password": "password",
    "confirm_password": "password"
} """
@app.post("/reset-password")
async def reset_password(password_data: schemas.PasswordReset, db: Session = Depends(get_db)):
    user = db.query(tablesmodel.User).filter(tablesmodel.User.email == password_data.email).first()

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password and confirm password do not match")

    hashed_password = utils.hash(password_data.new_password)
    user.password = hashed_password

    db.commit()

    return {"message": "Password reset successfully"}

@app.get("/student-details")
async def get_student_details(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    student = db.query(tablesmodel.Student).filter(tablesmodel.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    return student

@app.get("/professor-details")
async def get_professor_details(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    professor = db.query(tablesmodel.Professor).filter(tablesmodel.Professor.user_id == current_user.id).first()
    if not professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor not found")
    
    return professor

# Teacher to get attendance list
@app.get("/attendance-list", response_model=list[dict])
async def get_attendance_list(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    professor = db.query(tablesmodel.Professor).filter(tablesmodel.Professor.user_id == current_user.id).first()
    if not professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor not found")
    
    section = db.query(tablesmodel.Section).filter(tablesmodel.Section.department == professor.department).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found for professor")

    students = db.query(tablesmodel.Student).filter(tablesmodel.Student.admission_class == section.section_name).all()
    if not students:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No students found in the section")
    
    attendance_list = [{"name": student.name, "roll_number": student.roll_number, "present": False} for student in students]
    return attendance_list

#By teacher(on submitted, attendence is stored in database)
""" [
    {
        "roll_number": "IFI2022006",
        "present": true
    },
    {
        "roll_number": "IFI2022003",
        "present": true
    }
] """
# By teacher (on submitted, attendance is stored in database)
@app.post("/submit-attendance")
async def submit_attendance(attendance_list: list[dict], current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UnAuthorized to perform action")

    professor = db.query(tablesmodel.Professor).filter(tablesmodel.Professor.user_id == current_user.id).first()
    if not professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor not found")
    
    lecture = db.query(tablesmodel.Lecture).filter(tablesmodel.Lecture.professor_id == professor.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found for this professor")

    for attendance_data in attendance_list:
        try:
            roll_number = attendance_data["roll_number"]
            present = attendance_data["present"]
            attendance_date = attendance_data.get("date", date.today())

            student = db.query(tablesmodel.Student).filter(tablesmodel.Student.roll_number == roll_number).first()
            if not student:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with Roll Number {roll_number} not found")

            existing_attendance = db.query(tablesmodel.Attendance).filter(
                tablesmodel.Attendance.student_roll_number == roll_number,
                tablesmodel.Attendance.lecture_id == lecture.id,
                tablesmodel.Attendance.date == attendance_date
            ).first()

            if existing_attendance:
               raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Attendance for Roll Number {roll_number} in Lecture {lecture.id} on {attendance_date} already exists")

            attendance = tablesmodel.Attendance(student_roll_number=roll_number, lecture_id=lecture.id, present=present, date=attendance_date)
            db.add(attendance)

        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    db.commit()

    return {"message": "Attendance marked successfully"}

#By Student to get attendence status
@app.get("/student-attendance")
async def get_student_attendance(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    student = db.query(tablesmodel.Student).filter(tablesmodel.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    attendance_data = []
    
    section_id = db.query(tablesmodel.Section.id).filter(tablesmodel.Section.section_name == student.admission_class).first()
    if not section_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

    section_id = section_id[0]

    subjects = db.query(tablesmodel.Lecture.subject).filter(tablesmodel.Lecture.section_id == section_id).all()
    for subject in subjects:
        subject_name = subject[0]
        total_days = db.query(func.count(tablesmodel.Attendance.id)).join(tablesmodel.Lecture).filter(
            tablesmodel.Lecture.subject == subject_name,  
            tablesmodel.Attendance.student_roll_number == student.roll_number
        ).scalar()

        present_days = db.query(func.count(tablesmodel.Attendance.id)).join(tablesmodel.Lecture).filter(
            tablesmodel.Lecture.subject == subject_name,
            tablesmodel.Attendance.student_roll_number == student.roll_number,
            tablesmodel.Attendance.present == True
        ).scalar()

        percentage_attendance = (present_days / total_days) * 100 if total_days > 0 else 0

        attendance_data.append({
            "subject": subject_name,
            "total_days": total_days,
            "present_days": present_days,
            "percentage_attendance": round(percentage_attendance, 2)
        })

    return attendance_data

@app.get("/holidays")
async def get_holidays(db: Session = Depends(get_db)):
    holidays = db.query(tablesmodel.Holiday).all()

    if not holidays:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="list of holidays is not found in database")
    
    return holidays

#timetable of exams
@app.get("/datesheet")
async def get_datesheet(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):
    
    user_email = db.query(tablesmodel.User.email).filter(tablesmodel.User.id == current_user.id).scalar()

    if not user_email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"email not found for id {current_user.id}")
    
    user_detail = db.query(tablesmodel.Student).filter(tablesmodel.Student.email == user_email).first()

    if not user_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"branch and current semester not found for email {user_email}")
    
    datesheet = db.query(tablesmodel.DateSheet).filter(tablesmodel.DateSheet.branch == user_detail.branch_name, tablesmodel.DateSheet.current_semester == user_detail.current_semester).all()

    if not datesheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Date Sheet is not available")
    
    return datesheet

#By Student(regular classes)
@app.get("/timetable")
async def get_timetable(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):

    user_email = db.query(tablesmodel.User.email).filter(tablesmodel.User.id == current_user.id).scalar()

    if not user_email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"email not found for id {current_user.id}")
    
    user_detail = db.query(tablesmodel.Student).filter(tablesmodel.Student.email == user_email).first()

    if not user_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"branch and current semester not found for email {user_email}")
    
    timetable_data = db.query(tablesmodel.Timetable).filter(tablesmodel.Timetable.branch_name == user_detail.branch_name, tablesmodel.Timetable.semester == user_detail.current_semester).all()
    
    if not timetable_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time table is not available")
    
    return timetable_data

#By Student
@app.get("/results")
async def get_result(current_user: tablesmodel.User = Depends(oAuth2.get_current_user), db: Session = Depends(get_db)):

    user_email = db.query(tablesmodel.User.email).filter(tablesmodel.User.id == current_user.id).scalar()

    if not user_email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"email not found for id {current_user.id}")

    roll_number = db.query(tablesmodel.Student.roll_number).filter(tablesmodel.Student.email == user_email).scalar()

    if not roll_number:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"roll number not found for email {user_email}")
    
    student_result = db.query(tablesmodel.Result).filter(tablesmodel.Result.roll_no == roll_number).all()

    if not student_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"result of {roll_number} is not found")
    
    return student_result

def find_closest_match(query: str, text: str) -> bool:
    query_words = query.split()
    text_words = text.split()
    for query_word in query_words:
        matches = difflib.get_close_matches(query_word, text_words)
        if not matches:
            return False
    return True

@app.get("/find-notes", response_model=schemas.NotesOut)
def get_notes(db: Session = Depends(get_db), search: Optional[str] = ""):
    retrieved_content = db.query(tablesmodel.Notes.title1, tablesmodel.Notes.content1,
                                    tablesmodel.Notes.title2, tablesmodel.Notes.content2).all()

    for row in retrieved_content:
        if find_closest_match(search.lower(), row[0].lower()): 
            note = schemas.NotesOut(title1=row[0], content1=row[1], title2=row[2], content2=row[3])
            return note  
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notes not found")

@app.get("/find-notes/{id}", response_model=schemas.NotesOut)
def get_notes(id: int, db: Session = Depends(get_db)):
    notes = db.query(tablesmodel.Notes).filter(tablesmodel.Notes.id == id).first()
    return notes