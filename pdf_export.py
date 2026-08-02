from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import sqlite3


def export_chat_to_pdf(username):

    connection = sqlite3.connect("support.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_message, ai_response, created_at
        FROM chats
        WHERE username=?
        ORDER BY id ASC
    """, (username,))

    chats = cursor.fetchall()

    connection.close()

    filename = f"{username}_chat_history.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI Customer Support Chat History</b>", styles["Title"]))

    for chat in chats:

        story.append(Paragraph(f"<b>Time:</b> {chat[2]}", styles["Normal"]))
        story.append(Paragraph(f"<b>You:</b> {chat[0]}", styles["Normal"]))
        story.append(Paragraph(f"<b>AI:</b> {chat[1]}", styles["Normal"]))
        story.append(Paragraph("<br/>", styles["Normal"]))

    doc.build(story)

    return filename