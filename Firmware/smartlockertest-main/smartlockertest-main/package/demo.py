import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
# Khởi tạo ứng dụng Firebase
cred = credentials.Certificate("gggg-fda6e-firebase-adminsdk-zefbi-2b2a67ab05.json")
firebase_admin.initialize_app(cred)

mysql_connection = mysql.connector.connect(
      host="localhost",
    user="root",
    password="1234",
    database="smart_locker1"
)
mysql_cursor = mysql_connection.cursor(dictionary=True)

# Lấy dữ liệu từ MySQL
mysql_cursor.execute("SELECT * FROM users")
mysql_data = mysql_cursor.fetchall()

# # Lấy tham chiếu đến cơ sở dữ liệu Firestore
# db = firestore.client()



# # Lấy dữ liệu từ một collection
# collection_ref = db.collection("user")
# docs = collection_ref.get()

# for doc in docs:
#     print(f'{doc.id} => {doc.to_dict()}')
# Lưu dữ liệu vào Firestore
db = firestore.client()
for row in mysql_data:
    # Sử dụng ID của mỗi dòng trong MySQL làm tên tài liệu trong Firestore
    doc_ref = db.collection("user").document(row['user_id'])
    # Xóa trường ID để tránh lưu nó trong dữ liệu Firestore
    del row['user_id']
    doc_ref.set(row)

print("Data transferred successfully.")