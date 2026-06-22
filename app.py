from flask import Flask,request,redirect,url_for,render_template, flash,session,send_file,jsonify
from io import BytesIO
import flask_excel as excel
from flask_session import Session
from otp import genotp
from cmail import send_mail
from stoken import endata,dndata
from mysql.connector import (connection)
import re
mydb=connection.MySQLConnection(user='flaskuser',host='localhost',password='password',database='flaskdb')
app=Flask(__name__)
excel.init_excel(app) 
app.secret_key='code1234'
app.config
app.config['SESSION_TYPE']='filesystem'
app.config['SERVER_NAME']='54.79.12.7'
app.config['PREFERRED_URL_SCHEME']='http'
Session(app)
@app.route('/',methods=['GET'])
def home():
    return render_template('Welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        useremail=request.form['useremail']
        userpassword=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from userdata where useremail=%s',[useremail])
            email_count=cursor.fetchone()[0]
            cursor.close()
        except Exception as e:
            print(e)
            flash('Could not verify email')
        else:
            if email_count==0:
                gotp=genotp()
                userdetails={'username':username,'useremail':useremail,'userpassword':userpassword,'userotp':gotp}
                subject='user validation otp for snm'
                body=f'use the give otp {gotp}'
                send_mail(to=useremail,subject=subject,body=body)
                flash('otp has been sent to given mail')
                return redirect(url_for('otpverify',serverdata=endata(data=userdetails)))
            elif email_count==1:
                flash('Email already existed')
                return redirect(url_for('register'))
    return render_template('registerform.html')
@app.route('/otpverify/<serverdata>',methods=['GET','POST'])
def otpverify(serverdata):
    if request.method=='POST':
        try:
            user_details=dndata(data=serverdata)
        except Exception as e:
            print('Error in deserialising data',str(e))
            return redirect(url_for('register'))
        userotp=request.form['otp']
        if user_details['userotp']==userotp:
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into userdata(username,useremail,userpassword) values(%s,%s,%s)',[user_details['username'],user_details['useremail'],user_details['userpassword']])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print('MySQL error',str(e))
                flash('cannot store the details')
                return redirect(url_for('otpverify',serverdata=serverdata))
            else:
                flash('user register succesfully')
                return 'login' 
        else:
            flash('otp was wrong')
            return redirect(url_for('otpverify',serverdata=serverdata))
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form['useremail']
        login_userpassword=request.form['password']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from userdata where useremail=%s',[login_useremail])
            email_count=cursor.fetchone()
        except Exception as e:
            print('Mysql ERROR :',str(e))
            flash('could not verify email')
            return redirect(url_for('login'))
        else:
            if email_count[0]>0:
                cursor.execute('select userpassword from userdata where useremail=%s',[login_useremail])
                stored_password=cursor.fetchone()
                cursor.close()
                if stored_password[0]==login_userpassword:
                    print(session,'before  session')
                    session['user']=login_useremail
                    print(session,'after session')
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('login'))
            elif email_count[0]<=0:
                flash('no email found pls check')
                return redirect(url_for('login'))
    return render_template('login.html')
@app.route('/dashboard',methods=['GET'])
def dashboard():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    return render_template('dashboard.html')
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if not session.get('user'):
        flash('pls loginn first')
        return redirect(url_for('login'))
    if request.method=='POST':
        notes_title=request.form['title']
        notes_desc=request.form['description']
        try:
            useremail=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where useremail=%s',[useremail])
            user_id=cursor.fetchone()[0]
            cursor.execute('insert into notesdata(title,description,userid) values(%s,%s,%s)',[notes_title,notes_desc,user_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print('MYSQL Error:',str(e))
            flash('could save notes')
            return redirect(url_for('addnotes'))
        else:
            flash('notes details succesfully stored')
            return redirect(url_for('addnotes'))
    return render_template('addnotes.html')
@app.route('/viewallnotes',methods=['GET'])
def viewallnotes():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select notesid,title,created_at from notesdata where userid=%s',[user_id])
        allnotesdata=cursor.fetchall() 
        print(allnotesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallnotes.html',allnotesdata=allnotesdata)
@app.route('/viewnotes/<nid>',methods=['GET'])
def viewnotes(nid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select notesid,title,description,created_at from notesdata where userid=%s and notesid=%s',[user_id,nid])
        notesdata=cursor.fetchone() 
        print(notesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewnotes.html',notesdata=notesdata)

@app.route('/deletenotes/<nid>', methods=['GET'])
def deletenotes(nid):
    if not session.get('user'):
        flash('Please login first')
        return redirect(url_for('login'))
    try:
        useremail = session.get('user')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id = cursor.fetchone()[0]
        cursor.execute('delete from notesdata where notesid=%s and userid=%s',[nid, user_id])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print('MYSQL Error:', str(e))
        flash('Could not delete notes')
        return redirect(url_for('viewallnotes'))
    else:
        flash('Note deleted successfully')
        return redirect(url_for('viewallnotes'))
    
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select notesid,title,description,created_at from notesdata where userid=%s and notesid=%s',[user_id,nid])
        stored_notesdata=cursor.fetchone() 
        print(stored_notesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        if request.method=='POST':
            print(request.form)
            updated_title=request.form['title']
            updated_description=request.form['description']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update notesdata set title=%s,description=%s where notesid=%s and userid=%s',[updated_title,updated_description,nid,user_id])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('could update notes details')
                return redirect(url_for('updatenotes',nid=nid))
            else:
                flash('notes updated succesfylly')
                return redirect(url_for('updatenotes',nid=nid))
        return render_template('updatenotes.html',stored_notesdata=stored_notesdata)
@app.route('/Getexceldata',methods=['Get'])
def Getexceldata():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select notesid,title,description,created_at from notesdata where userid=%s ',[user_id])
        stored_allnotesdata=cursor.fetchall() 
        print(stored_allnotesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        notesdata=[list(i) for i in stored_allnotesdata]
        columns=['Notesid','Title','Description','created_at']
        notesdata.insert(0,columns)
        return excel.make_response_from_array(notesdata,'xlsx',file_name='Notesdata')
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    if request.method=='POST':
        filedata=request.files['file']
        fdata=filedata.read()
        fname=filedata.filename
        try:
            useremail=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from userdata where useremail=%s',[useremail])
            user_id=cursor.fetchone()[0] 
            cursor.execute('insert into filesdata(filename,filedata,userid) values(%s,%s,%s)',[fname,fdata,user_id])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print('MYSql Error',str(e))
            flash('could not save succesfully')
            return redirect(url_for('fileupload'))
        else:
            flash('file uploaded succesfully')
            return redirect(url_for('fileupload'))
    return render_template('uploadfile.html')

@app.route('/viewallfiles',methods=['GET'])
def viewallfiles():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select fileid,filename,created_at from filesdata where userid=%s',[user_id])
        allfilesdata=cursor.fetchall() 
        print(allfilesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the files details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallfiles.html',allfilesdata=allfilesdata)
@app.route('/deletefiles/<fid>',methods=['GET'])
def deletefiles(fid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('delete from filesdata where fileid=%s and userid=%s',[fid,user_id])
        mydb.commit()
        cursor.close()
    except Exception as e:
        print('MYSQL Error:',str(e))
        flash('could not delete file')
        return redirect(url_for('viewallfiles'))
    else:
        flash('files deleted successfully')
        return redirect(url_for('viewallfiles'))
@app.route('/viewfile/<fid>',methods=['GET'])
def viewfile(fid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=%s and fileid=%s',[user_id,fid])
        storedfile_data=cursor.fetchone()
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the files details')
        return redirect(url_for('dashboard'))
    else:
        filename=storedfile_data[1]
        bytes_array=BytesIO(storedfile_data[2])
        return send_file(bytes_array,as_attachment=False,download_name=filename)
@app.route('/downloadfile/<fid>',methods=['GET'])
def downloadfile(fid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from userdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] 
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=%s and fileid=%s',[user_id,fid])
        storedfile_data=cursor.fetchone()
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the files details')
        return redirect(url_for('dashboard'))
    else:
        filename=storedfile_data[1]
        bytes_array=BytesIO(storedfile_data[2])
        return send_file(bytes_array,as_attachment=True,download_name=filename)
@app.route('/search',methods=['GET'])
def search():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        searchdata=request.args.get('query')
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(searchdata):
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select * from notesdata where notesid like %s or title like %s or description like %s or created_at like %s',[searchdata+'%',searchdata+'%',searchdata+'%',searchdata+'%'])
                allnotesdata=cursor.fetchall()
                print(allnotesdata)
                cursor.close()
            except Exception as e:
                print('MYsql Error:',str(e))
                flash('could not search notes details')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallnotes.html',allnotesdata=allnotesdata)
        else:
            flash('invalid search data')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the files details')
        return redirect(url_for('dashboard'))   
@app.route('/logout',methods=['GET'])
def logout():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        session.pop('user')
        flash('user logged out')
        return redirect(url_for('login'))
    except Exception as e:
        print(e)
        flash('could not logout')
        return redirect(url_for('dashboard'))    

@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        forgot_email=request.form['useremail']
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from userdata where useremail=%s',[forgot_email])
            email_count=cursor.fetchone()[0]
            if email_count==1:
                subject=f'use the reset link for forgotpassword SNM Appy'
                body=f"Click the reset link {url_for('newpassword',data=endata(forgot_email),_external=True)}"
                send_mail(to=forgot_email,subject=subject,body=body)

            elif email_count==0:
                flash('email not found pls check')
                return redirect(url_for('forgotpassword')) 
        except Exception as e:
            print(e)
            flash('could not sent the link')
            return redirect(url_for('forgotpassword'))
        else:
            flash('reset-link has been sent to given email')
            return redirect(url_for('forgotpassword'))
        
    return render_template('forgotpassword.html')   

@app.route('/newpassword/<data>',methods=['GET','PUT'])
def newpassword(data):
    try:
        forgot_email=dndata(data)
    except Exception as e:
        flash('could not verify email')
        return redirect(url_for('newpassword',data=data))
    else:
        if request.method=='PUT':
            npassword=request.get_json()['password']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update userdata set userpassword=%s where useremail=%s',[npassword,forgot_email])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('could not update password in db')
                return redirect(url_for('newpassword',data=data))
            else:
                flash('password updated succesfully')
                return jsonify({'status':'success','message':'ok'})
    return render_template('newpassword.html',data=data)
if __name__=='__main__':
    app.run()
 