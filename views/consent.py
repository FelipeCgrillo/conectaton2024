import streamlit as st
from streamlit_drawable_canvas import st_canvas
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, legal
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
from datetime import datetime
import os
from PIL import Image
import numpy as np

def generate_qr_code(data):
    """Genera un código QR con los datos proporcionados"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen temporalmente
    img_path = "temp_qr.png"
    qr_image.save(img_path)
    return img_path

def generate_consent_pdf(patient_data, signature_image, qr_data, qr_image=None):
    """Generates a PDF with consent form, signature and QR code"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=legal)
    width, height = legal  # Legal size: 8.5 x 14 pulgadas

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Patient Consent Form")
    
    # Patient Information
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 90, "Patient Information")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 110, f"Name: {patient_data.get('name', '')}")
    c.drawString(50, height - 130, f"Patient ID: {patient_data.get('id', '')}")
    c.drawString(50, height - 150, f"Date: {datetime.now().strftime('%B %d, %Y')}")

    # Signature and QR Code at the top with more spacing
    # Signature on the left
    if signature_image is not None:
        c.drawString(50, height - 190, "Patient Signature:")
        signature_path = "temp_signature.png"
        Image.fromarray(signature_image.astype(np.uint8)).save(signature_path)
        c.drawImage(signature_path, 50, height - 280, width=200, height=80)
        os.remove(signature_path)

    # QR Code on the right
    if qr_image:
        qr_bytes = qr_image.getvalue()
        qr_image.seek(0)
        with open("temp_qr.png", "wb") as f:
            f.write(qr_bytes)
    else:
        qr_path = generate_qr_code(qr_data)
    
    c.drawImage("temp_qr.png", width - 150, height - 280, width=80, height=80)
    c.drawString(width - 150, height - 300, "Scan for patient access")
    os.remove("temp_qr.png")

    # Consent Header with adjusted spacing
    y_position = height - 350
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "Consents Granted")
    
    # Data Access Consent
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Data Access and Storage")
    c.setFont("Helvetica", 10)
    c.drawString(70, y_position - 15, "• I consent to the secure storage and processing of my medical data")
    c.drawString(70, y_position - 30, "• Data will be encrypted and protected according to healthcare standards")
    
    # Medical Information Consent
    y_position -= 60
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Medical Information Sharing")
    c.setFont("Helvetica", 10)
    c.drawString(70, y_position - 15, "• Authorization to access and manage:")
    c.drawString(90, y_position - 30, "- Glucose level records")
    c.drawString(90, y_position - 45, "- Medical history")
    c.drawString(90, y_position - 60, "- Laboratory results")
    c.drawString(90, y_position - 75, "- Prescribed medications")
    
    # App Usage Consent
    y_position -= 95
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Application Usage")
    c.setFont("Helvetica", 10)
    c.drawString(70, y_position - 15, "• Consent to use the medical tracking application")
    c.drawString(70, y_position - 30, "• Permission to receive notifications and updates")
    
    # Healthcare Provider Access
    y_position -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Healthcare Provider Access")
    c.setFont("Helvetica", 10)
    c.drawString(70, y_position - 15, "• Authorization for healthcare providers to access my information")
    c.drawString(70, y_position - 30, "• Sharing of medical data with authorized medical professionals")

    # Patient Rights
    y_position -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Patient Rights")
    c.setFont("Helvetica", 10)
    c.drawString(70, y_position - 15, "• Right to revoke this consent at any time")
    c.drawString(70, y_position - 30, "• Right to request data deletion or modification")
    c.drawString(70, y_position - 45, "• Right to access my complete medical record")

    # Legal Notice
    y_position -= 65
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "Legal Notice")
    c.setFont("Helvetica", 10)
    c.drawString(50, y_position - 20, "By accepting this consent, I acknowledge that I have read and understood all the above terms.")
    c.drawString(50, y_position - 35, "I understand that this consent remains valid until explicitly revoked by me.")

    # Verificar que todo quepa en la página
    if y_position - 35 < 50:  # Si el contenido está muy cerca del borde inferior
        raise ValueError("Content exceeds page size")

    c.save()
    buffer.seek(0)
    return buffer

def show_consent_form():
    """Muestra el formulario de consentimiento en Streamlit"""
    st.title("Consentimiento de Uso de la Aplicación")

    # Obtener datos del paciente de la sesión
    patient_id = st.session_state.get('patient_id', None)
    if not patient_id:
        st.warning("No se ha seleccionado ningún paciente.")
        return

    # Mostrar información del paciente
    st.write(f"ID del Paciente: {patient_id}")
    
    # Campo para el nombre del paciente
    patient_name = st.text_input("Nombre del Paciente")

    # Canvas para la firma digital
    st.write("Firma Digital:")
    st.write("Por favor, firme en el espacio a continuación:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#ffffff",
        height=150,
        drawing_mode="freedraw",
        key="signature_canvas"
    )

    if st.button("Generar Consentimiento"):
        if not patient_name:
            st.error("Por favor ingrese el nombre del paciente.")
            return
            
        if canvas_result.image_data is None or not np.any(canvas_result.image_data):
            st.error("Por favor firme el documento antes de continuar.")
            return

        # Datos para el código QR
        qr_data = f"Paciente: {patient_name}\nID: {patient_id}\nFecha: {datetime.now().strftime('%d/%m/%Y')}"

        # Datos del paciente para el PDF
        patient_data = {
            'name': patient_name,
            'id': patient_id
        }

        # Generar el PDF
        pdf_buffer = generate_consent_pdf(patient_data, canvas_result.image_data, qr_data)
        
        # Botón para descargar el PDF
        st.download_button(
            label="Descargar Consentimiento PDF",
            data=pdf_buffer,
            file_name=f"consentimiento_{patient_id}.pdf",
            mime="application/pdf"
        )

        st.success("Consentimiento generado exitosamente.") 