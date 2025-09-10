# streamlit_app.py — Troubleshooting EPP (CSV+Excel+correo)
import os, ssl, smtplib, pandas as pd, datetime as dt
from email.message import EmailMessage
import streamlit as st

CSV_PATH = "troubleshooting_log.csv"
XLSX_PATH = "troubleshooting_log.xlsx"

DESCRIPTION_CHOICES = [
    "1 - Underfilling / falta de llenado",
    "2 - Demoulding / mal formado",
    "3 - Adhesion",
    "4 - Dimension",
    "5 - Warping / pandeo",
]
BEAD_CHOICES = ["15", "22", "35", "42"]
MACHINE_CHOICES = [str(i) for i in range(1, 11)]   # 1..10
CURING_CHOICES  = [str(i) for i in range(1, 13)]   # 1..12
COLOR_CHOICES = {
    "Fix it (VERDE)":   "#00B050",
    "Only a Patch (NARANJA)": "#FFC000",
    "Look it (AMARILLO)": "#FFFF00",
}
COLUMNS = [
    "date","model","description","internal_issue","how_to_fix",
    "machine","bead","curing_room","comment",
    "color_label","color_hex","created_at"
]

def ensure_files():
    if not os.path.exists(CSV_PATH):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)

def append_and_save(row: dict) -> str:
    ensure_files()
    df = pd.read_csv(CSV_PATH)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False)
    try:
        df.to_excel(XLSX_PATH, index=False)
    except Exception as e:
        return f"⚠️ CSV guardado. Error creando Excel: {e}"
    return "✅ Registro guardado (CSV + Excel)."

def send_email(sender_email, app_password, recipient_email, subject, body) -> str:
    ensure_files()
    if not os.path.exists(XLSX_PATH):
        try:
            pd.read_csv(CSV_PATH).to_excel(XLSX_PATH, index=False)
        except Exception as e:
            return f"❌ No pude preparar el Excel: {e}"
    try:
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject or "Troubleshooting EPP – Reporte"
        msg.set_content(body or "Adjunto el archivo troubleshooting_log.xlsx")
        with open(XLSX_PATH, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(XLSX_PATH),
            )
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return "📧 ¡Correo enviado exitosamente!"
    except Exception as e:
        return f"❌ Error al enviar correo: {e}"

# ---------- UI ----------
st.set_page_config(page_title="Captura de Troubleshooting – EPP", page_icon="🛠️", layout="wide")
st.title("🛠️ Captura de Troubleshooting – EPP")
st.caption(f"Guarda en **{CSV_PATH}** y **{XLSX_PATH}**. Para correo usa contraseña de aplicación de Gmail.")

with st.form("frm"):
    c1, c2 = st.columns(2)
    with c1:
        date = st.text_input("Date (YYYY-MM-DD)", value="")
        model = st.text_input("Model", value="")
        description = st.selectbox("Description (Scrap Reason)", DESCRIPTION_CHOICES, index=0)
        internal_issue = st.text_input("Internal Issue", value="")
        how_to_fix = st.text_input("How to Fix?", value="")
    with c2:
        machine = st.selectbox("Machine", MACHINE_CHOICES, index=0)
        bead = st.selectbox("Bead", BEAD_CHOICES, index=0)
        curing_room = st.selectbox("Curing Room", CURING_CHOICES, index=0)
        comment = st.text_input("Comment", value="")
        color_label = st.selectbox("Color code (estatus)", list(COLOR_CHOICES.keys()), index=0)

    submitted = st.form_submit_button("💾 Guardar registro")
    if submitted:
        row = {
            "date": (date or dt.datetime.now().strftime("%Y-%m-%d")).strip(),
            "model": model.strip(),
            "description": description,
            "internal_issue": internal_issue.strip(),
            "how_to_fix": how_to_fix.strip(),
            "machine": machine,
            "bead": bead,
            "curing_room": curing_room,
            "comment": comment.strip(),
            "color_label": color_label,
            "color_hex": COLOR_CHOICES.get(color_label, ""),
            "created_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.success(append_and_save(row))

st.divider()
st.subheader("Enviar el Excel por correo (opcional)")
sender_default = st.secrets.get("email", {}).get("sender", "")
app_pass_default = st.secrets.get("email", {}).get("app_password", "")
recipient_default = st.secrets.get("email", {}).get("recipient_default", "gsdos1984@gmail.com")

c3, c4 = st.columns(2)
with c3:
    sender_email = st.text_input("Tu Gmail (remitente)", value=sender_default, placeholder="tu-cuenta@gmail.com")
    app_password = st.text_input("Contraseña de aplicación", value=app_pass_default, type="password")
with c4:
    recipient_email = st.text_input("Destinatario", value=recipient_default)
    subject = st.text_input("Asunto", value="Troubleshooting EPP – Reporte")
body = st.text_input("Mensaje", value="Adjunto el archivo troubleshooting_log.xlsx")

if st.button("✉️ Enviar Excel por correo"):
    st.info("Enviando…")
    st.write(send_email(sender_email, app_password, recipient_email, subject, body))

st.divider()
st.subheader("Descargas")
if os.path.exists(CSV_PATH):
    with open(CSV_PATH, "rb") as f:
        st.download_button("⬇️ Descargar CSV", f, file_name="troubleshooting_log.csv")
if os.path.exists(XLSX_PATH):
    with open(XLSX_PATH, "rb") as f:
        st.download_button("⬇️ Descargar Excel", f, file_name="troubleshooting_log.xlsx")
