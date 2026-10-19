"""Configurable academic and institutional export styles.

Export styling never mutates the saved manuscript or grants publication approval.
"""
from __future__ import annotations
from io import BytesIO
from typing import Literal, Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from xml.sax.saxutils import escape
from .erw_v121 import owner_from_auth
from .erw_v134_export import get_report, elements, NOTICE

router=APIRouter(tags=["erw-style-export"])
class StyleOptions(BaseModel):
    preset:Literal["modern-academic","classic-academic","institutional"]="modern-academic"
    fontFamily:Literal["Cambria","Times New Roman","Liberation Serif"]="Cambria"
    fontSizePt:float=Field(default=11,ge=10,le=12)
    lineSpacing:float=Field(default=1.5,ge=1.0,le=2.0)
    marginMm:float=Field(default=25,ge=20,le=35)
    headingsNumbered:bool=False

def resolved(req:StyleOptions)->StyleOptions:
    # Preset selection supplies a useful default, while explicit controls
    # retain precedence (the UI sends all controls).
    return req

def docx_export(report,project_id,owner,s:StyleOptions):
    d=Document();sec=d.sections[0]
    sec.page_height=Mm(297);sec.page_width=Mm(210)
    sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Mm(s.marginMm)
    normal=d.styles["Normal"];normal.font.name=s.fontFamily;normal.font.size=Pt(s.fontSizePt)
    normal.paragraph_format.line_spacing=s.lineSpacing
    normal.paragraph_format.space_after=Pt(5)
    for name,size in (("Title",17),("Heading 1",13)):
        st=d.styles[name];st.font.name=s.fontFamily;st.font.size=Pt(size)
        st.font.bold=True;st.paragraph_format.keep_with_next=True
        if s.preset=="institutional":st.font.color.rgb=RGBColor(108,28,44)
    if s.preset=="institutional":
        sec.header.paragraphs[0].text="SUSTAINABLE CATALYST  /  RESEARCH PUBLICATION"
        d.add_paragraph("INDEPENDENT RESEARCH REPORT")
    d.add_heading(report["title"],0)
    d.add_paragraph(", ".join(report.get("authors",[])))
    d.add_paragraph(NOTICE)
    counter=0
    for kind,value in elements(report,project_id,owner):
        if kind=="heading":
            counter+=1
            d.add_heading((str(counter)+". " if s.headingsNumbered and value!="Bibliography" else "")+value,level=1)
        elif kind=="body":
            for para in value.split("\n\n"):
                if para.strip():d.add_paragraph(para)
        elif kind=="caption":d.add_paragraph(value,style="Caption")
        elif kind=="equation":d.add_paragraph(value)
        elif kind=="table":
            t=d.add_table(rows=1,cols=len(value[0]));t.style="Table Grid"
            for i,c in enumerate(value[0]):t.rows[0].cells[i].text=str(c)
            for row in value[1:]:
                cells=t.add_row().cells
                for i,c in enumerate(row):cells[i].text=str(c)
        elif kind=="image":d.add_picture(value,width=Mm(150))
    out=BytesIO();d.save(out);return out.getvalue()

def pdf_export(report,project_id,owner,s:StyleOptions):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # PDFs do not have access to proprietary Cambria on the Linux VPS.
    # Liberation Serif is an explicit compatible substitute when available.
    import os
    paths=("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
    font="Times-Roman"
    for candidate in paths:
        if os.path.isfile(candidate):
            try:
                if "SCAcademic" not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont("SCAcademic",candidate))
                font="SCAcademic";break
            except Exception:continue
    accent=colors.HexColor("#6c1c2c") if s.preset=="institutional" else colors.black
    normal=ParagraphStyle("SCBody",fontName=font,fontSize=s.fontSizePt,
                          leading=s.fontSizePt*s.lineSpacing,spaceAfter=8)
    heading=ParagraphStyle("SCHeading",parent=normal,fontSize=13,leading=17,
                           textColor=accent,spaceBefore=18,spaceAfter=10,keepWithNext=True)
    title=ParagraphStyle("SCTitle",parent=normal,fontSize=17,leading=22,
                         textColor=accent,spaceAfter=12)
    small=ParagraphStyle("SCNote",parent=normal,fontSize=9,leading=13)
    flow=[]
    if s.preset=="institutional":
        flow.extend([Paragraph("SUSTAINABLE CATALYST / RESEARCH PUBLICATION",small),Spacer(1,14)])
    flow.extend([Paragraph(escape(report["title"]),title),
                 Paragraph(escape(", ".join(report.get("authors",[]))),normal),
                 Spacer(1,12),Paragraph(escape(NOTICE),small),Spacer(1,14)])
    counter=0
    for kind,value in elements(report,project_id,owner):
        if kind=="heading":
            counter+=1
            label=(str(counter)+". " if s.headingsNumbered and value!="Bibliography" else "")+value
            flow.append(Paragraph(escape(label),heading))
        elif kind in ("body","equation","caption"):
            use=small if kind=="caption" else normal
            for para in value.split("\n\n"):
                if para.strip():flow.append(Paragraph(escape(para).replace("\n","<br/>"),use))
        elif kind=="table":
            data=[[Paragraph(escape(str(c)),small) for c in row] for row in value]
            table=Table(data,repeatRows=1,hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#ececef")),
                ("GRID",(0,0),(-1,-1),0.4,colors.grey),
                ("VALIGN",(0,0),(-1,-1),"TOP")]))
            flow.extend([table,Spacer(1,12)])
        elif kind=="image":flow.append(Image(value,width=430,height=238))
    out=BytesIO()
    mm=72/25.4
    SimpleDocTemplate(out,pagesize=A4,leftMargin=s.marginMm*mm,rightMargin=s.marginMm*mm,
                      topMargin=s.marginMm*mm,bottomMargin=s.marginMm*mm).build(flow)
    return out.getvalue()

@router.get("/erw/v1.3.6/styles/status")
def status():
    return {"ok":True,"version":"1.3.6-style-engine","defaultPreset":"modern-academic",
            "presets":["modern-academic","classic-academic","institutional"],
            "nativeDocx":True,"nativePdf":True,"pdfFontSubstitutionPossible":True,
            "publicationCertified":False,"verifiedCDR":False}

@router.post("/erw/v1.3.6/projects/{project_id}/reports/{report_id}/styled-export/{format}")
def export(project_id:str,report_id:str,format:str,style:StyleOptions,
           authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    report=get_report(project_id,report_id,owner)
    if format=="docx":
        binary=docx_export(report,project_id,owner,style)
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif format=="pdf":
        binary=pdf_export(report,project_id,owner,style)
        mime="application/pdf"
    else:raise HTTPException(404,detail="Unsupported export format")
    return Response(binary,media_type=mime,headers={
        "Content-Disposition":"attachment; filename=erw-"+style.preset+"."+format,
        "Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})
