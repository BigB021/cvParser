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

        pdf_filename = None
        if 'pdf_path' in data and data['pdf_path']:
            pdf_filename = os.path.basename(data['pdf_path'])
        else:
            pdf_filename = None  # Ou une valeur par défaut si tu veux


        sql_resume = """
            INSERT INTO resumes (name, email, phone, occupation, exp_years, city, status, pdf_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_resume, (
            data['name'], data['email'], data['phone'], data.get('occupation'),
            data.get('exp_years'), data.get('city'), data.get('status'), pdf_filename
        ))
        resume_id = cursor.lastrowid

        for degree in data.get('degrees', []):
            degree_type = degree  # degree is a string here
            degree_subject = None  # no subject available

            cursor.execute("""
                INSERT INTO degrees (resume_id, degree_type, degree_subject)
                VALUES (%s, %s, %s)
            """, (resume_id, degree_type, degree_subject))


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
        resumes = cursor.fetchall()

        for resume in resumes:
            resume_id = resume['id']
            resume['degrees'] = fetch_degrees(cursor, resume_id)
            resume['skills'] = fetch_skills(cursor, resume_id)

        return {
            "status": "success",
            "data": resumes,
            "message": "Resumes retrieved." if resumes else "No resumes found."
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
        resume = cursor.fetchone()

        if resume:
            resume['degrees'] = fetch_degrees(cursor, resume_id)
            resume['skills'] = fetch_skills(cursor, resume_id)
            return {"status": "success", "data": resume}
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
        resume = cursor.fetchone()

        if resume:
            resume_id = resume['id']
            resume['degrees'] = fetch_degrees(cursor, resume_id)
            resume['skills'] = fetch_skills(cursor, resume_id)
            return {"status": "success", "data": resume}
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
        resume = cursor.fetchone()

        if resume:
            resume_id = resume['id']
            resume['degrees'] = fetch_degrees(cursor, resume_id)
            resume['skills'] = fetch_skills(cursor, resume_id)
            return {"status": "success", "data": resume}
        else:
            return {"status": "not_found", "message": f"No resumes found with name like '{name}'"}
    except mysql.connector.Error as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        db.close()

def apply_filters(keyword=None, city=None, degree=None, skill=None, min_exp=None):
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT DISTINCT r.*
        FROM resumes r
        LEFT JOIN degrees d ON r.id = d.resume_id
        LEFT JOIN skills s ON r.id = s.resume_id
        WHERE 1=1
        """
        values = []

        if keyword:
            query += " AND (LOWER(r.occupation) LIKE LOWER(%s) OR LOWER(r.status) LIKE LOWER(%s))"
            values += [f"%{keyword}%", f"%{keyword}%"]

        if city:
            query += " AND r.city = %s"
            values.append(city)

        if degree:
            query += " AND (LOWER(d.degree_type) LIKE %s OR LOWER(d.degree_subject) LIKE %s)"
            values += [f"%{degree}%", f"%{degree}%"]

        if skill:
            query += " AND LOWER(s.skill_name) LIKE LOWER(%s)"
            values.append(f"%{skill}%")

        if min_exp:
            query += " AND r.exp_years >= %s"
            values.append(int(min_exp))

        cursor.execute(query, tuple(values))
        results = cursor.fetchall()

        # Embed degrees and skills for each result
        for resume in results:
            resume_id = resume['id']
            resume['degrees'] = fetch_degrees(cursor, resume_id)
            resume['skills'] = fetch_skills(cursor, resume_id)

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


def fetch_degrees(cursor, resume_id):
    cursor.execute("SELECT degree_type, degree_subject FROM degrees WHERE resume_id = %s", (resume_id,))
    return cursor.fetchall()

def fetch_skills(cursor, resume_id):
    cursor.execute("SELECT skill_name FROM skills WHERE resume_id = %s", (resume_id,))
    return [row['skill_name'] for row in cursor.fetchall()]

# todo: add update_resume method if needed
