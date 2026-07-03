import csv
from io import StringIO
from flask import Response

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from flask import Flask, render_template, request, redirect, url_for
from flask import session, flash

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from db import get_connection
from config import SECRET_KEY

import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)

model = joblib.load("student_score_model.pkl")
scaler = joblib.load("scaler.pkl")

app.secret_key = SECRET_KEY

# ===================================================
# HOME
# ===================================================

@app.route("/")
def home():
    return render_template("home.html")


# ===================================================
# SIGNUP
# ===================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:

            query = """
            INSERT INTO users
            (full_name,email,password)
            VALUES(%s,%s,%s)
            """

            cursor.execute(
                query,
                (
                    full_name,
                    email,
                    hashed_password
                )
            )

            conn.commit()

            flash("Account created successfully")
            return redirect(url_for("login"))

        except Exception as e:

            flash("Email already exists")

            return redirect(url_for("signup"))

        finally:

            cursor.close()
            conn.close()

    return render_template("signup.html")


# ===================================================
# LOGIN
# ===================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT *
        FROM users
        WHERE email=%s
        """

        cursor.execute(query, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            if check_password_hash(
                    user["password"],
                    password):

                session["user_id"] = user["id"]

                session["full_name"] = user["full_name"]

                return redirect(url_for("dashboard"))

        flash("Invalid Email or Password")

        return redirect(url_for("login"))

    return render_template("login.html")


# ===================================================
# DASHBOARD
# ===================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COUNT(*) AS total_predictions,
            MAX(predicted_score) AS highest_score,
            AVG(predicted_score) AS average_score
        FROM predictions
        WHERE user_id=%s
    """, (session["user_id"],))

    stats = cursor.fetchone()

    cursor.execute("""
        SELECT predicted_score
        FROM predictions
        WHERE user_id=%s
        ORDER BY prediction_id DESC
        LIMIT 1
    """, (session["user_id"],))

    latest = cursor.fetchone()

    cursor.execute("""
        SELECT prediction_id, predicted_score
        From predictions
        where user_id = %s
        order by prediction_id   
        """, (session["user_id"],))

    score_history = cursor.fetchall()

    cursor.execute("""
        SELECT mental_state,count(*) as total
        From predictions
        where user_id = %s
        group by mental_state   
        """, (session["user_id"],))

    mental_state_data = cursor.fetchall()

    cursor.close()
    conn.close()

    total_predictions = stats["total_predictions"] or 0

    highest_score = (
        round(float(stats["highest_score"]), 2)
        if stats["highest_score"] is not None
        else "--"
    )

    average_score = (
        round(float(stats["average_score"]), 2)
        if stats["average_score"] is not None
        else "--"
    )

    latest_score = (
        round(float(latest["predicted_score"]), 2)
        if latest
        else "--"
    )

    return render_template(
        "dashboard.html",
         name=session["full_name"],
         total_predictions=total_predictions,
         latest_score=latest_score,
         average_score=average_score,
         highest_score=highest_score,
         score_history=score_history,
         mental_state_data=mental_state_data
    )

@app.route("/predict", methods=["GET", "POST"])
def predict():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        age = int(request.form["age"])
        study_hours_per_day = float(request.form["study_hours_per_day"])
        deep_work_sessions = int(request.form["deep_work_sessions"])
        assignment_completion_rate = int(request.form["assignment_completion_rate"])
        attendance_percentage = int(request.form["attendance_percentage"])
        social_media_hours = float(request.form["social_media_hours"])
        doomscrolling_before_sleep = int(request.form["doomscrolling_before_sleep"])
        notification_distractions = int(request.form["notification_distractions"])
        ai_tool_usage_hours = float(request.form["ai_tool_usage_hours"])
        gaming_hours = float(request.form["gaming_hours"])
        stress_level = int(request.form["stress_level"])
        motivation_level = int(request.form["motivation_level"])
        focus_score = float(request.form["focus_score"])
        procrastination_index = int(request.form["procrastination_index"])
        sleep_hours = float(request.form["sleep_hours"])
        caffeine_intake = int(request.form["caffeine_intake"])
        physical_activity_hours = float(request.form["physical_activity_hours"])
        internet_quality = int(request.form["internet_quality"])
        family_support = int(request.form["family_support"])
        financial_stress = int(request.form["financial_stress"])
        productivity_after_midnight = int(request.form["productivity_after_midnight"])
        revision_efficiency = int(request.form["revision_efficiency"])
        burnout_risk = int(request.form["burnout_risk"])
        consistency_score = int(request.form["consistency_score"])

        mental_state = request.form["mental_state"]

        burnout = 0
        distracted = 0
        focused = 0

        if mental_state == "Burnout":
            burnout = 1

        elif mental_state == "Distracted":
            distracted = 1

        elif mental_state == "Focused":
            focused = 1

        data = [[
            age,
            study_hours_per_day,
            deep_work_sessions,
            assignment_completion_rate,
            attendance_percentage,
            social_media_hours,
            doomscrolling_before_sleep,
            notification_distractions,
            ai_tool_usage_hours,
            gaming_hours,
            stress_level,
            motivation_level,
            focus_score,
            procrastination_index,
            sleep_hours,
            caffeine_intake,
            physical_activity_hours,
            internet_quality,
            family_support,
            financial_stress,
            productivity_after_midnight,
            revision_efficiency,
            burnout_risk,
            consistency_score,
            burnout,
            distracted,
            focused
        ]]

        scaled_data = scaler.transform(data)

        prediction = model.predict(scaled_data)[0]

        prediction = max(0, min(100, prediction))

        prediction = round(prediction, 2)

        conn = get_connection()
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO predictions(
        user_id,
        predicted_score,
        age,
        study_hours_per_day,
        deep_work_sessions,
        assignment_completion_rate,
        attendance_percentage,
        social_media_hours,
        doomscrolling_before_sleep,
        notification_distractions,
        ai_tool_usage_hours,
        gaming_hours,
        stress_level,
        motivation_level,
        focus_score,
        procrastination_index,
        sleep_hours,
        caffeine_intake,
        physical_activity_hours,
        internet_quality,
        family_support,
        financial_stress,
        productivity_after_midnight,
        revision_efficiency,
        burnout_risk,
        consistency_score,
        mental_state
        )
        VALUES(
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s
        )
        """

        cursor.execute(insert_query, (
            session["user_id"],
            prediction,
            age,
            study_hours_per_day,
            deep_work_sessions,
            assignment_completion_rate,
            attendance_percentage,
            social_media_hours,
            doomscrolling_before_sleep,
            notification_distractions,
            ai_tool_usage_hours,
            gaming_hours,
            stress_level,
            motivation_level,
            focus_score,
            procrastination_index,
            sleep_hours,
            caffeine_intake,
            physical_activity_hours,
            internet_quality,
            family_support,
            financial_stress,
            productivity_after_midnight,
            revision_efficiency,
            burnout_risk,
            consistency_score,
            mental_state
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return render_template(
            "predict.html",
            prediction=prediction,
            form = request.form
        )

    return render_template("predict.html",prediction=None,
                           form={})

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Prediction History

    cursor.execute("""
        SELECT *
        FROM predictions
        WHERE user_id=%s
        ORDER BY prediction_date DESC
    """,(session["user_id"],))

    predictions = cursor.fetchall()

    # Latest Prediction

    cursor.execute("""
        SELECT
            predicted_score,
            study_hours_per_day,
            attendance_percentage,
            social_media_hours,
            sleep_hours,
            stress_level,
            focus_score
        FROM predictions
        WHERE user_id=%s
        ORDER BY prediction_id DESC
        LIMIT 1
    """,(session["user_id"],))

    latest = cursor.fetchone()

    feedback = []
    rating = ""
    potential = ""

    if latest:

        score = latest["predicted_score"]

        if score >= 90:
            rating = "Excellent 🌟"
        elif score >= 75:
            rating = "Good 👍"
        elif score >= 60:
            rating = "Average 🙂"
        else:
            rating = "Needs Improvement 📚"

        if latest["study_hours_per_day"] < 5:
            feedback.append("Increase your study time by about 30–60 minutes daily.")

        if latest["attendance_percentage"] < 90:
            feedback.append(f"Your attendance is {latest['attendance_percentage']}%. Try maintaining it above 90% for better academic consistency.")

        if latest["social_media_hours"] > 2:
            feedback.append(f"You're spending {latest['social_media_hours']} hours/day on social media. Reducing it below 2 hours may improve concentration.")

        if latest["sleep_hours"] < 7:
            feedback.append(f"Your average sleep is {latest['sleep_hours']} hours. Aim for 7–8 hours for better memory and learning.")

        if latest["stress_level"] >= 7:
            feedback.append(f"Your stress level is {latest['stress_level']}/10. Taking regular breaks and exercising may help improve productivity.")

        if latest["focus_score"] < 7:
            feedback.append(f"Your focus score is {latest['focus_score']}/10. Improving concentration during study sessions can positively impact your score.")

        if score >= 90:
            potential = "Maintain your current habits and aim for consistent excellence."
        elif score >= 75:
            potential = "You have the potential to score above 90 with a few habit improvements."
        elif score >= 60:
            potential = "With better consistency and discipline, you can comfortably reach 80+."
        else:
            potential = "A structured study plan can significantly improve your academic performance."


    # -----------------------------
# Study Habits Analysis
# -----------------------------

    cursor.execute("""
SELECT

AVG(study_hours_per_day) AS avg_study,

AVG(sleep_hours) AS avg_sleep,

AVG(social_media_hours) AS avg_social,

AVG(focus_score) AS avg_focus

FROM predictions

WHERE user_id=%s
""",(session["user_id"],))

    study_stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(

    "history.html",

    predictions=predictions,

    latest=latest,

    rating=rating,

    feedback=feedback,

    potential=potential,

    study_stats=study_stats

)

@app.route("/download_csv")
def download_csv():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            prediction_id,
            predicted_score,
            age,
            study_hours_per_day,
            attendance_percentage,
            stress_level,
            sleep_hours,
            mental_state
        FROM predictions
        WHERE user_id=%s
        ORDER BY prediction_id DESC
    """, (session["user_id"],))

    predictions = cursor.fetchall()

    cursor.close()
    conn.close()

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Prediction ID",
        "Predicted Score",
        "Age",
        "Study Hours",
        "Attendance %",
        "Stress Level",
        "Sleep Hours",
        "Mental State"
    ])

    for row in predictions:

        writer.writerow([
            row["prediction_id"],
            row["predicted_score"],
            row["age"],
            row["study_hours_per_day"],
            row["attendance_percentage"],
            row["stress_level"],
            row["sleep_hours"],
            row["mental_state"]
        ])

    output.seek(0)

    return Response(

        output,

        mimetype="text/csv",

        headers={

            "Content-Disposition":
            "attachment; filename=student_predictions.csv"

        }

    )

@app.route("/download_pdf")
def download_pdf():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
        count(*) AS total_predictions,
        MAX(predicted_score) AS highest_score,
        AVG(predicted_score) AS average_score
        FROM predictions
        where user_id=%s
    """, (session["user_id"],))
    stats = cursor.fetchone()

    cursor.execute("""
          Select
            prediction_id,
            predicted_score,        
            mental_state,
            study_hours_per_day,
            attendance_percentage
            from predictions
            where user_id=%s
                  order by prediction_id desc
    """, (session["user_id"],))
    predictions = cursor.fetchall()


    cursor.close()
    conn.close()

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    elements = []

    styles = getSampleStyleSheet()

    elements.append(
        Paragraph(
            "Student Performance Prediction Report",
            styles["Heading1"]
        )
    )

    elements.append(Spacer(1, 0.25 * inch))

    elements.append(
        Paragraph(
            f"<b>Student Name:</b> {session['full_name']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Total Predictions:</b> {stats['total_predictions']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Highest Score:</b> {round(float(stats['highest_score']),2) if stats['highest_score'] else '--'}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Average Score:</b> {round(float(stats['average_score']),2) if stats['average_score'] else '--'}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1,0.35*inch))

    table_data = [[

    "Prediction ID",
    "Score",
    "Mental State",
    "Study Hours",
    "Attendance"

]]

    for row in predictions:
        table_data.append([
        row["prediction_id"],
        round(float(row["predicted_score"]),2),
        row["mental_state"],
        row["study_hours_per_day"],
        row["attendance_percentage"]
    ])


    table = Table(table_data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("BACKGROUND",(0,1),(-1,-1),colors.beige),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

        ("BOTTOMPADDING",(0,0),(-1,0),10)
]))

    elements.append(table)

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return Response(

        pdf,

        mimetype="application/pdf",

        headers={

            "Content-Disposition":
            "attachment; filename=Student_Report.pdf"

        }

    )

@app.route("/download_ai_report")
def download_ai_report():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # -----------------------------
    # User Information
    # -----------------------------
    cursor.execute("""
        SELECT
            full_name,
            email,
            created_at
        FROM users
        WHERE id=%s
    """, (session["user_id"],))

    user = cursor.fetchone()

    # -----------------------------
    # Prediction Summary
    # -----------------------------
    cursor.execute("""
        SELECT
            COUNT(*) AS total_predictions,
            MAX(predicted_score) AS highest_score,
            AVG(predicted_score) AS average_score
        FROM predictions
        WHERE user_id=%s
    """, (session["user_id"],))

    stats = cursor.fetchone()

    # -----------------------------
    # Latest Prediction
    # -----------------------------
    cursor.execute("""
        SELECT
            predicted_score,
            study_hours_per_day,
            attendance_percentage,
            social_media_hours,
            sleep_hours,
            stress_level,
            focus_score,
            mental_state
        FROM predictions
        WHERE user_id=%s
        ORDER BY prediction_id DESC
        LIMIT 1
    """, (session["user_id"],))

    latest = cursor.fetchone()

    # -----------------------------
    # Study Habits Analysis
    # -----------------------------
    cursor.execute("""
        SELECT
            AVG(study_hours_per_day) AS avg_study,
            AVG(sleep_hours) AS avg_sleep,
            AVG(social_media_hours) AS avg_social,
            AVG(focus_score) AS avg_focus
        FROM predictions
        WHERE user_id=%s
    """, (session["user_id"],))

    study_stats = cursor.fetchone()

    cursor.close()
    conn.close()

    # -----------------------------
    # Create PDF
    # -----------------------------
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    # =============================
    # Title
    # =============================

    elements.append(
        Paragraph(
            "<b><font size='18'>Student Performance AI Report</font></b>",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 20))

    # =============================
    # User Information
    # =============================

    elements.append(
        Paragraph("<b>User Information</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(f"Name : {user['full_name']}", styles["BodyText"])
    )

    elements.append(
        Paragraph(f"Email : {user['email']}", styles["BodyText"])
    )

    elements.append(
        Paragraph(f"Member Since : {user['created_at']}", styles["BodyText"])
    )

    elements.append(Spacer(1, 15))

    # =============================
    # Prediction Summary
    # =============================

    elements.append(
        Paragraph("<b>Prediction Summary</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(
            f"Total Predictions : {stats['total_predictions']}",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Highest Score : {round(stats['highest_score'] or 0, 2)}",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Average Score : {round(stats['average_score'] or 0, 2)}",
            styles["BodyText"]
        )
    )

    elements.append(Spacer(1, 15))

    # =============================
    # Latest Prediction
    # =============================

    elements.append(
        Paragraph("<b>Latest Prediction</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(
            f"Predicted Score : {latest['predicted_score']}",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Mental State : {latest['mental_state']}",
            styles["BodyText"]
        )
    )

    elements.append(Spacer(1, 15))

    # =============================
    # Study Habits
    # =============================

    elements.append(
        Paragraph("<b>Study Habits Analysis</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(
            f"Average Study Hours : {round(study_stats['avg_study'] or 0, 1)} hrs/day",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Average Sleep : {round(study_stats['avg_sleep'] or 0, 1)} hrs/day",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Average Social Media : {round(study_stats['avg_social'] or 0, 1)} hrs/day",
            styles["BodyText"]
        )
    )

    elements.append(
        Paragraph(
            f"Average Focus Score : {round(study_stats['avg_focus'] or 0, 1)}/10",
            styles["BodyText"]
        )
    )

    elements.append(Spacer(1, 20))

    # =============================
    # AI Verdict
    # =============================

    elements.append(
        Paragraph("<b>AI Performance Verdict</b>", styles["Heading2"])
    )

    score = latest["predicted_score"]

    if score >= 90:
        verdict = (
            "Outstanding academic performance. Your study habits indicate excellent "
            "consistency. Continue maintaining your current routine to sustain high performance."
        )

    elif score >= 75:
        verdict = (
            "Good academic performance. With slightly increased study time and better "
            "consistency, you have strong potential to achieve scores above 90."
        )

    elif score >= 60:
        verdict = (
            "Average academic performance. Improving study discipline, sleep quality "
            "and reducing distractions can significantly improve future predictions."
        )

    else:
        verdict = (
            "Your current academic performance requires improvement. Developing a "
            "structured study routine and maintaining healthier study habits will greatly improve results."
        )

    elements.append(
        Paragraph(verdict, styles["BodyText"])
    )

    elements.append(Spacer(1, 20))

    # =============================
    # Personalized Recommendations
    # =============================

    elements.append(
        Paragraph("<b>Personalized Recommendations</b>", styles["Heading2"])
    )

    tips = []

    if latest["study_hours_per_day"] < 5:
        tips.append("• Increase daily study hours to around 5–6 hours.")

    if latest["attendance_percentage"] < 90:
        tips.append("• Maintain attendance above 90%.")

    if latest["social_media_hours"] > 2:
        tips.append("• Reduce social media usage below 2 hours/day.")

    if latest["sleep_hours"] < 7:
        tips.append("• Sleep at least 7–8 hours every night.")

    if latest["stress_level"] >= 7:
        tips.append("• Reduce stress through regular breaks and physical activity.")

    if latest["focus_score"] < 7:
        tips.append("• Improve focus by minimizing distractions during study.")

    if not tips:
        tips.append("• Excellent! Keep maintaining your current study habits.")

    for tip in tips:
        elements.append(
            Paragraph(tip, styles["BodyText"])
        )

    elements.append(Spacer(1, 20))

    # =============================
    # Generate PDF
    # =============================

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Student_AI_Report.pdf",
        mimetype="application/pdf"
    )

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))
    
    success = request.args.get("success")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT
        full_name,
        email,
        created_at
    FROM users
    WHERE id=%s
""",(session["user_id"],))

    user = cursor.fetchone()

    cursor.execute("""
    SELECT
        COUNT(*) AS total_predictions,
        MAX(predicted_score) AS highest_score,
        AVG(predicted_score) AS average_score
    FROM predictions
    WHERE user_id=%s
""",(session["user_id"],))

    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(

    "profile.html",

    user=user,

    stats=stats,

    success=success

)

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            full_name,
            email
        FROM users
        WHERE id=%s
    """, (session["user_id"],))

    user = cursor.fetchone()

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]

        cursor.execute("""
            UPDATE users
            SET
                full_name=%s,
                email=%s
            WHERE id=%s
        """, (
            full_name,
            email,
            session["user_id"]
        ))

        conn.commit()

        session["full_name"] = full_name

        cursor.close()
        conn.close()

        return redirect(url_for("profile", success="profile"))

    cursor.close()
    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route("/change_password", methods=["GET","POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn=get_connection()
    cursor=conn.cursor(dictionary=True)

    if request.method=="POST":

        current_password=request.form["current_password"]
        new_password=request.form["new_password"]
        confirm_password=request.form["confirm_password"]

        cursor.execute("""
            SELECT password
            FROM users
            WHERE id=%s
        """,(session["user_id"],))

        user=cursor.fetchone()

        if not check_password_hash(
            user["password"],
            current_password
        ):

            cursor.close()
            conn.close()

            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        if new_password!=confirm_password:

            cursor.close()
            conn.close()

            return render_template(
                "change_password.html",
                error="Passwords do not match."
            )

        hashed_password=generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password=%s
            WHERE id=%s
        """,(
            hashed_password,
            session["user_id"]
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("profile", success="password"))

    cursor.close()
    conn.close()

    return render_template("change_password.html")
# ===================================================
# LOGOUT
# ===================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ===================================================
# RUN
# ===================================================

if __name__ == "__main__":
    app.run(debug=True)