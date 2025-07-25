import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("user"),
        password=os.getenv("password"),
        database="cvParser"
    )

def init_database():
    """Initialize database and create tables"""
    db = None
    cursor = None

    try:
        db = get_connection()
        cursor = db.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS cvParser")
        cursor.execute("USE cvParser")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                occupation VARCHAR(100),
                exp_years TINYINT,
                city VARCHAR(100),
                status VARCHAR(255),
                pdf_path VARCHAR(255) NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS degrees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                resume_id INT NOT NULL,
                degree_type VARCHAR(100),
                degree_subject VARCHAR(200),
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                resume_id INT NOT NULL,
                skill_name VARCHAR(100) NOT NULL,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
        """)

        print("[✓] Tables created successfully.")

    except mysql.connector.Error as e:
        print(f"[!] MySQL Error: {e}")
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def add_resume(data):
    try:
        db = get_connection()
        cursor = db.cursor()

        sql_resume = """
            INSERT INTO resumes (name, email, phone, occupation, exp_years, city, status, pdf_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_resume, (
            data['name'], data['email'], data['phone'], data.get('occupation'),
            data.get('exp_years'), data.get('city'), data.get('status'), data['pdf_path']
        ))
        resume_id = cursor.lastrowid

        for degree in data.get('degrees', []):
            cursor.execute("""
                INSERT INTO degrees (resume_id, degree_type, degree_subject)
                VALUES (%s, %s, %s)
            """, (resume_id, degree['type'], degree['subject']))

        for skill in data.get('skills', []):
            cursor.execute("""
                INSERT INTO skills (resume_id, skill_name)
                VALUES (%s, %s)
            """, (resume_id, skill))

        db.commit()
        print(f"[+] Resume '{data['name']}' inserted with ID {resume_id}.")

    except mysql.connector.IntegrityError as e:
        print(f"[!] Integrity Error: {e}")
    except mysql.connector.Error as e:
        print(f"[!] MySQL Error: {e}")
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
            if db:
                db.close()

            print(f"[Debug] added to db successfully")
        except:
            pass


def delete_resume(resume_id):
    try:
        db = get_connection()
        cursor = db.cursor()

        cursor.execute("DELETE FROM resumes WHERE id = %s", (resume_id,))
        db.commit()

        if cursor.rowcount == 0:
            print(f"[!] No resume found with ID {resume_id}.")
        else:
            print(f"[-] Resume with ID {resume_id} deleted.")

    except mysql.connector.Error as e:
        print(f"[!] MySQL Error: {e}")
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
            if db:
                db.close()
        except:
            pass



def get_all_resumes():
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes")
        results = cursor.fetchall()
        return {
            "status": "success",
            "data": results,
            "message": "Resumes retrieved." if results else "No resumes found."
        }
    except mysql.connector.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

def get_resume_by_id(resume_id):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes WHERE id = %s", (resume_id,))
        result = cursor.fetchone()
        if result:
            return {"status": "success", "data": result}
        else:
            return {"status": "not_found", "message": f"No resume with ID {resume_id}"}
    except mysql.connector.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

def get_resume_by_email(email):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            return {"status": "success", "data": result}
        else:
            return {"status": "not_found", "message": f"No resume found for email {email}"}
    except mysql.connector.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

def get_resumes_by_name(name):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM resumes WHERE name LIKE %s", (f"%{name}%",))
        results = cursor.fetchall()
        if results:
            return {"status": "success", "data": results}
        else:
            return {"status": "not_found", "message": f"No resumes found with name like '{name}'"}
    except mysql.connector.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

def filter_resumes(keyword=None, city=None, degree=None, min_exp=None):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT DISTINCT r.*
        FROM resumes r
        LEFT JOIN degrees d ON r.id = d.resume_id
        WHERE 1=1
        """
        values = []

        if keyword:
            query += " AND (r.occupation LIKE %s OR r.status LIKE %s)"
            values += [f"%{keyword}%", f"%{keyword}%"]

        if city:
            query += " AND r.city = %s"
            values.append(city)

        if degree:
            query += " AND d.degree_type LIKE %s"
            values.append(f"%{degree}%")

        if min_exp:
            query += " AND r.exp_years >= %s"
            values.append(int(min_exp))

        cursor.execute(query, tuple(values))
        results = cursor.fetchall()

        return {
            "status": "success",
            "data": results,
            "message": f"{len(results)} resume(s) matched filters" if results else "No results"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

# todo: add update_resume method if needed
