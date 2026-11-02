from app.main import StudentIn, ClubIn, VenueIn, EventIn

def test_student_validation():
    x=StudentIn(name='A Student',email='a@uvce.edu',department='ISE',year_of_study=2,enrollment_date='2025-08-01')
    assert x.year_of_study == 2

def test_invalid_year():
    try: StudentIn(name='A Student',email='a@uvce.edu',department='ISE',year_of_study=8,enrollment_date='2025-08-01')
    except Exception: return
    assert False, 'year validation should fail'
