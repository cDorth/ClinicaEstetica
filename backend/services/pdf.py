import os
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import settings

# Clinic colors
BEIGE = colors.HexColor("#F5EDE6")
NUDE = colors.HexColor("#E8D5C4")
GOLD = colors.HexColor("#C6A77D")
TEXT_COLOR = colors.HexColor("#3A3A3A")
WHITE = colors.white
LIGHT_GRAY = colors.HexColor("#F8F8F8")


def get_custom_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ClinicTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    ))
    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=TEXT_COLOR,
        spaceBefore=8 * mm,
        spaceAfter=4 * mm,
        borderColor=GOLD,
        borderWidth=0,
        borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=TEXT_COLOR,
    ))
    styles.add(ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=TEXT_COLOR,
        leftIndent=4 * mm,
    ))
    styles.add(ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    ))
    return styles


def generate_anamnese_pdf(anamnese, db) -> bytes:
    """Generate a styled PDF for a completed anamnesis."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = get_custom_styles()
    elements = []

    # Header
    elements.append(Paragraph("Clínica de Estética", styles['ClinicTitle']))
    elements.append(Paragraph("Ficha de Anamnese", styles['SectionTitle']))

    # Decorative line
    elements.append(HRFlowable(
        width="100%", thickness=2, color=GOLD,
        spaceBefore=2 * mm, spaceAfter=6 * mm,
    ))

    # Patient data section
    elements.append(Paragraph("Dados do Paciente", styles['SectionTitle']))
    paciente = anamnese.paciente
    if paciente:
        patient_data = [
            ["Nome:", paciente.nome or "—"],
            ["CPF:", paciente.cpf or "—"],
            ["Telefone:", paciente.telefone or "—"],
            ["Data de Nascimento:", str(paciente.data_nascimento) if paciente.data_nascimento else "—"],
            ["Histórico de Saúde:", paciente.historico_saude or "—"],
        ]
        table = Table(patient_data, colWidths=[5 * cm, 12 * cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4 * mm),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 0.5, NUDE),
            ('LEFTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
        ]))
        elements.append(table)

    # Procedure section
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Procedimento", styles['SectionTitle']))
    if anamnese.modelo:
        elements.append(Paragraph(
            f"<b>Tipo:</b> {anamnese.modelo.nome_procedimento}",
            styles['FieldValue'],
        ))
        if anamnese.modelo.descricao:
            elements.append(Paragraph(
                f"<b>Descrição:</b> {anamnese.modelo.descricao}",
                styles['FieldValue'],
            ))

    # Responses section
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Respostas da Anamnese", styles['SectionTitle']))

    for resp in anamnese.respostas:
        campo = resp.campo
        if campo:
            label = campo.label
            valor = resp.valor
            if isinstance(valor, list):
                valor = ", ".join(str(v) for v in valor)
            elif valor is None:
                valor = "—"
            else:
                valor = str(valor)
            elements.append(Paragraph(f"<b>{label}:</b>", styles['FieldLabel']))
            elements.append(Paragraph(valor, styles['FieldValue']))
            elements.append(Spacer(1, 2 * mm))

    # Observations
    if anamnese.observacoes:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph("Observações do Procedimento", styles['SectionTitle']))
        elements.append(Paragraph(anamnese.observacoes, styles['FieldValue']))

    # Signatures section
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph("Assinaturas", styles['SectionTitle']))

    for assinatura in anamnese.assinaturas:
        tipo_label = "Assinatura Inicial" if assinatura.tipo == "inicial" else "Assinatura Final — Confirmação"
        elements.append(Paragraph(f"<b>{tipo_label}</b>", styles['FieldLabel']))
        elements.append(Spacer(1, 2 * mm))

        sig_path = os.path.join(settings.UPLOAD_DIR, assinatura.imagem_path)
        if os.path.exists(sig_path):
            try:
                sig_img = RLImage(sig_path, width=8 * cm, height=3 * cm)
                elements.append(sig_img)
            except Exception:
                elements.append(Paragraph("[Assinatura não disponível]", styles['FieldValue']))
        elements.append(Spacer(1, 4 * mm))

    # Attachments
    if anamnese.anexos:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph("Fotos Anexadas", styles['SectionTitle']))
        for anexo in anamnese.anexos:
            tipo_label = "Bancada" if anexo.tipo == "bancada" else "Antes/Depois"
            elements.append(Paragraph(f"<b>{tipo_label}</b>", styles['FieldLabel']))
            if anexo.descricao:
                elements.append(Paragraph(anexo.descricao, styles['FieldValue']))

            anexo_path = os.path.join(settings.UPLOAD_DIR, anexo.arquivo_path)
            if os.path.exists(anexo_path):
                try:
                    img = RLImage(anexo_path, width=10 * cm, height=7 * cm)
                    elements.append(img)
                except Exception:
                    elements.append(Paragraph("[Imagem não disponível]", styles['FieldValue']))
            elements.append(Spacer(1, 4 * mm))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=NUDE,
        spaceBefore=2 * mm, spaceAfter=4 * mm,
    ))
    created = anamnese.created_at.strftime("%d/%m/%Y %H:%M") if anamnese.created_at else "—"
    finalizada = anamnese.finalizada_at.strftime("%d/%m/%Y %H:%M") if anamnese.finalizada_at else "—"
    elements.append(Paragraph(
        f"Criada em: {created} | Finalizada em: {finalizada}",
        styles['FooterStyle'],
    ))
    elements.append(Paragraph(
        "Documento gerado automaticamente — Clínica de Estética",
        styles['FooterStyle'],
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
