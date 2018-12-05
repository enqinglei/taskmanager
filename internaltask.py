#coding:utf-8
#!/usr/bin/env python

import sys

reload(sys)

sys.setdefaultencoding("utf-8")

from datetime import datetime
from flask import Flask,session, request, flash, url_for, redirect, render_template, abort ,g,send_from_directory,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import login_user , logout_user , current_user , login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine,and_,or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from wtforms import StringField, PasswordField, BooleanField, SubmitField
import xlrd,xlwt
import mysql.connector
import numpy as np
import pandas as pd
from flask import send_file,make_response
from io import BytesIO
import re
import time
import os

from jira import JIRA
from jira.client import JIRA

from os.path import basename
import shutil

import requests
import ldap

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/webapp'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'secret_key'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  
basedir = os.path.abspath(os.path.dirname(__file__)) 
ALLOWED_EXTENSIONS = set(['txt', 'png', 'jpg', 'xls', 'JPG', 'PNG', 'xlsx', 'gif', 'GIF']) 


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/uploadmaterials',methods=['GET', 'POST'], strict_slashes=False)
@login_required
def uploadmaterials():
    if request.method == 'GET':
        #TaskId = request.form['TaskId']
        return render_template('uploadmaterials.html')
    else:
        global gTaskId
        file_dir = os.path.join(basedir, 'materials')
        file_dir = os.path.join(file_dir, gTaskId)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        f = request.files['fileField']
        #if f and allowed_file(f.filename):

        fname = f.filename.replace(' ','_')
        fname =fname.strip()
        todo_item = Todo.query.get(gTaskId)
        todo_item.FileName = fname
        db.session.commit()
        filename = os.path.join(file_dir, fname)
        f.save(filename)
        """
        ext = fname.rsplit('.', 1)[1]
        unix_time = int(time.time())
        new_filename = str(unix_time) + '.' + ext
        filename = os.path.join(file_dir, new_filename)
        print filename
        f.save(os.path.join(file_dir, new_filename))
        """
        flash('Internal task material has been successfully uploaded!!')
        return redirect(url_for('index'))



@app.route('/api/upload', methods=['POST'], strict_slashes=False)
def api_upload():
    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir) 
    f=request.files['fileField']  
    if f and allowed_file(f.filename): 
        fname=f.filename
        ext = fname.rsplit('.', 1)[1] 
        unix_time = int(time.time())
        new_filename = str(unix_time)+'.'+ext
        filename=os.path.join(file_dir, new_filename)
        print filename
        f.save(os.path.join(file_dir, new_filename))
        val=importfromexcel(filename)
        if val==0:
            flash('TaskId has been used! please use the recommanded one', 'error')
            todo=Todo.query.order_by(Todo.TaskId.desc()).first()
            a = re.sub("\D", "", todo.TaskId)
                    #a=filter(str.isdigit, todo.TaskId)
            a=int(a)
            a=a+1
                    
            b=len(str(a))
                    #sr=sr+'m'*(9-len(sr))
            TaskId='MAC'+'0'*(6-b)+ str(a)
            return render_template('new.html'
                                    ,TaskId=TaskId)
        else:
            flash('Internal task item has been successfully imported')
            return redirect(url_for('index'))
    else:
        flash('Invalid Filename!')
        return redirect(url_for('index'))
"""
        return jsonify({"errno": 0, "errmsg": "upload ok"})
    else:
        return jsonify({"errno": 1001, "errmsg": "upload fail"})
"""

db = SQLAlchemy(app)

Base=declarative_base()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column('user_id',db.Integer , primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(250))
    email = db.Column('email',db.String(50),unique=True , index=True)
    registered_on = db.Column('registered_on' , db.DateTime)
    todos = db.relationship('Todo' , backref='user',lazy='select')

    def __init__(self , username ,password , email):
        self.username = username
        self.set_password(password)
        self.email = email
        self.registered_on = datetime.utcnow()

    def set_password(self , password):
        self.password = generate_password_hash(password)

    def check_password(self , password):
        return check_password_hash(self.password , password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

class FusionUser(db.Model):
    __tablename__ = "fusionusers"
    id = db.Column('user_id',db.Integer , primary_key=True)
    username = db.Column('username', db.String(64), unique=True , index=True)
    password = db.Column('password' , db.String(256))
    email = db.Column('email',db.String(128),unique=True , index=True)
    displayName = db.Column(db.String(128))
    lineManagerAccountId = db.Column(db.String(128)) #nsnManagerAccountName
    lineManagerDisplayName = db.Column(db.String(128)) #nsnManagerName
    lineManagerEmail = db.Column(db.String(128)) # Further search thru uid.
    squadGroupName = db.Column(db.String(128))  # Further search thru uid.
    registered_on = db.Column('registered_on' , db.DateTime)

    todos = db.relationship('Todo', backref='fusionuser', lazy='select')
    # jiratodos = db.relationship('JiraTodo', backref='jirauser', lazy='select')
    # todoaps = db.relationship('TodoAP', backref='jirauser', lazy='select')
    # inchargegroups = db.relationship('InChargeGroup', backref='jirauser', lazy='select')

    def __init__(self , username, email,displayName,lineManagerAccountId,lineManagerDisplayName,lineManagerEmail,squadGroupName):
        self.username = username
        self.email = email
        self.displayName = displayName
        self.lineManagerAccountId = lineManagerAccountId
        self.lineManagerDisplayName = lineManagerDisplayName
        self.lineManagerEmail = lineManagerEmail
        self.squadGroupName = squadGroupName
        self.registered_on = datetime.utcnow()

    @staticmethod
    def try_login(username, password):
        global gSSOPWD
        try:
            conn = get_ldap_connection()
        except:
            flash('LDAP Connection Failed!!!')
            return redirect(url_for('login'))
        filter = '(uid=%s)'%username
        attrs = ['mail','displayName', 'nsnManagerAccountName']
        base_dn = 'o=NSN'
        try:
            result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
        except:
            flash('LDAP Searching Failed!!!')
            return redirect(url_for('login'))
        dn = result[0][0]
        try:
            a = conn.simple_bind_s(dn,password)
            gSSOPWD = password # For privacy policy, cannot save and use this for other purpose.
        except ldap.INVALID_CREDENTIALS:
            print "Your  password is incorrect!!!"
            flash('Password is incorrect!!')
            return redirect(url_for('login'))
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print e.message['desc']
            else:
                print e
            flash('LDAP Bind Failed!!!')
            return redirect(url_for('login'))
        except:
            flash('Other reason login Failed!!!')
            return redirect(url_for('login'))
        return result,conn
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return unicode(self.id)
    def __repr__(self):
        return '<FusionUser %r>' % (self.username)

class Todo(db.Model):
    __tablename__ = 'taskstable'
    TaskId = db.Column('TaskId', db.String(32), primary_key=True)
    Title = db.Column(db.String(512))
    ContentAndScope = db.Column(db.String(1024))
    ImpactRelease = db.Column(db.String(64))
    Comments = db.Column(db.String(1024))
    CreatedOn = db.Column(db.DateTime)
    Status = db.Column(db.String(60))
    Benifit = db.Column(db.String(1024))
    Effort = db.Column(db.String(64))
    SuitableTeam=db.Column(db.String(60))
    Priority = db.Column(db.String(60))
    TargetRelease = db.Column(db.String(60))
    Author = db.Column(db.String(64))
    APO=db.Column(db.String(60))
    FileName = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    fusionuser_id = db.Column(db.Integer, db.ForeignKey('fusionusers.user_id'))


    def __init__(self, TaskId,Author,APO,Title,ContentAndScope,Comments,Benifit,ImpactRelease,TargetRelease,Priority,\
                 SuitableTeam,Effort,Status,FileName):
        self.TaskId = TaskId
        self.Title = Title
        self.ContentAndScope = ContentAndScope
        self.Comments = Comments
        self.Benifit = Benifit
        self.Effort = Effort
        self.Status = Status
        self.Priority = Priority
        self.SuitableTeam = SuitableTeam
        self.TargetRelease = TargetRelease
        self.ImpactRelease = ImpactRelease
        self.Author = Author
        self.APO = APO
        self.CreatedOn = datetime.utcnow()
        self.FileName = FileName

        
db.create_all()

app.config['dbconfig'] = {'host': '127.0.0.1',
                          'user': 'root',
                          'password': '',
                          'database': 'webapp', }

class UseDatabase:
    def __init__(self, config):
        """Add the database configuration parameters to the object.

        This class expects a single dictionary argument which needs to assign
        the appropriate values to (at least) the following keys:

            host - the IP address of the host running MySQL/MariaDB.
            user - the MySQL/MariaDB username to use.
            password - the user's password.
            database - the name of the database to use.

        For more options, refer to the mysql-connector-python documentation.
        """
        self.configuration = config

    def __enter__(self):
        """Connect to database and create a DB cursor.

        Return the database cursor to the context manager.
        """
        self.conn = mysql.connector.connect(**self.configuration)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Destroy the cursor as well as the connection (after committing).
        """
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

gSSOPWD =''
def get_ldap_connection():
    # conn = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
    try:
        conn = ldap.initialize('ldap://ed-p-gl.emea.nsn-net.net')
        conn.simple_bind_s('cn=BOOTMAN_Acc,ou=SystemUsers,ou=Accounts,o=NSN', 'Eq4ZVLXqMbKbD4th')
    except:
        return redirect(url_for('login'))

    return conn

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form['username']
    password = request.form['password']
    user = User(request.form['username'], request.form['password'], request.form['email'])
    registered_user = User.query.filter_by(username=username).first()
    if registered_user is None:
        db.session.add(user)
        db.session.commit()
        flash('User successfully registered')
        return redirect(url_for('login'))
    else:
        flash('User name has been used,please try other one')
        return redirect(url_for('register'))


loginMode = ''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    remember_me = False
    global loginMode
    if 'remember_me' in request.form:
        # remember_me = BooleanField('Keep me logged in')
        remember_me = True
    user = User.query.filter_by(username=username).first()
    # if registered_user is None:
    #     flash('Username is invalid' , 'error')
    #     return redirect(url_for('login'))
    if user is None or user.check_password(password) is False:
        try:
            result, conn = FusionUser.try_login(username, password)
        except:
            flash(
                'Network Issue.Cannot connect to LDAP server, Please check the Network and try again.',
                'danger')
            return redirect(url_for('login'))
        loginMode = 'SSO'
        email = result[0][1]['mail'][0]
        displayName = result[0][1]['displayName'][0]
        lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
        user = FusionUser.query.filter_by(username=username).first()
        if not user:
            filter = '(uid=%s)' % lineManagerAccountId
            attrs = ['mail','displayName', 'nsnManagerAccountName']
            base_dn = 'o=NSN'
            lineResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            lineManagerDisplayName = lineResult[0][1]['displayName'][0]
            lineManagerEmail = lineResult[0][1]['mail'][0]
            link = "http://tdlte-report-server.china.nsn-net.net/api/get_user_info?u_id=%s" % username
            r = requests.get(link)
            if r.ok:
                c = r.json()
                d = c['sg_name']
                squadGroupName = d
            else:
                squadGroupName = ''
            user = FusionUser(username, email, displayName, lineManagerAccountId, lineManagerDisplayName,
                            lineManagerEmail, squadGroupName)
            db.session.add(user)
            db.session.commit()
        else:
            lineManagerAccountId = result[0][1]['nsnManagerAccountName'][0]
            filter = '(uid=%s)' % lineManagerAccountId
            attrs = ['mail','displayName', 'nsnManagerAccountName']
            base_dn = 'o=NSN'
            lineResult = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
            user.lineManagerDisplayName = lineResult[0][1]['displayName'][0]
            user.lineManagerEmail = lineResult[0][1]['mail'][0]
            link = "http://tdlte-report-server.china.nsn-net.net/api/get_user_info?u_id=%s" % username
            r = requests.get(link)
            if r.ok:
                c = r.json()
                d = c['sg_name']
                user.squadGroupName = d
            else:
                user.squadGroupName = ''
            db.session.commit()
    else:
        loginMode = ''
    login_user(user, remember=remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(id):
    global loginMode
    if loginMode:
        return FusionUser.query.get(int(id))
    else:
        return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user

def getUserAndUserName():
    global loginMode
    print loginMode
    if loginMode:
        if g.user.username == 'qmxh38':
            username = 'leienqing'
        else:
            lineManagerEmail = FusionUser.query.get(g.user.id).lineManagerEmail
            if lineManagerEmail in addr_dict1.keys():
                username = addr_dict1[FusionUser.query.get(g.user.id).lineManagerEmail].strip()
            else:
                username = lineManagerEmail #FusionUser.query.get(g.user.id).email
        user = FusionUser.query.get(g.user.id).displayName
    else:
        username = g.user.username
        user = username
    return user,username

def getUserAndUserNameLineName():
    global loginMode
    print loginMode
    if loginMode:
        if g.user.username == 'qmxh38':
            username = 'leienqing'
        else:
            lineManagerEmail = FusionUser.query.get(g.user.id).lineManagerEmail
            if lineManagerEmail in addr_dict1.keys():
                username = addr_dict1[FusionUser.query.get(g.user.id).lineManagerEmail]
            else:
                username = lineManagerEmail #FusionUser.query.get(g.user.id).email
        user = FusionUser.query.get(g.user.id).displayName
    else:
        username = g.user.username
        user = username
    return user,username

def getUserAndUserNameForInChargeGroup():
    global loginMode
    print loginMode
    if loginMode:
        # if g.user.username == 'qmxh38':
        #     username = 'leienqing'
        # else:
        #     lineManagerEmail = FusionUser.query.get(g.user.id).lineManagerEmail
        #     if lineManagerEmail in addr_dict1.keys():
        #         username = addr_dict1[FusionUser.query.get(g.user.id).lineManagerEmail]
        #     else:
        username = FusionUser.query.get(g.user.id).email
        user = FusionUser.query.get(g.user.id).displayName
    else:
        username = g.user.username
        user = username
    return user,username

def importfromexcel(filename):
    workbook = xlrd.open_workbook(filename)
    internaltask_sheet=workbook.sheet_by_name(r'Internal task list')
    rows=internaltask_sheet.row_values(0)
    nrows=internaltask_sheet.nrows
    ncols=internaltask_sheet.ncols
    #modifyColumnType('Title')
    #print str(nrows)+"*********"
    for i in range(nrows-1):
        TaskId = internaltask_sheet.cell_value(i+1,7)
        Title = internaltask_sheet.cell_value(i+1,8)
        #print len(Title)
        ContentAndScope =internaltask_sheet.cell_value(i+1,11)
        ImpactRelease = internaltask_sheet.cell_value(i+1,3)
        Comments = internaltask_sheet.cell_value(i+1,12)
        #CreatedOn = internaltask_sheet.cell_value(i+1,j)
        Status = internaltask_sheet.cell_value(i+1,9)
        Benifit = internaltask_sheet.cell_value(i+1,10)
        Effort = internaltask_sheet.cell_value(i+1,13)
        SuitableTeam=internaltask_sheet.cell_value(i+1,14)
        Priority =internaltask_sheet.cell_value(i+1,1)
        TargetRelease = internaltask_sheet.cell_value(i+1,4)
        Author = internaltask_sheet.cell_value(i+1,0)
        APO=''
        registered_user = Todo.query.filter_by(TaskId=TaskId).first()
        if registered_user is None:
            todo = Todo(TaskId,Author,APO,Title,ContentAndScope,Comments,Benifit,ImpactRelease,TargetRelease,Priority,SuitableTeam,Effort,Status)
            todo.user = g.user
            db.session.add(todo)
            db.session.commit()
        else:
            print str(registered_user.TaskId) +"BREAKBREAK!!!!!!!!!!!!!!!!!!!!!!"
            val=0
            return val
            
    val=1
    return val
    todo=Todo.query.filter_by(TaskId=registered_user[0].TaskId).first()
    flash('TaskId has been used please use the recommanded one', 'error')
    todo=Todo.query.order_by(Todo.TaskId.desc()).first()
    a = re.sub("\D", "", todo.TaskId)
            #a=filter(str.isdigit, todo.TaskId)
    a=int(a)
    a=a+1
            
    b=len(str(a))
            #sr=sr+'m'*(9-len(sr))
    TaskId='MAC'+'0'*(6-b)+ str(a)
    return render_template('new.html'
                            ,TaskId=TaskId)

class Excel:  
    def export(self):

        output = BytesIO() 

        writer = pd.ExcelWriter(output, engine='xlwt')
        workbook = writer.book

        worksheet= workbook.add_sheet('sheet1',cell_overwrite_ok=True)
        col=0
        row=1
        pattern = xlwt.Pattern() # Create the Pattern
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN # May be: NO_PATTERN, SOLID_PATTERN, or 0x00 through 0x12
        pattern.pattern_fore_colour = 5 # May be: 8 through 63. 0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = Yellow, 6 = Magenta, 7 = Cyan, 16 = Maroon, 17 = Dark Green, 18 = Dark Blue, 19 = Dark Yellow , almost brown), 20 = Dark Magenta, 21 = Teal, 22 = Light Gray, 23 = Dark Gray, the list goes on...
        #style = xlwt.XFStyle() # Create the Pattern
        font = xlwt.Font() # Create the Font
        font.name = 'Times New Roman'
        font.bold = True
        #font.underline = True
        #font.italic = True
        style = xlwt.XFStyle() # Create the Style
        style.font = font # Apply the Font to the Style
        style.pattern = pattern # Add Pattern to Style
        columns=['TaskId','Title','ContentAndScope','ImpactRelease','Comments','CreatedOn','Status','Benifit','Effort','SuitableTeam','Priority','TargetRelease','Author','APO']
        for item in columns:
            worksheet.col(col).width = 4333 # 3333 = 1" (one inch).
            worksheet.write(0, col,item,style)
            col+=1
        style = xlwt.XFStyle()
        style.num_format_str = 'M/D/YY' # Other options: D-MMM-YY, D-MMM, MMM-YY, h:mm, h:mm:ss, h:mm, h:mm:ss, M/D/YY h:mm, mm:ss, [h]:mm:ss, mm:ss.0
        alignment = xlwt.Alignment() # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_JUSTIFIED # May be: HORZ_GENERAL, HORZ_LEFT, HORZ_CENTER, HORZ_RIGHT, HORZ_FILLED, HORZ_JUSTIFIED,HORZ_CENTER_ACROSS_SEL, HORZ_DISTRIBUTED
        alignment.vert = xlwt.Alignment.VERT_TOP # May be: VERT_TOP, VERT_CENTER, VERT_BOTTOM, VERT_JUSTIFIED, VERT_DISTRIBUTED
        #style = xlwt.XFStyle() # Create Style
        style.alignment = alignment # Add Alignment to Style
        todos=Todo.query.order_by(Todo.TaskId.asc()).all()
        nrows=len(todos)
        print ('nrows==%s' %(nrows))
        for row in range(nrows):
            r=row+1
            worksheet.write(r,0,todos[row].TaskId)
            worksheet.write(r,1,todos[row].Title,style)
            worksheet.write(r,2,todos[row].ContentAndScope,style)
            worksheet.write(r,3,todos[row].ImpactRelease)
            worksheet.write(r,4,todos[row].Comments,style)
            worksheet.write(r,5,todos[row].CreatedOn,style)
            worksheet.write(r,6,todos[row].Status)
            worksheet.write(r,7,todos[row].Benifit,style)
            worksheet.write(r,8,todos[row].Effort)
            worksheet.write(r,9,todos[row].SuitableTeam)
            worksheet.write(r,10,todos[row].Priority)
            worksheet.write(r,11,todos[row].TargetRelease)
            worksheet.write(r,12,todos[row].Author)
            worksheet.write(r,13,todos[row].APO)
            
            """
            for co in columns:
                column=columns.index(co)
                cellvalue=todos[row][column]
                worksheet.write(row,column,cellvalue)
            print('row===%s,index===%s'%(column,cellvalue))
            """
 
        #worksheet.set_column('A:E', 20)  

        writer.close() 
        output.seek(0) 
        return output

def compare_time(start_t,end_t):
    s_time = time.mktime(time.strptime(start_t,'%Y-%m-%d'))                        
    #get the seconds for specify date
    e_time = time.mktime(time.strptime(end_t,'%Y-%m-%d'))
    if float(s_time) >= float(e_time):
        return True
    return False 

def comparetime(start_t,end_t):
    s_time = time.mktime(time.strptime(start_t,'%Y-%m-%d'))                        
    #get the seconds for specify date
    e_time = time.mktime(time.strptime(end_t,'%Y-%m-%d'))
    if(float(e_time)- float(s_time)) > float(86400):
        print ("@@@float(e_time)- float(s_time))=%f"%(float(e_time)- float(s_time)))
        return True
    return False 

def leap_year(y):
    if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0:
        return True
    else:
        return False
        
def days_in_month(y, m): 
    if m in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif m in [4, 6, 9, 11]:
        return 30
    else:
        if leap_year(y):
            return 29
        else:
            return 28
            
def days_this_year(year): 
    if leap_year(year):
        return 366
    else:
        return 365
            
def days_passed(year, month, day):
    m = 1
    days = 0
    while m < month:
        days += days_in_month(year, m)
        m += 1
    return days + day

def dateIsBefore(year1, month1, day1, year2, month2, day2):
    """Returns True if year1-month1-day1 is before year2-month2-day2. Otherwise, returns False."""
    if year1 < year2:
        return True
    if year1 == year2:
        if month1 < month2:
            return True
        if month1 == month2:
            return day1 < day2
    return False

def daysBetweenDates(year1, month1, day1, year2, month2, day2):
    if year1 == year2:
        return days_passed(year2, month2, day2) - days_passed(year1, month1, day1)
    else:
        sum1 = 0
        y1 = year1
        while y1 < year2:
            sum1 += days_this_year(y1)
            y1 += 1
        return sum1-days_passed(year1,month1,day1)+days_passed(year2,month2,day2)

def daysBetweenDate_(start,end):
    start=str(start)
    end=str(end)
    """
    year1=int(start.split('-',2)[0])
    month1=int(start.split('-',2)[1])
    day1=int(start.split('-',2)[2])

    year2=int(end.split('-',2)[0])
    month2=int(end.split('-',2)[1])
    day2=int(end.split('-',2)[2])
    """
    year1=start.split('-',2)[0]
    year1 = re.sub("\D", "", year1)
    month1=start.split('-',2)[1]
    month1 = re.sub("\D", "", month1)
    day1=start.split('-',2)[2]
    day1 = re.sub("\D", "", day1)
    
    year1=int(year1)
    month1=int(month1)
    day1=int(day1)
    
    year2=start.split('-',2)[0]
    year2 = re.sub("\D", "", year2)
    month2=start.split('-',2)[1]
    month2 = re.sub("\D", "", month2)
    day2=start.split('-',2)[2]
    day2 = re.sub("\D", "", day2)

    year2=int(year2)
    month2=int(month2)
    day2=int(day2)
    
    """
    year2=end.split('-',2)[0]
    month2=end.split('-',2)[1]
    day2=end.split('-',2)[2]
    a = re.sub("\D", "", todo.TaskId)
    #a=filter(str.isdigit, todo.TaskId)
    a=int(a)
    """
    print ("daysBetweenDates(year1, month1, day1, year2, month2, day2)=%d"%daysBetweenDates(year1, month1, day1, year2, month2, day2))
    return daysBetweenDates(year1, month1, day1, year2, month2, day2)    

def daysBetweenDate(start,end):
    year1=int(start.split('-',2)[0])
    month1=int(start.split('-',2)[1])
    day1=int(start.split('-',2)[2])

    year2=int(end.split('-',2)[0])
    month2=int(end.split('-',2)[1])
    day2=int(end.split('-',2)[2])
    print ("daysBetweenDates(year1, month1, day1, year2, month2, day2)=%d"%daysBetweenDates(year1, month1, day1, year2, month2, day2))
    return daysBetweenDates(year1, month1, day1, year2, month2, day2)

admin=['leienqing','tmt']

@app.route('/',methods=['GET','POST'])
@login_required
def index():
    user,username = getUserAndUserName()
    if request.method=='GET':
        headermessage = 'All Task Items'
        count = Todo.query.filter(Todo.Status != 'Rejected',Todo.Status != 'Closed').count()
        #hello = User.query.get(g.user.id)
        #username=hello.username
        if username not in admin:
            return render_template('index.html',headermessage=headermessage,count = count,
                               todos=Todo.query.filter(Todo.Status!='Rejected', \
                                                       Todo.Status != 'Closed',Todo.SuitableTeam != g.user.username).order_by(Todo.TaskId.asc()).all(),user = user)
        else:
            count = Todo.query.order_by(Todo.TaskId.asc()).count()
            todos = Todo.query.order_by(Todo.TaskId.asc()).all()
            return render_template('index.html',headermessage = headermessage,count = count,
                               todos=todos,user = user)
    else:
        output=Excel().export()
        resp = make_response(output.getvalue()) 
        resp.headers["Content-Disposition"] ="attachment; filename=internaltask.xls"
        resp.headers['Content-Type'] = 'application/x-xlsx'
        return resp
    
@app.route('/index',methods=['GET','POST'])
@login_required
def index1():
    return redirect(url_for('/'))

@app.route('/taskinprogress',methods=['GET','POST'])
@login_required
def taskinprogress():
    if request.method=='GET':
        headermessage = 'All Inprogress Task Items'
        if g.user.username in admin or g.user.username in APOgroup:
            count = Todo.query.filter(Todo.Status == 'InProgress').count()
            todos = Todo.query.filter(Todo.Status == 'InProgress').all()
            headermessage='All Inprogress Task Items'
            return render_template('index.html',count= count,headermessage = headermessage,
                                   todos = todos,user=User.query.get(g.user.id).username + '  Logged in')
        else:
            count = Todo.query.filter_by(user_id = g.user.id).filter(Todo.Status == 'InProgress').count()
            todos = Todo.query.filter_by(user_id = g.user.id).filter(Todo.Status == 'InProgress').all()
            return render_template('index.html',count=count,headermessage = headermessage,
                               todos= todos,\
                               user=User.query.get(g.user.id).username + '  Logged in')

@app.route('/taskpending',methods=['GET','POST'])
@login_required
def taskpending():
    if request.method=='GET':
        headermessage = 'All Pending Task Items'
        if g.user.username in admin:
            count = Todo.query.filter_by(SuitableTeam ='yangguangxin').count()
            return render_template('index.html',count= count,headermessage = headermessage,
                                   todos=Todo.query.filter_by( SuitableTeam = 'yangguangxin').all(), \
                                   user=User.query.get(g.user.id).username + '  Logged in')
        else:
            count=Todo.query.filter_by(user_id = g.user.id).count()
            count = Todo.query.filter(Todo.SuitableTeam.in_(APOgroup), Todo.Status != 'Rejected', Todo.Status != 'Closed').count()
            return render_template('index.html',count=count,headermessage = headermessage,
                               todos=Todo.query.filter(Todo.SuitableTeam.in_(APOgroup)).all(),\
                               user=User.query.get(g.user.id).username + '  Logged in')

@app.route('/taskdone',methods=['GET','POST'])
@login_required
def taskdone():
    if request.method=='GET':
        headermessage = 'All Done Task Items'
        if g.user.username in admin or g.user.username in APOgroup:
            count = Todo.query.filter(Todo.Status == 'Done').count()
            todos = Todo.query.filter(Todo.Status == 'Done').all()

            return render_template('index.html',count= count,headermessage = headermessage,
                                   todos=todos,\
                                   user=User.query.get(g.user.id).username + '  Logged in')
        else:
            count = Todo.query.filter_by(user_id = g.user.id,Status ='Done').count()
            todos = Todo.query.filter_by(user_id = g.user.id,Status ='Done').all()
            return render_template('index.html',count=count,headermessage = headermessage,
                               todos= todos,\
                               user=User.query.get(g.user.id).username + '  Logged in')

@app.route('/fromexcel',methods=['GET', 'POST'])
@login_required
def fromexcel():
    if request.method == 'GET':
        return render_template('fromexcel.html')
    else:
        print request.form['textfield']
        filename=request.form['textfield']
        val=importfromexcel(filename)
        if val==0:
            flash('TaskId has been used! please use the recommanded one', 'error')
            todo=Todo.query.order_by(Todo.TaskId.desc()).first()
            a = re.sub("\D", "", todo.TaskId)
                    #a=filter(str.isdigit, todo.TaskId)
            a=int(a)
            a=a+1
                    
            b=len(str(a))
                    #sr=sr+'m'*(9-len(sr))
            TaskId='MAC'+'0'*(6-b)+ str(a)
            return render_template('new.html'
                                    ,TaskId=TaskId)           
        flash('Todo item was successfully imported')
        return redirect(url_for('index'))
    #return render_template('new.html',newTaskId)

@app.route('/toexcel',methods=['GET', 'POST'])
@login_required
def toexcel():
    if request.method == 'GET':
        return render_template('toexcel.html')
    else:
        #print request.form['textfield']
        #filename=request.form['textfield']
        #exporttoexcel(filename)
        output=Excel().export()
        resp = make_response(output.getvalue()) 
        resp.headers["Content-Disposition"] ="attachment; filename=internaltask.xls"
        resp.headers['Content-Type'] = 'application/x-xlsx'
        flash('Export to excel successfully,Getting the result at bottom left!')
        return resp
        #return send_file(output,attachment_filename="testing.xls",as_attachment=True)
        flash('Export was successfully completed!')
        #return redirect(url_for('index'))
    #return render_template('new.html')


@app.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'GET':
        todo = Todo.query.order_by(Todo.TaskId.desc()).first()
        if todo:
            a = re.sub("\D", "", todo.TaskId)
            # a=filter(str.isdigit, todo.TaskId)
            a = int(a)
            a = a + 1
            b = len(str(a))
        else:
            a = 1
            b = 1
        # sr=sr+'m'*(9-len(sr))
        TaskId = 'MAC' + '0' * (6 - b) + str(a)
        Effort = 'Here input Efforts (hours) for completing this task, like: xxxH'
        return render_template('new.html', TaskId=TaskId, Effort=Effort)
    elif request.method == 'POST':
        todo=Todo.query.order_by(Todo.TaskId.desc()).first()
        if todo:
            a = re.sub("\D", "", todo.TaskId)
            # a=filter(str.isdigit, todo.TaskId)
            a = int(a)
            a = a + 1
            b = len(str(a))
        else:
            a = 1
            b = 1
        # sr=sr+'m'*(9-len(sr))
        TaskId = 'MAC' + '0' * (6 - b) + str(a)
        Effort='Here input Efforts (Hours) for completing this task, like: xxxH'
        Title = request.form['Title']
        ContentAndScope  = request.form['ContentAndScope']
        Comments = request.form['Comments']
        Benifit  = request.form['Benifit']
        Effort = request.form['Effort']
        Priority  = request.form['Priority']
        SuitableTeam = request.form['SuitableTeam']
        TargetRelease  = request.form['TargetRelease']
        ImpactRelease  = request.form['ImpactRelease']
        Author = request.form['Author']
        APO  = request.form['APO']
        Status  = request.form['Status']
        
        if str(request.form['TaskId']).strip() == '':
            flash('TaskId is required as suggested', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Title']).strip()=='':
            flash('Title is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['ContentAndScope']).strip()=='':
            flash('ToDoWhat is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Comments']).strip()=='':
            flash('Solution is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Benifit'].strip())=='':
            flash('Justification for Priority  is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if len(request.form['Effort'].strip())>10:
            flash('Effort: (xxxH)  is required', 'error')
            render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Priority'].strip())=='':
            flash('Priority  is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['TargetRelease'].strip())=='':
            flash('TargetRelease is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Author'].strip())=='':
            flash('Author is required', 'error')
            return render_template('new.html',TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        if str(request.form['Status'].strip())=='':
            flash('Status is required', 'error')
            return render_template('new.html', TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,\
			                Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
							SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,\
							Author=Author,APO=APO,Status=Status,)
        else:
            TaskId=request.form['TaskId'].strip()
            #registered_user = User.query.filter_by(username=username).first()
            #if registered_user is None:
            #todos=Todo.query.filter_by(user_id = g.user.id).order_by(Todo.TaskId.asc()).all()
            todo=Todo.query.filter_by(TaskId=TaskId).first()
            if todo:
                flash('TaskId has been used please use the recommanded one', 'error')
                todo=Todo.query.order_by(Todo.TaskId.desc()).first()
                a = re.sub("\D", "", todo.TaskId)
                #a=filter(str.isdigit, todo.TaskId)
                a=int(a)
                a=a+1
                
                b=len(str(a))
                #sr=sr+'m'*(9-len(sr))
                TaskId='MAC'+'0'*(6-b)+ str(a)
                
                return render_template('new.html'
                                       ,TaskId=TaskId,Title=Title,ContentAndScope=ContentAndScope,Comments=Comments,Benifit=Benifit,Effort=Effort,Priority=Priority,\
                                       SuitableTeam=SuitableTeam,TargetRelease=TargetRelease,ImpactRelease=ImpactRelease,Author=Author,APO=APO,Status=Status)
            
            Title = request.form['Title']
            ContentAndScope  = request.form['ContentAndScope']
            Comments = request.form['Comments']
            Benifit  = request.form['Benifit']
            Effort = request.form['Effort']
            Priority  = request.form['Priority']
            SuitableTeam = request.form['SuitableTeam']
            TargetRelease  = request.form['TargetRelease']
            ImpactRelease  = request.form['ImpactRelease']
            Author = request.form['Author']
            APO  = request.form['APO']
            Status  = request.form['Status']
            FileName = ''
            
            #todo = Todo(request.form['title'], request.form['text'])
            todo=Todo(TaskId,Author,APO,Title,ContentAndScope,Comments,Benifit,ImpactRelease,TargetRelease,Priority,SuitableTeam,Effort,Status,FileName)
            #todo.user = g.user
            global loginMode
            if loginMode:
                todo.fusionuser = g.user
            else:
                todo.user = g.user
            db.session.add(todo)
            db.session.commit()
            flash('Internal task item was successfully created')
            return redirect(url_for('index'))


admin=['leienqing','tmt','admin']
APOgroup=['yangguangxin','shenlizhen']

teamlist=['lanshenghai','lizhongyuan','zhangyijie','guyu','yangguangxin','admin','liaozhijun',\
          'shenlizhen','fumingjie']
# FC mapping table
addr_dict = {}
addr_dict['chenlong'] = {'email': 'loong.chen@nokia-sbell.com', 'fc': 'chengbin.qi@nokia-sbell.com'}
addr_dict['yangjinyong'] = {'email': 'jinyong.yang@nokia-sbell.com', 'fc': 'joseph.zhou@nokia-sbell.com'}
addr_dict['zhangyijie'] = {'email': 'frank.han@nokia-sbell.com', 'fc': 'zhilong.jiang@nokia-sbell.com'}
addr_dict['lanshenghai'] = {'email': 'shenghai.lan@nokia-sbell.com', 'fc': 'linggang.tu@nokia-sbell.com'}
addr_dict['liumingjing'] = {'email': 'mingjing.liu@nokia-sbell.com', 'fc': 'zhihua.xu@nokia-sbell.com'}
addr_dict['lizhongyuan'] = {'email': 'zhongyuan.y.li@nokia-sbell.com', 'fc': 'yu.tan@nokia-sbell.com'}
# addr_dict['leienqing']={'email':'enqing.lei@nokia-sbell.com','fc':'chengbin.qi@nokia-sbell.com'}
addr_dict['caizhichao'] = {'email': 'zhi_chao.cai@nokia-sbell.com', 'fc': 'zhi_chao.cai@nokia-sbell.com'}
addr_dict['hujun'] = {'email': 'jun-julian.hu@nokia-sbell.com', 'fc': 'jun-julian.hu@nokia-sbell.com'}
addr_dict['xiezhen'] = {'email': 'jason.xie@nokia-sbell.com', 'fc': 'fei-kevin.liu@nokia-sbell.com'}
addr_dict['wangli'] = {'email': 'li-daniel.wang@nokia-sbell.com',
                       'fc': 'yuan_xing.wu@nokia-sbell.com,jun-julian.hu@nokia-sbell.com'}

addr_dict1 = {}
addr_dict1['loong.chen@nokia-sbell.com'] = 'chenlong'
addr_dict1['jinyong.yang@nokia-sbell.com'] = 'yangjinyong'
addr_dict1['yijie.zhang@nokia-sbell.com'] = 'zhangyijie'
addr_dict1['shenghai.lan@nokia-sbell.com'] = 'lanshenghai'
addr_dict1['mingjing.liu@nokia-sbell.com'] = 'liumingjing'
addr_dict1['zhongyuan.y.li@nokia-sbell.com'] = 'lizhongyuan'
addr_dict1['zhi_chao.cai@nokia-sbell.com'] = 'caizhichao'
addr_dict1['jason.xie@nokia-sbell.com'] = 'xiezhen'
addr_dict1['li-daniel.wang@nokia-sbell.com'] = 'wangli'
addr_dict1['sean.x.yang@nokia-sbell.com'] = 'yangguangxin'
addr_dict1['legend.shen@nokia-sbell.com'] = 'shenlizhen'

gTaskId  = 'MAC000001'
# GuYu's AccountName: z000dekc

@app.route('/internaltask2fusion',methods=['GET', 'POST'], strict_slashes=False)
@login_required
def internaltask2fusion():
    global gTaskId
    global gTaskId
    if request.method == 'GET':
        print "Impossible!"
        return render_template('FusionLogin4InternalTaskUpdate.html')
        return redirect(url_for('internaltask2fusion'))
    else:
        username = request.form['username']
        password = request.form['password']
        options = {'server': 'https://jiradc.int.net.nokia.com/'}
        #jira = JIRA(options, basic_auth=(aa, bb))
        try:
            jira = JIRA(options, basic_auth=(username, password))
        except:
            flash('Invalid login,Please login with your own JIRA account and password!!!')
            return render_template('FusionLogin4InternalTaskUpdate.html')
        project = jira.project('FFB')
        prjId=project.id
        #Fusion Feature Backlog key is FFB
        # FFB id=u'42894' key =u'FFB'
        todo_item = Todo.query.get(gTaskId)
        JiraIssueId = todo_item.ApJiraId
        #issue = jira.issue('MNRCA-15563')
        issue = jira.issue(JiraIssueId)
        rcaapevidence = gEvidenceFileName
        dict1 = {'customfield_38032': rcaapevidence}
        dict2 =  {'customfield_38032': rcaapevidence}
        issue.update(dict1)
        jira.transition_issue(issue,JIRA_STATUS['Resolved'])
        #todo_item = TodoAP.query.get(gAPID)
        todo_item.APCompletedOn = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        todo_item.IsApCompleted = 'Yes'
        db.session.commit()
        flash('AP Status has been successfully updated!!!')
        return redirect(url_for('show_or_updateap', APID=gAPID))
        #return redirect(url_for('apindex'))
def getTaskId():
    todo = Todo.query.order_by(Todo.TaskId.desc()).first()
    if todo:
        a = re.sub("\D", "", todo.TaskId)
        # a=filter(str.isdigit, todo.TaskId)
        a = int(a)
        a = a + 1
        b = len(str(a))
    else:
        a = 1
        b = 1
    # sr=sr+'m'*(9-len(sr))
    TaskId = 'MAC' + '0' * (6 - b) + str(a)
    return TaskId

@app.route('/todos/<TaskId>', methods = ['GET' , 'POST'])
@login_required
def show_or_update(TaskId):
    global gTaskId
    #global APOgroup
    user,username = getUserAndUserName()
    gTaskId = TaskId.strip()
    # hello = User.query.get(g.user.id)
    # username=hello.username
    todo_item = Todo.query.get(TaskId)
    
    if request.method == 'GET':
        #value = request.form['button']
        if todo_item.SuitableTeam == username or username in admin:
            print ("todo_item.user_id=%d"%todo_item.user_id)
            print ("g.user.id=%d"%g.user.id)
            print "before"
            if username in admin:
                return render_template('admin_view.html',todo=todo_item)
            elif username in APOgroup:
                return render_template('apo_view.html', todo=todo_item)
            else:
                return render_template('view.html',todo=todo_item)
        elif username in APOgroup:
            return render_template('apo_view.html',todo=todo_item)
        else: #g.user.id != todo_item.user.id:
            print "after" 
            print ("todo_item.user_id=%d"%todo_item.user_id)
            print ("g.user.id=%d"%g.user.id)
            flash('You are not authorized to edit this todo item','error')
            #return redirect(url_for('show_or_update',TaskId=TaskId))
            #return redirect(url_for('logout'))
            return render_template('view.html', todo=todo_item)

    elif request.method == 'POST':
        value = request.form['button']
        if value == 'Split Task':
            TaskId = getTaskId()
            Title = request.form['Title'] +'Child task of Task:'+ request.form['TaskId']
            ContentAndScope = request.form['ContentAndScope']
            Comments = request.form['Comments']
            Benifit = request.form['Benifit']
            Effort = request.form['Effort']
            print Effort
            a = re.sub("\D", "", Effort)
            a = int(a)
            Effort = a/2
            print Effort
            Priority = request.form['Priority']
            SuitableTeam = request.form['SuitableTeam']
            TargetRelease = request.form['TargetRelease']
            ImpactRelease = request.form['ImpactRelease']
            Author = request.form['Author']
            APO = request.form['APO']
            Status = request.form['Status']
            FileName = todo_item.FileName
            todo=Todo(TaskId,Author,APO,Title,ContentAndScope,Comments,Benifit,ImpactRelease,TargetRelease,Priority,SuitableTeam,Effort,Status,FileName)
            todo.user = g.user
            db.session.add(todo)
            db.session.commit()
            flash('Internal task split item was successfully created')
            todo_item.Effort = Effort
            db.session.commit()
            return redirect(url_for('index'))
        if value == 'Update':
        # if todo_item.user.id == g.user.id or username in admin or username in APOgroup:
            if username in admin:
                todo_item.TaskId=request.form['TaskId'].strip()
                todo_item.Title = request.form['Title']
                todo_item.ContentAndScope  = request.form['ContentAndScope']
                todo_item.Comments = request.form['Comments']
                todo_item.Benifit  = request.form['Benifit']
                todo_item.Effort = request.form['Effort']
                todo_item.Priority  = request.form['Priority']
                todo_item.SuitableTeam = request.form['SuitableTeam']
                team= request.form['SuitableTeam']
                if not request.form['SuitableTeam']:
                    flash('Owner(Team/APO) is required', 'error')
                todo_item.TargetRelease  = request.form['TargetRelease']
                todo_item.ImpactRelease  = request.form['ImpactRelease']
                todo_item.Author = request.form['Author']
                todo_item.APO  = request.form['APO'] # Target date
                if not request.form['APO']:
                    flash('Tagetdate is required', 'error')
                todo_item.Status  = request.form['Status']
                if not request.form['Status']:
                    flash('Task status is required', 'error')
                if team in teamlist: # team is in teamlist,update user_id, otherwise keep the original one.    
                    hello = User.query.filter_by(username=team).first()
                    todo_item.user_id=hello.id
                
            elif username in APOgroup: # APO view
                todo_item.Title = request.form['Title']
                todo_item.ContentAndScope  = request.form['ContentAndScope']
                todo_item.Comments = request.form['Comments']
                todo_item.Benifit  = request.form['Benifit']
                todo_item.Effort = request.form['Effort']
                todo_item.Priority  = request.form['Priority']
                todo_item.SuitableTeam = request.form['SuitableTeam']
                team= request.form['SuitableTeam']
                if not request.form['SuitableTeam']:
                    flash('Owner(Team/APO) is required', 'error')
                
                todo_item.TargetRelease  = request.form['TargetRelease']
                todo_item.ImpactRelease  = request.form['ImpactRelease']
                todo_item.Author = request.form['Author']
                todo_item.APO  = request.form['APO'] #APO Column used as TargetDate,Suitable team used for team assignment

                targetdate = request.form['APO']
                #current_time = datetime.utcnow()
                current_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
                days = daysBetweenDate(current_time, targetdate)
                if not request.form['APO']:
                    flash('Task Taget date is required', 'error')
                    return render_template('view.html',todo=todo_item)

                if days < 20:
                    flash('TargetDate should be one month later from now, Please select a suitalbe date', 'error')
                    #return render_template('view.html', todo=todo_item)
                    return redirect(url_for('show_or_update',TaskId=TaskId))
                todo_item.Status  = request.form['Status']
                todo_item.Status = 'InProgress'
                if not todo_item.Status:
                    flash('Task status should be set as InProgress if you want to assign it successfully', 'error')
                    return render_template('view.html',todo=todo_item)
                if todo_item.Status !='InProgress':
                    flash('Task status should be set as InProgress if you want to assign it successfully', 'error')
                    return render_template('view.html',todo=todo_item)
                #current_time=datetime.utcnow()
                #APCreatedDate=time.strftime('%Y-%m-%d',time.localtime(time.time()))
                todos=Todo.query.filter_by(SuitableTeam = team,Status='InProgress').order_by(Todo.APO.desc()).first()
                if todos:
                    #targetdate=todos.APO
                    if days > 20:
                        hello = User.query.filter_by(username=team).first()
                        todo_item.user_id=hello.id
                    else:
                        flash('Team is overloaded, try another team', 'error')
                        return render_template('view.html',todo=todo_item)
                else:
                    hello = User.query.filter_by(username=team).first()
                    todo_item.user_id=hello.id
                db.session.commit() # update DB
                #fusion update
                #return redirect(url_for('internaltask2fusion'))
                #return render_template('JIRAlogin4ApUpdate.html')
            else: # Team or other user view
                todo_item.Title = request.form['Title']
                todo_item.ContentAndScope  = request.form['ContentAndScope']
                if str(request.form['ContentAndScope']).strip()=='':
                    flash('TodoWhat is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.Comments = request.form['Comments']
                if str(request.form['Comments']).strip()=='':
                    flash('Solution is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.Benifit  = request.form['Benifit']
                if str(request.form['Benifit']).strip()=='':
                    flash('Priority Justification is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.Effort = request.form['Effort']
                if str(request.form['Effort']).strip()=='':
                    flash('Effort is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.Priority  = request.form['Priority']
                if str(request.form['Priority']).strip()=='':
                    flash('Priority is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.SuitableTeam = request.form['SuitableTeam']
                team= request.form['SuitableTeam']
                if not request.form['SuitableTeam']:
                    flash('Owner(Team/APO) is required', 'error')
                todo_item.TargetRelease  = request.form['TargetRelease']
                if str(request.form['TargetRelease']).strip()=='':
                    flash('TargetRelease is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.ImpactRelease  = request.form['ImpactRelease']
                if str(request.form['ImpactRelease']).strip() == '':
                    flash('ImpactRelease is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.Author = request.form['Author']
                if str(request.form['Author']).strip() == '':
                    flash('Author is required', 'error')
                    return render_template('view.html',todo=todo_item)
                todo_item.APO  = request.form['APO']
                if not request.form['APO']:
                    flash('Tagetdate is required', 'error')
                todo_item.Status  = request.form['Status']
                status=request.form['Status']
                if str(request.form['Status']).strip()=='':
                    flash('Task status is required', 'error')
                    return render_template('view.html',todo=todo_item)
                
                if status =='InProgress': # only in progress task, team can assign back to po,others cannot change the user_it from normal user. 
                    if team in APOgroup:
                        hello = User.query.filter_by(username=team).first()
                        todo_item.user_id=hello.id
                    else:
                        flash('You can only return the task to APO when the task is in Inprogress', 'error')
            db.session.commit()
            return redirect(url_for('index'))
        if value == 'Update' and g.user.id != todo_item.user.id:
            flash('You are not authorized to edit this todo item','error')
            return redirect(url_for('show_or_update',TaskId=TaskId))

@app.route('/dashboard')
def dashboard():
    #logout_user()
    return render_template('chart_index.html')

# @app.route('/register' , methods=['GET','POST'])
# def register():
#     if request.method == 'GET':
#         return render_template('register.html')
#     username = request.form['username']
#     password = request.form['password']
#     user = User(request.form['username'] , request.form['password'],request.form['email'])
#     registered_user = User.query.filter_by(username=username).first()
#     if registered_user is None:
#         db.session.add(user)
#         db.session.commit()
#         flash('User successfully registered')
#         return redirect(url_for('login'))
#     else:
#         flash('User name has been used,please try other one')
#         return redirect(url_for('register'))
#
#
# @app.route('/login',methods=['GET','POST'])
# def login():
#     if request.method == 'GET':
#         return render_template('login.html')
#
#     username = request.form['username']
#     password = request.form['password']
#     remember_me = False
#     if 'remember_me' in request.form:
#         #remember_me = BooleanField('Keep me logged in')
#         remember_me = True
#     registered_user = User.query.filter_by(username=username).first()
#     if registered_user is None:
#         flash('Username is invalid, please register first' , 'error')
#         return redirect(url_for('login'))
#     if not registered_user.check_password(password):
#         flash('Password is invalid','error')
#         return redirect(url_for('login'))
#     login_user(registered_user, remember = remember_me)
#     flash('Logged in successfully')
#     return redirect(request.args.get('next') or url_for('index'))
#
# @app.route('/logout')
# def logout():
#     logout_user()
#     return redirect(url_for('index'))
#
# @login_manager.user_loader
# def load_user(id):
#     return User.query.get(int(id))
#
# @app.before_request
# def before_request():
#     g.user = current_user

def modifyColumnType(fieldname):
    with UseDatabase(app.config['dbconfig']) as cursor:
        #alter table user MODIFY new1 VARCHAR(1) -->modify field type
        _SQL = "alter table taskstable MODIFY `"+fieldname+"` VARCHAR(512)"
        cursor.execute(_SQL)

def modifyColumn():
    with UseDatabase(app.config['dbconfig']) as cursor:
        #_SQL = "alter table taskstable MODIFY RcaEdaActionType VARCHAR(128)"
        _SQL = "alter table taskstable ADD column FileName VARCHAR(128)"
        cursor.execute(_SQL)

def addColumn():
    with UseDatabase(app.config['dbconfig']) as cursor:
        #alter table user MODIFY new1 VARCHAR(1) -->modify field type
        _SQL = "alter table taskstable ADD column fusionuser_id Integer"
        cursor.execute(_SQL)
if __name__ == '__main__':
    #modifyColumn()
    #addColumn()
    app.run(debug=True,host='0.0.0.0',port=5000)