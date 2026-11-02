from contextlib import asynccontextmanager
import os
import aiomysql
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

DB = dict(host=os.getenv('MYSQL_HOST','localhost'), port=int(os.getenv('MYSQL_PORT','3306')), user=os.getenv('MYSQL_USER','campusconnect'), password=os.getenv('MYSQL_PASSWORD','campusconnect'), db=os.getenv('MYSQL_DATABASE','campusconnect'), autocommit=True, minsize=1, maxsize=10, charset='utf8mb4', cursorclass=aiomysql.DictCursor)
@asynccontextmanager
async def lifespan(app):
    app.state.pool = await aiomysql.create_pool(**DB)
    yield
    app.state.pool.close(); await app.state.pool.wait_closed()
app=FastAPI(title='CampusConnect API',version='1.0.0',description='Student Club & Event Management System',lifespan=lifespan)
origins=os.getenv('FRONTEND_ORIGIN','http://localhost:5173,http://localhost:3000').split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

class StudentIn(BaseModel):
    name:str=Field(min_length=2,max_length=120); email:str; phone:str|None=None; department:str; year_of_study:int=Field(ge=1,le=6); enrollment_date:str
class ClubIn(BaseModel):
    club_name:str; description:str|None=None; category:str='OTHER'; date_founded:str|None=None; status:str='ACTIVE'
class VenueIn(BaseModel):
    venue_name:str; building:str; room_number:str|None=None; capacity:int=Field(gt=0); venue_type:str='OTHER'
class EventIn(BaseModel):
    club_id:int; venue_id:int; event_name:str; description:str|None=None; event_date:str; start_time:str; end_time:str; capacity:int=Field(gt=0); registration_deadline:str
class JoinIn(BaseModel): student_id:int
class OfficerIn(BaseModel): student_id:int; role:str
class AttendanceIn(BaseModel): attendance:Literal['PENDING','PRESENT','ABSENT']
class FeedbackIn(BaseModel): student_id:int; rating:int=Field(ge=1,le=5); comments:str|None=None

async def fetch(sql,args=None,one=False):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(sql,args or ())
                if sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')): return {'lastrowid':cur.lastrowid,'rowcount':cur.rowcount}
                return await (cur.fetchone() if one else cur.fetchall())
            except aiomysql.MySQLError as e:
                errno=e.args[0] if e.args else 0
                status={51001:404,51002:409,51003:422,1062:409,1451:409,1452:404}.get(errno,400)
                raise HTTPException(status_code=status,detail=str(e.args[-1] if e.args else e))
async def proc(name,args):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.callproc(name,args); rows=await cur.fetchall()
                while await cur.nextset(): pass
                return rows
            except aiomysql.MySQLError as e:
                errno=e.args[0] if e.args else 0
                raise HTTPException(status_code={51001:404,51002:409,51003:422,1062:409,1452:404}.get(errno,400),detail=str(e.args[-1] if e.args else e))
def page(rows): return {'total':len(rows),'items':rows}
@app.get('/health')
async def health():
    await fetch('SELECT 1 AS ok',one=True); return {'status':'ok','database':'up'}
@app.get('/api/v1/health')
async def api_health(): return await health()

# Dashboard + reports (views are the reporting layer used by the DBMS project)
@app.get('/api/v1/reports/dashboard')
async def dashboard():
    return await fetch("SELECT (SELECT COUNT(*) FROM students) students,(SELECT COUNT(*) FROM clubs WHERE status='ACTIVE') active_clubs,(SELECT COUNT(*) FROM events) events,(SELECT COUNT(*) FROM events WHERE event_status IN ('UPCOMING','ONGOING')) upcoming_events,(SELECT COUNT(*) FROM event_registrations WHERE registration_status='REGISTERED') registrations,(SELECT COUNT(*) FROM venues) venues",one=True)
@app.get('/api/v1/reports/{report}')
async def report(report:str,limit:int=Query(10,ge=1,le=100)):
    views={'club-membership':'v_club_membership_counts','club-activity':'v_club_activity_report','officers':'v_club_officers','event-popularity':'v_event_popularity','event-attendance':'v_event_attendance','feedback-summary':'v_event_feedback_summary','top-students':'v_student_activity','upcoming':'v_upcoming_events','venue-utilisation':None,'department-participation':None}
    if report not in views: raise HTTPException(404,'Report not found')
    if report=='venue-utilisation': sql="SELECT v.venue_id,v.venue_name,v.building,v.capacity,COUNT(e.event_id) events_hosted FROM venues v LEFT JOIN events e USING(venue_id) GROUP BY v.venue_id ORDER BY events_hosted DESC"
    elif report=='department-participation': sql="SELECT department,COUNT(*) students,AVG(events_registered) avg_events_registered FROM v_student_activity GROUP BY department ORDER BY students DESC"
    else: sql=f'SELECT * FROM {views[report]}'
    if report in ('event-popularity','top-students','upcoming'): sql+=f' LIMIT {limit}'
    return page(await fetch(sql))

# Students
@app.get('/api/v1/students')
async def students(q:str|None=None,department:str|None=None,year:int|None=None,limit:int=50,offset:int=0):
    sql='SELECT * FROM students WHERE (%s IS NULL OR name LIKE %s OR email LIKE %s) AND (%s IS NULL OR department=%s) AND (%s IS NULL OR year_of_study=%s) ORDER BY student_id DESC LIMIT %s OFFSET %s'
    p=f'%{q}%' if q else None; rows=await fetch(sql,(p,p,p,department,department,year,year,limit,offset)); return page(rows)
@app.get('/api/v1/students/{sid}')
async def student(sid:int):
    row=await fetch('SELECT * FROM students WHERE student_id=%s',(sid,),True)
    if not row: raise HTTPException(404,'Student not found')
    return row
@app.post('/api/v1/students',status_code=201)
async def add_student(x:StudentIn):
    r=await fetch('INSERT INTO students(name,email,phone,department,year_of_study,enrollment_date) VALUES(%s,%s,%s,%s,%s,%s)',tuple(x.model_dump().values())); return await student(r['lastrowid'])
@app.put('/api/v1/students/{sid}')
async def edit_student(sid:int,x:StudentIn):
    await fetch('UPDATE students SET name=%s,email=%s,phone=%s,department=%s,year_of_study=%s,enrollment_date=%s WHERE student_id=%s',(*x.model_dump().values(),sid)); return await student(sid)
@app.delete('/api/v1/students/{sid}')
async def del_student(sid:int):
    r=await fetch('DELETE FROM students WHERE student_id=%s',(sid,));
    if not r['rowcount']: raise HTTPException(404,'Student not found')
    return {'detail':'Student deleted'}
@app.get('/api/v1/students/{sid}/clubs')
async def student_clubs(sid:int): return page(await fetch('SELECT cm.*,c.club_name FROM club_memberships cm JOIN clubs c USING(club_id) WHERE student_id=%s',(sid,)))
@app.get('/api/v1/students/{sid}/registrations')
async def student_regs(sid:int): return page(await fetch('SELECT r.*,e.event_name,e.event_date,c.club_name FROM event_registrations r JOIN events e USING(event_id) JOIN clubs c USING(club_id) WHERE r.student_id=%s',(sid,)))

# Clubs and membership
@app.get('/api/v1/clubs')
async def clubs(q:str|None=None,category:str|None=None,status:str|None=None):
    p=f'%{q}%' if q else None; return page(await fetch('SELECT c.*,COALESCE(v.active_members,0) active_members FROM clubs c LEFT JOIN v_club_membership_counts v USING(club_id) WHERE (%s IS NULL OR c.club_name LIKE %s) AND (%s IS NULL OR c.category=%s) AND (%s IS NULL OR c.status=%s) ORDER BY c.club_name',(p,p,category,category,status,status)))
@app.post('/api/v1/clubs',status_code=201)
async def add_club(x:ClubIn):
    r=await fetch('INSERT INTO clubs(club_name,description,category,date_founded,status) VALUES(%s,%s,%s,%s,%s)',tuple(x.model_dump().values())); return await fetch('SELECT * FROM clubs WHERE club_id=%s',(r['lastrowid'],),True)
@app.get('/api/v1/clubs/{cid}')
async def club(cid:int):
    r=await fetch('SELECT * FROM clubs WHERE club_id=%s',(cid,),True)
    if not r: raise HTTPException(404,'Club not found')
    return r
@app.put('/api/v1/clubs/{cid}')
async def edit_club(cid:int,x:ClubIn):
    await fetch('UPDATE clubs SET club_name=%s,description=%s,category=%s,date_founded=%s,status=%s WHERE club_id=%s',(*x.model_dump().values(),cid)); return await club(cid)
@app.delete('/api/v1/clubs/{cid}')
async def del_club(cid:int):
    r=await fetch('DELETE FROM clubs WHERE club_id=%s',(cid,));
    if not r['rowcount']: raise HTTPException(404,'Club not found')
    return {'detail':'Club deleted'}
@app.get('/api/v1/clubs/{cid}/members')
async def members(cid:int,status:str|None=None): return page(await fetch('SELECT cm.*,s.name,s.email,s.department,s.year_of_study FROM club_memberships cm JOIN students s USING(student_id) WHERE club_id=%s AND (%s IS NULL OR membership_status=%s) ORDER BY s.name',(cid,status,status)))
@app.post('/api/v1/clubs/{cid}/members',status_code=201)
async def join(cid:int,x:JoinIn): return (await proc('sp_join_club',(x.student_id,cid)))[0]
@app.patch('/api/v1/memberships/{mid}')
async def membership_status(mid:int,status:Literal['ACTIVE','INACTIVE']):
    await fetch("UPDATE club_memberships SET membership_status=%s,membership_role=IF(%s='ACTIVE',membership_role,'MEMBER') WHERE membership_id=%s",(status,status,mid)); row=await fetch('SELECT * FROM club_memberships WHERE membership_id=%s',(mid,),True)
    if not row: raise HTTPException(404,'Membership not found')
    return row
@app.post('/api/v1/memberships/{mid}/leave')
async def leave(mid:int): return (await proc('sp_leave_club',(mid,)))[0]
@app.get('/api/v1/clubs/{cid}/officers')
async def officers(cid:int): return page(await fetch('SELECT * FROM v_club_officers WHERE club_id=%s',(cid,)))
@app.put('/api/v1/clubs/{cid}/officers')
async def assign(cid:int,x:OfficerIn): return page(await proc('sp_assign_officer',(cid,x.student_id,x.role)))
@app.get('/api/v1/clubs/{cid}/events')
async def club_events(cid:int): return page(await fetch('SELECT * FROM v_event_overview WHERE club_id=%s ORDER BY event_date DESC',(cid,)))

# Venues
@app.get('/api/v1/venues')
async def venues(q:str|None=None,venue_type:str|None=None):
    p=f'%{q}%' if q else None; return page(await fetch('SELECT * FROM venues WHERE (%s IS NULL OR venue_name LIKE %s OR building LIKE %s) AND (%s IS NULL OR venue_type=%s) ORDER BY venue_name',(p,p,p,venue_type,venue_type)))
@app.post('/api/v1/venues',status_code=201)
async def add_venue(x:VenueIn):
    r=await fetch('INSERT INTO venues(venue_name,building,room_number,capacity,venue_type) VALUES(%s,%s,%s,%s,%s)',tuple(x.model_dump().values())); return await fetch('SELECT * FROM venues WHERE venue_id=%s',(r['lastrowid'],),True)
@app.get('/api/v1/venues/{vid}')
async def venue(vid:int):
    r=await fetch('SELECT * FROM venues WHERE venue_id=%s',(vid,),True)
    if not r: raise HTTPException(404,'Venue not found')
    return r
@app.put('/api/v1/venues/{vid}')
async def edit_venue(vid:int,x:VenueIn):
    await fetch('UPDATE venues SET venue_name=%s,building=%s,room_number=%s,capacity=%s,venue_type=%s WHERE venue_id=%s',(*x.model_dump().values(),vid)); return await venue(vid)
@app.delete('/api/v1/venues/{vid}')
async def del_venue(vid:int):
    r=await fetch('DELETE FROM venues WHERE venue_id=%s',(vid,));
    if not r['rowcount']: raise HTTPException(404,'Venue not found')
    return {'detail':'Venue deleted'}
@app.get('/api/v1/venues/{vid}/events')
async def venue_events(vid:int): return page(await fetch('SELECT * FROM v_event_overview WHERE venue_id=%s',(vid,)))

# Events, registrations, attendance and feedback
@app.get('/api/v1/events')
async def events(status:str|None=None,club_id:int|None=None,venue_id:int|None=None,q:str|None=None,date_from:str|None=None,date_to:str|None=None,limit:int=50,offset:int=0):
    p=f'%{q}%' if q else None; return page(await fetch("SELECT * FROM v_event_overview WHERE (%s IS NULL OR event_status=%s) AND (%s IS NULL OR club_id=%s) AND (%s IS NULL OR venue_id=%s) AND (%s IS NULL OR event_name LIKE %s) AND (%s IS NULL OR event_date >= %s) AND (%s IS NULL OR event_date <= %s) ORDER BY event_date DESC,start_time LIMIT %s OFFSET %s",(status,status,club_id,club_id,venue_id,venue_id,p,p,date_from,date_from,date_to,date_to,limit,offset)))
@app.post('/api/v1/events',status_code=201)
async def add_event(x:EventIn):
    r=await fetch('INSERT INTO events(club_id,venue_id,event_name,description,event_date,start_time,end_time,capacity,registration_deadline) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',tuple(x.model_dump().values())); return await fetch('SELECT * FROM v_event_overview WHERE event_id=%s',(r['lastrowid'],),True)
@app.get('/api/v1/events/{eid}')
async def event(eid:int):
    r=await fetch('SELECT * FROM v_event_overview WHERE event_id=%s',(eid,),True)
    if not r: raise HTTPException(404,'Event not found')
    return r
@app.put('/api/v1/events/{eid}')
async def edit_event(eid:int,x:EventIn):
    await fetch('UPDATE events SET club_id=%s,venue_id=%s,event_name=%s,description=%s,event_date=%s,start_time=%s,end_time=%s,capacity=%s,registration_deadline=%s WHERE event_id=%s',(*x.model_dump().values(),eid)); return await event(eid)
@app.delete('/api/v1/events/{eid}')
async def del_event(eid:int):
    r=await fetch('DELETE FROM events WHERE event_id=%s',(eid,));
    if not r['rowcount']: raise HTTPException(404,'Event not found')
    return {'detail':'Event deleted'}
@app.get('/api/v1/events/{eid}/summary')
async def event_summary(eid:int): return (await proc('sp_event_summary',(eid,)) or [{}])[0]
@app.post('/api/v1/events/{eid}/complete')
async def complete(eid:int): return (await proc('sp_complete_event',(eid,)) or [{}])[0]
@app.post('/api/v1/events/{eid}/cancel')
async def cancel_event(eid:int): return (await proc('sp_cancel_event',(eid,)) or [{}])[0]
@app.get('/api/v1/events/{eid}/roster')
async def roster(eid:int,status:str|None=None): return page(await fetch('SELECT * FROM v_event_roster WHERE event_id=%s AND (%s IS NULL OR registration_status=%s) ORDER BY registered_at',(eid,status,status)))
@app.post('/api/v1/events/{eid}/registrations',status_code=201)
async def register(eid:int,x:JoinIn): return (await proc('sp_register_for_event',(x.student_id,eid)))[0]
@app.post('/api/v1/registrations/{rid}/cancel')
async def cancel_registration(rid:int): return (await proc('sp_cancel_registration',(rid,)) or [{}])[0]
@app.patch('/api/v1/registrations/{rid}/attendance')
async def mark_attendance(rid:int,x:AttendanceIn): return (await proc('sp_mark_attendance',(rid,x.attendance)) or [{}])[0]
@app.get('/api/v1/events/{eid}/feedback')
async def event_feedback(eid:int): return page(await fetch('SELECT f.*,s.name FROM event_feedback f JOIN students s USING(student_id) WHERE event_id=%s ORDER BY submitted_at DESC',(eid,)))
@app.post('/api/v1/events/{eid}/feedback',status_code=201)
async def submit_feedback(eid:int,x:FeedbackIn): return (await proc('sp_submit_feedback',(x.student_id,eid,x.rating,x.comments)))[0]
@app.get('/api/v1/feedback/recent')
async def recent_feedback(limit:int=10): return page(await fetch('SELECT f.*,s.name,e.event_name FROM event_feedback f JOIN students s USING(student_id) JOIN events e USING(event_id) ORDER BY submitted_at DESC LIMIT %s',(limit,)))
