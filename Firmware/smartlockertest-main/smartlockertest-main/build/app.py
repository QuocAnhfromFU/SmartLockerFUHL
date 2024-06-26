import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import firebase_admin
from firebase_admin import credentials, firestore
# Khởi tạo ứng dụng Firebase
cred = credentials.Certificate("gggg-fda6e-firebase-adminsdk-zefbi-2b2a67ab05.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# Thiết lập thông tin kết nối đến cơ sở dữ liệu MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="smart_locker1"
)
cursor = db.cursor()

# Bảng roles chứa thông tin về vai trò của người dùng
# Bảng users chứa thông tin về người dùng

def generate_user_id():
    cursor = db.cursor()
    cursor.execute("SELECT MAX(user_id) FROM users")
    result = cursor.fetchone()
    cursor.close()

    if result[0] is not None:
        current_id = int(result[0][1:])
        next_id = current_id + 1
        user_id = f"U{next_id:03d}"
    else:
        user_id = "U001"

    return user_id


def generate_history_id():
    cursor = db.cursor()
    cursor.execute("SELECT MAX(history_id) FROM histories")
    result = cursor.fetchone()
    cursor.close()

    if result[0] is not None:
        current_id = int(result[0][1:])
        next_id = current_id + 1
        history_id = f"H{next_id:03d}"
    else:
        history_id = "H001"

    return history_id

def generate_otp_id():
    cursor = db.cursor()
    cursor.execute("SELECT MAX(otp_id) FROM otps")
    result = cursor.fetchone()
    cursor.close()

    if result[0] is not None:
        current_id = int(result[0][1:])
        next_id = current_id + 1
        otp_id = f"{next_id:03d}"
    else:
        otp_id = "001"

    return otp_id

def send_email(mail, locker_id, otp_code):
    # Thiết lập thông tin SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "quocanh340@gmail.com"
    smtp_password = "aivb lrnr ffie kvmh"

    # Tạo email
    msg = MIMEMultipart()
    msg['From'] = "quocanh340@gmail.com"
    msg['To'] = mail
    msg['Subject'] = "Thông tin đặt tủ"

    body = f"Tủ đã được cấp. Mã OTP là: {otp_code} Vui lòng không cung cấp mã này cho bất kì ai.Mã OTP có thời gian sử dụng là 3 tiếng."
    msg.attach(MIMEText(body, 'plain'))

    # Gửi email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())

# Hàm xóa otps sau khi qua ngày mới
def delete_otps():
    try:
        current_time = datetime.now()
        expiration_time = current_time.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        delete_query = "DELETE FROM otps WHERE expiration_time < %s"
        cursor.execute(delete_query, (expiration_time,))

        # Lưu thay đổi và đóng kết nối đến cơ sở dữ liệu
        db.commit()
        cursor.close()
        db.close()

        print("Xóa các OTP hết hạn thành công.")

    except Exception as e:
        print(f"Lỗi: {e}")

    # Gọi hàm để xóa các OTP hết hạn
    delete_otps()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
   if request.method == 'POST':
       name = request.form['name']
       email = request.form['email']
       phone = request.form['phone']
       password = request.form['password']
       confirm_password = request.form['confirm_password']
       role = request.form['role']


       # Kiểm tra xác nhận mật khẩu
       if password != confirm_password:
           return "Mật khẩu và xác nhận mật khẩu không khớp"


       cursor = db.cursor()
       cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (role,))
       role_id = cursor.fetchone()[0]


       cursor.execute("SELECT phone FROM users WHERE phone = %s", (phone,))
       existing_user = cursor.fetchone()
       if existing_user:
           return render_template('register.html')


       user_id = generate_user_id()


       # Tiến hành lưu thông tin vào bảng users
       insert_query = "INSERT INTO users (user_id, name, mail, phone, role_id, password) VALUES (%s, %s, %s, %s, %s, %s)"
       values = (user_id, name, email, phone, role_id, password)
       cursor.execute(insert_query, values)


       db.commit()
       cursor.close()

       db_firestore = firestore.client()
       user_doc_ref = db_firestore.collection("users").document(user_id)
       user_data = {
           'name': name,
           'email': email,
           'phone': phone,
           'role_id': role_id
       }
       user_doc_ref.set(user_data)

       return redirect(url_for('login'))


   return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
       phone = request.form['phone']
       password = request.form['password']


       cursor = db.cursor()
       cursor.execute("SELECT user_id, name, role_id FROM users WHERE phone = %s AND password = %s", (phone, password))
       user = cursor.fetchone()


       if user:
           session['user_id'] = user[0]
           user_name = user[1]
           role_id = user[2]


           cursor.close()


           if role_id == '1':
               return render_template('admin.html', user_name=user_name)
           elif role_id == '3':
               return render_template('delivery.html', user_name=user_name)
           elif role_id == '2':
               return render_template('process_locker.html', user_name=user_name)
           else:
               error_message = "Vai trò không hợp lệ."
               return render_template('login.html', error_message=error_message)


       else:
           error_message = "Sai số điện thoại hoặc mật khẩu. Vui lòng thử lại."
           return render_template('login.html', error_message=error_message)


   return render_template('login.html')

@app.route('/process_locker', methods=['GET','POST'])
def process_locker():

 if 'user_id' in session:
    try:
     if request.method == 'POST':
        name = request.form['name']
        mail = request.form['mail']
        phone = request.form['phone']
        start_time = request.form['start_time']


        # Kiểm tra xem số điện thoại có tồn tại trong bảng "users" hay không
        cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
        user = cursor.fetchone()
        if user:
            # Kiểm tra xem có tủ nào có status "off" không
            cursor.execute("SELECT locker_id FROM lockers WHERE status = 'off' AND locker_id BETWEEN 'locker1' AND 'locker4'")
            available_lockers = cursor.fetchall()

            if available_lockers:
                # Random một tủ
                selected_locker_id = random.choice(available_lockers)[0]

                # Cập nhật status của tủ đã chọn
                cursor.execute("UPDATE lockers SET status = 'on' WHERE locker_id = %s", (selected_locker_id,))

                # Tạo mã OTP
                otp_code = random.randint(1000, 9999)

                history_id = generate_history_id()
                # Tiến hành lưu thông tin vào bảng histories
                insert_query = "INSERT INTO histories (history_id,user_id, locker_id, start_time, end_time) VALUES (%s,%s, %s,%s,%s)"
                end_time = datetime.now() + timedelta(hours=3)  # Tính thời gian kết thúc sau 3 tiếng
                values = (history_id, user[0], selected_locker_id, start_time, end_time)
                cursor.execute(insert_query, values)
                db.commit()
                # Tạo otp_id mới
                otp_id = generate_otp_id()
                cursor.execute("SELECT end_time FROM histories WHERE locker_id = %s ORDER BY end_time DESC LIMIT 1", (selected_locker_id,))
                expiration_time_records = cursor.fetchall()

                if expiration_time_records:
                    # Trích xuất giá trị duy nhất từ danh sách expiration_time_records
                    expiration_time = expiration_time_records[0][0]

                    # Tiếp theo, bạn có thể chèn giá trị này vào bảng otps
                    cursor.execute(
                        "INSERT INTO otps (otp_id, otp_code, user_id, locker_id, expiration_time) VALUES (%s, %s, %s, %s, %s)",
                        (otp_id, otp_code, user[0], selected_locker_id, expiration_time))
                    db.commit()

                 # Tạo một tài liệu Firestore cho bảng otps
                # Tạo một tài liệu Firestore cho bảng otps
                    db_firestore = firestore.client()
                    otp_doc_ref = db_firestore.collection("otps").document(str(otp_id))
                    otp_data = {
                                'otp_code': otp_code,
                                'user_id': user[0],
                                'locker_id': selected_locker_id,
                                'expiration_time': expiration_time
                            }
                    otp_doc_ref.set(otp_data)
                # Gửi email
                send_email(mail, selected_locker_id, otp_code)

                return redirect(url_for('otp'))

            else:
                return jsonify("Khong co tu trong.")

        else:
            return jsonify("So dien thoai khong ton tai trong he thong")


    except Exception as e:
        return f"Lỗi: {e}"
    return render_template('process_locker.html')
 else:
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/otp',  methods=['GET','POST'])
def otp():
    if request.method == 'POST':
        otp_code = request.form['otp_code']

        cursor.execute("SELECT locker_id, CAST(expiration_time AS DATETIME) FROM otps WHERE otp_code = %s", (otp_code,))
        otp_data = cursor.fetchone()

        if otp_data:
            locker_id, expiration_time = otp_data

            # Kiểm tra xem thời gian hiện tại có nằm trong khoảng thời gian cho phép không
            current_time = datetime.now()
            if current_time < expiration_time:
                return f"Tủ : {locker_id} đã được mở thành công"
            else:
                return "Mã OTP đã hết hạn."
        else:
            return "Mã OTP không hợp lệ."

    return render_template('otp.html')

@app.route('/end_process', methods=['GET','POST'])
def end_process():
  try:
    if request.method == 'POST':
        otp_code = request.form['otp_code']

        cursor.execute("SELECT locker_id,user_id FROM otps WHERE otp_code = %s", (otp_code,))
        result = cursor.fetchone()

        if result:
            locker_id = result[0]
            user_id = result[1]
            # Tạo mã OTP mới và kiểm tra tính duy nhất
            otp_code_new= random.randint(1000, 9999)
            # Tạo otp_id mới
            otp_id = generate_otp_id()
            cursor.execute("SELECT end_time FROM histories WHERE locker_id = %s ORDER BY end_time DESC LIMIT 1",
                           (locker_id,))
            expiration_time_records = cursor.fetchall()
            cursor.execute("DELETE FROM otps WHERE locker_id = %s", (locker_id,))

            if expiration_time_records:
                # Trích xuất giá trị duy nhất từ danh sách expiration_time_records
                expiration_time = expiration_time_records[0][0]

                # Tiếp theo, bạn có thể chèn giá trị này vào bảng otps
                cursor.execute(
                    "INSERT INTO otps (otp_id, otp_code, user_id, locker_id, expiration_time) VALUES (%s, %s, %s, %s, %s)",
                    (otp_id, otp_code_new, result[1],locker_id, expiration_time))
                db.commit()

                cursor.execute("SELECT mail FROM users WHERE role_id = '3'")
                emails = cursor.fetchall()

                for email in emails:
                    user_email = email[0]
                    send_email(user_email, locker_id, otp_code_new)
        else:
                return jsonify("Không tìm thấy thông tin mã OTP.")
  except Exception as e:
        return f"Lỗi: {e}"
  return render_template('end_process.html')

@app.route('/complete', methods=['GET','POST'])
def complete():
    try:
        if request.method == 'POST':
            otp_code = request.form['otp_code']

            cursor.execute("SELECT locker_id FROM otps WHERE otp_code = %s", (otp_code,))
            result = cursor.fetchone()

            if result:
                locker_id = result[0]

                # Cập nhật status của tủ đã chọn
                cursor.execute("UPDATE lockers SET status = 'off' WHERE locker_id = %s", (locker_id,))
                current_time = datetime.now()
                cursor.execute("UPDATE histories SET end_time = %s WHERE locker_id = %s", (current_time, locker_id,))
                cursor.execute("DELETE FROM otps WHERE locker_id = %s", (locker_id,))
                db.commit()
                return ("Đơn hàng đã hoàn thành quá trình nhận hàng!!!")
            else:
                return ("Mã OTP không hợp lệ, vui lòng kiểm tra lại!!!")

    except Exception as e:
        return f"Lỗi: {e}"
    return render_template('complete.html')


@app.route('/history')
def history():
    # Truy vấn lịch sử dùng tủ
            select_history_query = "SELECT history_id, user_id, locker_id, start_time, end_time FROM histories"
            cursor.execute(select_history_query)
            history_data = cursor.fetchall()

            # Đóng kết nối cơ sở dữ liệu
            # cursor.close()
            # db.close()
            return render_template('history.html', history_data=history_data)

if __name__ == '__main__':
    app.run()
