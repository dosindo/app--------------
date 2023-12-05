from flask import Flask, render_template, request, redirect, flash,session,url_for,g #render_template으로 html파일 렌더링
import os
from functools import wraps
import cx_Oracle
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus
import pandas as pd
from datetime import datetime, timedelta
from random import randint
import json
app = Flask(__name__) 
movlist = []
userid_login = ""
username_login=""
connection = cx_Oracle.connect('c##min','1234','localhost/orcl')
app.config["SECRET_KEY"] = "ABCD"
@app.route('/')
#GET = 페이지가 나오도록 요청. POST = 버튼을 눌렀을때 데이터를 가지고오는 요청/ 요청정보확인하려면 request 임포트 필요
@app.route('/mainscreen', methods=['GET','POST'])
def mainscreen():
    if request.method == 'GET':
        yesterday = datetime.today() - timedelta(1) 
        url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
        service_key='0859801475c4cb4e85c3886ab17ddb1d'
        queryParams = '?' + urlencode({quote_plus('key') : service_key,
                                    quote_plus('targetDt') : yesterday.strftime("%Y%m%d")
        })
        response = urlopen(url + queryParams)
        json_api = response.read().decode("utf-8")

        json_file = json.loads(json_api)
        
        movlist.clear()
        for i in json_file['boxOfficeResult']['dailyBoxOfficeList']:
            d1 = ""
            d2=""
            if i['rankOldAndNew']=='NEW':
                d1="NEW!"
            if i['rankInten']!='0':
                if i['rankInten'][0]=='-':
                    d2 = '▼'+i['rankInten']
                else:
                    d2 = '▲'+i['rankInten']
            movlist.append([("순위",i['rank']),("영화이름",i['movieNm']),("누적 매출액",i['salesAcc']+"원"),("누적 관객수",i['audiAcc']+"명"),(d2,d1)])
        return render_template("main.html", data=movlist)
    elif request.method == 'POST':
        
        userid = request.form.get('userid')
        password = request.form.get('password')

        cursor = connection.cursor()
        cursor.execute("""
        select password, username from userinfo
        where userid = :1
        """, (userid,))
        result = cursor.fetchone()
        
        if result:
            if result[0] == password:
                session['userid'] = userid
                session['username'] = result[1]
                return redirect('/main_logined')
            else:
                
                return redirect('/mainscreen')
        else:
            flash("존재하지 않는 아이디입니다.")
            return redirect('/mainscreen')

        return redirect('/mainscreen')
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    elif request.method == 'POST':
        #회원정보 생성
        userid = request.form.get('userid') 
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        print(userid,username,password) # 들어오나 확인해볼 수 있다. 
        cursor = connection.cursor()
        cursor.execute("""
        select username from userinfo
        where userid = :1
        """, (userid,))

        result = cursor.fetchone()

        if not (userid and username and password and re_password and email) :
            flash("모두 입력해주세요")
            return render_template("register.html")
        elif password != re_password:
            flash("비밀번호를 확인해주세요")
            return render_template("register.html")
        elif result:
            flash("중복되는 아이디입니다.")
            return render_template("register.html")
        else: #모두 입력이 정상적으로 되었다면 밑에명령실행(DB에 입력됨)
            
            cursor = connection.cursor()
            
            cursor.execute("""
            insert into userinfo(userid,password,username,email)
            values (:1,:2,:3,:4)
                        """,[userid,password,username,email]
            )
            connection.commit()
            session['userid'] = userid
            session['username'] = username

        return redirect('/main_logined')

    return redirect('/')
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("아이디와 비밀번호를 확인해주세요")
            return redirect('/mainscreen') # or wherever you want to redirect to
        return f(*args, **kwargs)
    return decorated_function
@app.route('/main_logined', methods=['GET','POST'])
@login_required
def main_logined():
    print('mid')
    global userid_login
    global username_login 
    result = None
    if 'userid' in session:
        userid_login = session['userid']
        username_login = session['username']

    if request.method == 'GET':
        print('end')
        yesterday = datetime.today() - timedelta(1)
        url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
        service_key='0859801475c4cb4e85c3886ab17ddb1d'
        queryParams = '?' + urlencode({quote_plus('key') : service_key,
                                    quote_plus('targetDt') : yesterday.strftime("%Y%m%d")
        })
        response = urlopen(url + queryParams)
        json_api = response.read().decode("utf-8")


        json_file = json.loads(json_api)
        
        movlist.clear()
        for i in json_file['boxOfficeResult']['dailyBoxOfficeList']:
            d1 = ""
            d2=""
            if i['rankOldAndNew']=='NEW':
                d1="NEW!"
            if i['rankInten']!='0':
                if i['rankInten'][0]=='-':
                    d2 = '▼'+i['rankInten']
                else:
                    d2 = '▲'+i['rankInten']
            movlist.append([("순위",i['rank']),("영화이름",i['movieNm']),("누적 매출액",i['salesAcc']+"원"),("누적 관객수",i['audiAcc']+"명"),(d2,d1)])
        cursor = connection.cursor()
        cursor.execute("""
        select resdate from reservation
        """)
        result = cursor.fetchall()
        print(result)
        session['reservated'] = [res[0].strftime('%Y-%m-%d') for res in result]
        userid = session['userid']
        cursor = connection.cursor()
        print(userid)
        # 해당 사용자의 예약된 영화표 정보를 가져옵니다.
        cursor.execute("""
        select room, wantmovie, resdate,num from reservation
        where userid = :1
        order by resdate
        """, (userid,))
        tickets = cursor.fetchall()
        print(tickets)
        return render_template("main_logined.html",data = movlist,idname=username_login,reservated=session['reservated'],tickets=tickets)
    elif request.method == 'POST':
        room = request.form.get('room')
        wantmovie = request.form.get('wantmovie')
        resdate = request.form.get('resdate')
        num = randint(1,1000000)
        cursor = connection.cursor()
        cursor.execute("""
        select num from reservation
        where num=:1
        """, (num,))
        result = cursor.fetchone()
        while result:
            num = randint(1,1000000)
            cursor.execute("""
            select num from reservation
            where num=:1
            """, (num,))
            result = cursor.fetchone()
        r = str(resdate).split('/')
        r = r[2]+"-"+r[0]+"-"+r[1]
        cursor = connection.cursor()
        cursor.execute("""
INSERT INTO reservation (userid, room, wantmovie, resdate,num)
VALUES (:1, :2, :3, :4,:5)
""", (session['userid'], room, wantmovie, r,num))
        connection.commit()
        
        flash("예약되었습니다!")
        return redirect('/main_logined')
    return redirect('/')
@app.route('/delete_ticket', methods=['POST'])
def delete_ticket():
    num = request.form.get('num')
    cursor = connection.cursor()
    cursor.execute("""
    delete from reservation
    where num = :1
    """, (num,))
    connection.commit()
    flash("예약이 취소되었습니다!")
    return redirect('/main_logined')
if __name__ == "__main__":
    os.putenv('NLS_LANG', '.UTF8')
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True     # 사용자에게 원하는 정보를 전달완료했을때가 TEARDOWN, 그 순간마다 COMMIT을 하도록 한다.라는 설정
    #여러가지 쌓아져있던 동작들을 Commit을 해주어야 데이터베이스에 반영됨. 이러한 단위들은 트렌젝션이라고함.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #app.run(host='127.0.0.1', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True) 
########################