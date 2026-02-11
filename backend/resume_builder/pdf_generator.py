"""
Professional PDF resume generator using ReportLab Platypus.
Builds structured resume PDFs directly from user data — no HTML conversion needed.
Supports three distinct template styles: Modern, Professional, and Creative.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, ListFlowable, ListItem, PageBreak,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import html
import re


# ---------------------------------------------------------------------------
# Template detection helper
# ---------------------------------------------------------------------------

def _detect_template(resume):
    """Detect the template style name from a resume instance."""
    if resume is None:
        return 'modern'
    template = getattr(resume, 'template', None)
    if template is None:
        return 'modern'
    name = (getattr(template, 'name', '') or '').lower().strip()
    if 'professional' in name:
        return 'professional'
    elif 'creative' in name:
        return 'creative'
    return 'modern'


# ---------------------------------------------------------------------------
# Custom flowables
# ---------------------------------------------------------------------------

class ColoredLine(Flowable):
    """A coloured horizontal rule."""
    def __init__(self, width, height=1, color=HexColor('#4f46e5')):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.height)
        self.canv.line(0, 0, self.width, 0)


class SectionHeader(Flowable):
    """Section title with coloured underline."""
    def __init__(self, text, color=HexColor('#4f46e5'), font_size=12, width=None,
                 template_style='modern'):
        super().__init__()
        self.text = text
        self.color = color
        self.font_size = font_size
        self._width = width or 460
        self.template_style = template_style

    def wrap(self, aW, aH):
        self._width = aW
        return (aW, self.font_size + 8)

    def draw(self):
        if self.template_style == 'professional':
            # Professional: serif font, uppercase, double-line border
            self.canv.setFont('Times-Bold', self.font_size)
            self.canv.setFillColor(HexColor('#1a1a2e'))
            self.canv.drawString(0, 6, self.text.upper())
            self.canv.setStrokeColor(self.color)
            self.canv.setLineWidth(0.8)
            self.canv.line(0, 0, self._width, 0)
            self.canv.setLineWidth(0.3)
            self.canv.line(0, -2.5, self._width, -2.5)
        elif self.template_style == 'creative':
            # Creative: bold sans-serif with thick colour accent bar (left side)
            self.canv.setFont('Helvetica-Bold', self.font_size)
            self.canv.setFillColor(self.color)
            # Thick left accent bar
            self.canv.setFillColor(self.color)
            self.canv.rect(0, -2, 3, self.font_size + 6, fill=1, stroke=0)
            self.canv.setFillColor(self.color)
            self.canv.drawString(10, 6, self.text.upper())
            # Thin bottom line
            self.canv.setStrokeColor(HexColor('#e0e0e0'))
            self.canv.setLineWidth(0.5)
            self.canv.line(0, -2, self._width, -2)
        else:
            # Modern: clean sans-serif with underline
            self.canv.setFont('Helvetica-Bold', self.font_size)
            self.canv.setFillColor(self.color)
            self.canv.drawString(0, 6, self.text.upper())
            self.canv.setStrokeColor(self.color)
            self.canv.setLineWidth(1.2)
            self.canv.line(0, 0, self._width, 0)


# ---------------------------------------------------------------------------
# Style factory — produces template-specific paragraph styles
# ---------------------------------------------------------------------------

def _build_styles(primary_color='#4f46e5', secondary_color='#6b7280',
                  template_style='modern'):
    """Create all paragraph styles used in the PDF, adapted by template."""
    pc = HexColor(primary_color)
    sc = HexColor(secondary_color)

    # Font families per template
    if template_style == 'professional':
        heading_font = 'Times-Bold'
        heading_italic = 'Times-BoldItalic'
        body_font = 'Times-Roman'
        body_italic = 'Times-Italic'
        name_align = TA_LEFT
        header_align = TA_LEFT
        name_size = 20
        name_color = HexColor('#1a1a2e')
    elif template_style == 'creative':
        heading_font = 'Helvetica-Bold'
        heading_italic = 'Helvetica-BoldOblique'
        body_font = 'Helvetica'
        body_italic = 'Helvetica-Oblique'
        name_align = TA_LEFT
        header_align = TA_LEFT
        name_size = 24
        name_color = pc
    else:  # modern
        heading_font = 'Helvetica-Bold'
        heading_italic = 'Helvetica-BoldOblique'
        body_font = 'Helvetica'
        body_italic = 'Helvetica-Oblique'
        name_align = TA_CENTER
        header_align = TA_CENTER
        name_size = 22
        name_color = pc

    styles = {
        'name': ParagraphStyle(
            'Name', fontName=heading_font, fontSize=name_size,
            textColor=name_color, alignment=name_align, spaceAfter=2,
            leading=name_size + 4,
        ),
        'job_title': ParagraphStyle(
            'JobTitle', fontName=body_font, fontSize=11,
            textColor=sc, alignment=header_align, spaceAfter=4,
            leading=14,
        ),
        'contact': ParagraphStyle(
            'Contact', fontName=body_font, fontSize=9,
            textColor=HexColor('#555555'), alignment=header_align,
            spaceAfter=2, leading=12,
        ),
        'section_title': ParagraphStyle(
            'SectionTitle', fontName=heading_font, fontSize=11,
            textColor=pc, spaceBefore=10, spaceAfter=4,
            leading=14,
        ),
        'body': ParagraphStyle(
            'Body', fontName=body_font, fontSize=10,
            textColor=HexColor('#333333'), alignment=TA_JUSTIFY,
            spaceAfter=4, leading=13,
        ),
        'item_title': ParagraphStyle(
            'ItemTitle', fontName=heading_font, fontSize=10,
            textColor=HexColor('#222222'), spaceAfter=1,
            leading=13,
        ),
        'item_subtitle': ParagraphStyle(
            'ItemSubtitle', fontName=body_font, fontSize=9,
            textColor=sc, spaceAfter=1, leading=12,
        ),
        'item_date': ParagraphStyle(
            'ItemDate', fontName=body_italic, fontSize=9,
            textColor=sc, alignment=TA_RIGHT, leading=12,
        ),
        'bullet': ParagraphStyle(
            'Bullet', fontName=body_font, fontSize=9.5,
            textColor=HexColor('#444444'), leftIndent=14,
            bulletIndent=4, spaceAfter=2, leading=12,
            bulletFontName=body_font, bulletFontSize=9.5,
        ),
        'skill_tag': ParagraphStyle(
            'SkillTag', fontName=body_font, fontSize=9,
            textColor=HexColor('#333333'), leading=12,
        ),
    }

    # Professional template: adjust specific styles
    if template_style == 'professional':
        styles['name'].spaceBefore = 4
        styles['name'].spaceAfter = 1
        styles['body'].alignment = TA_LEFT
        styles['bullet'].textColor = HexColor('#333333')

    # Creative template: adjust
    if template_style == 'creative':
        styles['name'].spaceBefore = 0
        styles['name'].spaceAfter = 1

    return styles, pc, sc


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _clean(text):
    """Sanitise text for ReportLab Paragraph (escape XML entities, strip HTML)."""
    if not text:
        return ''
    text = str(text)
    # strip HTML tags
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.escape(text, quote=False)
    # ReportLab uses <br/> for newlines inside Paragraph
    text = text.replace('\n', '<br/>')
    return text


def _add_section_header(story, title, pc, template_style='modern'):
    """Append a section header flowable."""
    story.append(SectionHeader(title, color=pc, template_style=template_style))
    story.append(Spacer(1, 6))


def _make_two_col_row(left_text, right_text, styles):
    """Create a two-column table row (title left, date right)."""
    data = [[
        Paragraph(left_text, styles['item_title']),
        Paragraph(right_text, styles['item_date']),
    ]]
    t = Table(data, colWidths=['75%', '25%'])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_header(story, user, styles, resume=None, template_style='modern', pc=None):
    """Name, job title, and contact line — varies by template."""
    if template_style == 'professional':
        # Professional: left-aligned name with thin underline
        story.append(Paragraph(_clean(user.full_name), styles['name']))
        job_title = getattr(user, 'job_title', '') or ''
        if job_title:
            story.append(Paragraph(_clean(job_title), styles['job_title']))
        story.append(Spacer(1, 2))
    elif template_style == 'creative':
        # Creative: name with colour accent
        story.append(Paragraph(_clean(user.full_name), styles['name']))
        job_title = getattr(user, 'job_title', '') or ''
        if job_title:
            story.append(Paragraph(_clean(job_title), styles['job_title']))
        story.append(Spacer(1, 2))
    else:
        # Modern: centered
        story.append(Paragraph(_clean(user.full_name), styles['name']))
        job_title = getattr(user, 'job_title', '') or ''
        if job_title:
            story.append(Paragraph(_clean(job_title), styles['job_title']))

    # Contact info line
    parts = []
    if user.email:
        parts.append(user.email)
    if user.phone_number:
        parts.append(str(user.phone_number))
    if getattr(user, 'location', ''):
        parts.append(user.location)

    show_links = getattr(resume, 'show_links', True) if resume else True
    if show_links:
        if getattr(user, 'linkedin_profile', ''):
            parts.append(user.linkedin_profile)
        if getattr(user, 'github_profile', ''):
            parts.append(user.github_profile)
        if getattr(user, 'portfolio_website', ''):
            parts.append(user.portfolio_website)

    if parts:
        separator = '  •  ' if template_style == 'creative' else '  |  '
        contact_line = separator.join(parts)
        story.append(Paragraph(_clean(contact_line), styles['contact']))

    story.append(Spacer(1, 4))


def _build_objective(story, user, styles, pc, template_style='modern'):
    """Professional summary / objective."""
    objective = getattr(user, 'objective', '') or ''
    if not objective:
        return
    title = 'Profile' if template_style == 'professional' else 'Professional Summary'
    _add_section_header(story, title, pc, template_style)
    story.append(Paragraph(_clean(objective), styles['body']))
    story.append(Spacer(1, 2))


def _build_education(story, user, styles, pc, template_style='modern'):
    """Education section."""
    university = getattr(user, 'university', '') or ''
    if not university:
        return
    _add_section_header(story, 'Education', pc, template_style)
    degree = getattr(user, 'degree', '') or ''
    grad_year = getattr(user, 'graduation_year', '') or ''
    cgpa = getattr(user, 'cgpa', '') or ''

    row = _make_two_col_row(
        _clean(degree),
        _clean(str(grad_year)),
        styles,
    )
    story.append(row)
    story.append(Paragraph(_clean(university), styles['item_subtitle']))
    if cgpa:
        story.append(Paragraph(f"CGPA: {_clean(str(cgpa))}", styles['item_subtitle']))
    story.append(Spacer(1, 4))


def _build_skills(story, skills, styles, pc, template_style='modern'):
    """Technical skills as a compact comma-separated list or tag grid."""
    if not skills:
        return
    _add_section_header(story, 'Technical Skills', pc, template_style)

    # Build a wrapped table of skill tags
    cols = 4
    rows_data = []
    row = []
    for i, skill in enumerate(skills):
        row.append(Paragraph(f"• {_clean(skill)}", styles['skill_tag']))
        if len(row) == cols:
            rows_data.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append(Paragraph('', styles['skill_tag']))
        rows_data.append(row)

    if rows_data:
        col_width = '25%'
        t = Table(rows_data, colWidths=[col_width] * cols)
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
    story.append(Spacer(1, 2))


def _build_experience(story, work_experience, styles, pc, label='Work Experience',
                      template_style='modern'):
    """Work experience / internship items."""
    if not work_experience:
        return
    _add_section_header(story, label, pc, template_style)

    for job in work_experience:
        title = job.get('title', job.get('role', ''))
        company = job.get('company', '')
        start = job.get('start_date', '')
        end = job.get('end_date', 'Present')
        desc = job.get('description', '')

        elements = []
        elements.append(_make_two_col_row(
            _clean(title),
            _clean(f"{start} – {end}"),
            styles,
        ))
        if company:
            elements.append(Paragraph(_clean(company), styles['item_subtitle']))

        # Parse description into bullet points
        if desc:
            desc_clean = re.sub(r'<br\s*/?>', '\n', str(desc), flags=re.IGNORECASE)
            desc_clean = re.sub(r'<[^>]+>', '', desc_clean)
            lines = [l.strip() for l in desc_clean.split('\n') if l.strip()]
            for line in lines:
                line = line.lstrip('•-– ')
                if line:
                    elements.append(Paragraph(
                        f"• {html.escape(line)}",
                        styles['bullet'],
                    ))

        elements.append(Spacer(1, 6))
        story.append(KeepTogether(elements))


def _build_projects(story, projects, styles, pc, template_style='modern'):
    """Projects section."""
    if not projects:
        return
    _add_section_header(story, 'Projects', pc, template_style)

    for proj in projects:
        title = proj.get('title', proj.get('name', ''))
        tech = proj.get('technologies', '')
        desc = proj.get('description', '')
        url = proj.get('url', proj.get('link', ''))

        elements = []
        title_text = _clean(title)
        if tech:
            title_text += f"  <font size='8' color='#888888'>| {_clean(tech)}</font>"
        elements.append(Paragraph(title_text, styles['item_title']))

        if url:
            elements.append(Paragraph(_clean(url), styles['item_subtitle']))

        if desc:
            desc_clean = re.sub(r'<br\s*/?>', '\n', str(desc), flags=re.IGNORECASE)
            desc_clean = re.sub(r'<[^>]+>', '', desc_clean)
            lines = [l.strip() for l in desc_clean.split('\n') if l.strip()]
            for line in lines:
                line = line.lstrip('•-– ')
                if line:
                    elements.append(Paragraph(
                        f"• {html.escape(line)}",
                        styles['bullet'],
                    ))

        elements.append(Spacer(1, 6))
        story.append(KeepTogether(elements))


def _build_certifications(story, certifications, styles, pc, template_style='modern'):
    """Certifications section."""
    if not certifications:
        return
    _add_section_header(story, 'Certifications', pc, template_style)

    for cert in certifications:
        name = cert.get('name', cert.get('title', ''))
        org = cert.get('issuing_organization', cert.get('organization', ''))
        date = cert.get('date', cert.get('issue_date', ''))

        line = _clean(name)
        sub_parts = []
        if org:
            sub_parts.append(_clean(org))
        if date:
            sub_parts.append(_clean(str(date)))

        story.append(Paragraph(f"• <b>{line}</b>", styles['bullet']))
        if sub_parts:
            story.append(Paragraph(
                f"  {' | '.join(sub_parts)}", styles['item_subtitle']
            ))

    story.append(Spacer(1, 4))


def _build_achievements(story, achievements_list, styles, pc, template_style='modern'):
    """Achievements section."""
    if not achievements_list:
        return
    _add_section_header(story, 'Achievements', pc, template_style)
    for ach in achievements_list:
        story.append(Paragraph(f"• {_clean(ach)}", styles['bullet']))
    story.append(Spacer(1, 4))


def _build_extracurricular(story, text, styles, pc, template_style='modern'):
    """Extra-curricular activities."""
    if not text:
        return
    _add_section_header(story, 'Extra-Curricular Activities', pc, template_style)
    story.append(Paragraph(_clean(text), styles['body']))
    story.append(Spacer(1, 4))


# ---------------------------------------------------------------------------
# Creative template — two-column sidebar layout
# ---------------------------------------------------------------------------

class _SidebarHeading(Flowable):
    """Section heading for creative sidebar (white text + translucent divider)."""
    def __init__(self, text, width=None):
        super().__init__()
        self.text = text.upper()
        self._width = width or 150

    def wrap(self, aW, aH):
        self._width = aW
        return (aW, 20)

    def draw(self):
        self.canv.setFont('Helvetica-Bold', 9)
        self.canv.setFillColor(Color(1, 1, 1, alpha=0.8))
        self.canv.drawString(0, 8, self.text)
        self.canv.setStrokeColor(Color(1, 1, 1, alpha=0.25))
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 2, self._width, 2)


class _AvatarCircle(Flowable):
    """Round avatar circle with initial letter for creative sidebar."""
    def __init__(self, letter, bg_color=None, size=52):
        super().__init__()
        self.letter = letter
        self.bg = bg_color or Color(1, 1, 1, alpha=0.2)
        self.size = size
        self._width = None

    def wrap(self, aW, aH):
        self._width = aW
        return (aW, self.size + 8)

    def draw(self):
        cx = (self._width or 150) / 2  # center within available cell width
        cy = 4
        r = self.size / 2
        self.canv.setFillColor(self.bg)
        self.canv.circle(cx, cy + r, r, fill=1, stroke=0)
        self.canv.setFillColor(white)
        self.canv.setFont('Helvetica-Bold', 22)
        tw = self.canv.stringWidth(self.letter, 'Helvetica-Bold', 22)
        self.canv.drawString(cx - tw / 2, cy + r - 8, self.letter)


def _build_creative_sidebar(user_profile, skills, certifications, resume, pc, inner_w):
    """Build sidebar flowables (white text on coloured background)."""
    elements = []

    # Styles — all white text
    name_s = ParagraphStyle('CrName', fontName='Helvetica-Bold', fontSize=18,
                            textColor=white, alignment=TA_CENTER, spaceAfter=2, leading=22)
    title_s = ParagraphStyle('CrTitle', fontName='Helvetica', fontSize=10,
                             textColor=Color(1, 1, 1, alpha=0.85), alignment=TA_CENTER, spaceAfter=6)
    text_s = ParagraphStyle('CrText', fontName='Helvetica', fontSize=9.5,
                            textColor=Color(1, 1, 1, alpha=0.92), spaceAfter=3, leading=12)
    light_s = ParagraphStyle('CrLight', fontName='Helvetica', fontSize=8.5,
                             textColor=Color(1, 1, 1, alpha=0.7), spaceAfter=2, leading=11)
    bold_s = ParagraphStyle('CrBold', fontName='Helvetica-Bold', fontSize=9.5,
                            textColor=Color(1, 1, 1, alpha=0.95), spaceAfter=1, leading=12)
    tag_s = ParagraphStyle('CrTag', fontName='Helvetica', fontSize=8.5,
                           textColor=white, leading=12, alignment=TA_CENTER)

    # Avatar + Name
    initial = (user_profile.full_name or '?')[0].upper()
    elements.append(_AvatarCircle(initial))
    elements.append(Paragraph(_clean(user_profile.full_name), name_s))
    job_title = getattr(user_profile, 'job_title', '') or ''
    if job_title:
        elements.append(Paragraph(_clean(job_title), title_s))

    # Contact
    elements.append(_SidebarHeading('Contact'))
    if user_profile.email:
        elements.append(Paragraph(_clean(user_profile.email), text_s))
    if user_profile.phone_number:
        elements.append(Paragraph(_clean(str(user_profile.phone_number)), text_s))
    show_links = getattr(resume, 'show_links', True) if resume else True
    if show_links:
        for attr in ('linkedin_profile', 'github_profile', 'portfolio_website'):
            val = getattr(user_profile, attr, '')
            if val:
                elements.append(Paragraph(_clean(val), light_s))
    elements.append(Spacer(1, 4))

    # Skills
    if skills:
        elements.append(_SidebarHeading('Skills'))
        cols = 2
        rows_data, row = [], []
        for s in skills:
            row.append(Paragraph(_clean(s), tag_s))
            if len(row) == cols:
                rows_data.append(row)
                row = []
        if row:
            while len(row) < cols:
                row.append(Paragraph('', tag_s))
            rows_data.append(row)
        if rows_data:
            cw = inner_w / cols
            tbl = Table(rows_data, colWidths=[cw] * cols)
            cmds = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]
            for r_idx, r_data in enumerate(rows_data):
                for c_idx in range(cols):
                    if r_data[c_idx] is not None and (hasattr(r_data[c_idx], 'text') and r_data[c_idx].text):
                        cmds.append(('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx),
                                     Color(1, 1, 1, alpha=0.18)))
            tbl.setStyle(TableStyle(cmds))
            elements.append(tbl)
        elements.append(Spacer(1, 4))

    # Education
    university = getattr(user_profile, 'university', '') or ''
    if university:
        elements.append(_SidebarHeading('Education'))
        degree = getattr(user_profile, 'degree', '') or ''
        if degree:
            elements.append(Paragraph(_clean(degree), bold_s))
        elements.append(Paragraph(_clean(university), text_s))
        grad_year = getattr(user_profile, 'graduation_year', '') or ''
        if grad_year:
            elements.append(Paragraph(_clean(str(grad_year)), light_s))
        cgpa = getattr(user_profile, 'cgpa', '') or ''
        if cgpa:
            elements.append(Paragraph(f"CGPA: {_clean(str(cgpa))}", light_s))
        elements.append(Spacer(1, 4))

    # Certifications
    if certifications:
        elements.append(_SidebarHeading('Certifications'))
        for cert in certifications:
            name = cert.get('name', cert.get('title', ''))
            org = cert.get('issuing_organization', cert.get('organization', ''))
            elements.append(Paragraph(_clean(name), bold_s))
            if org:
                elements.append(Paragraph(_clean(org), light_s))
            elements.append(Spacer(1, 3))

    return elements


def _generate_creative_resume_pdf(user, resume=None, context=None):
    """
    Generate Creative-style PDF with a two-column sidebar layout
    that visually matches the HTML preview.
    """
    primary = getattr(resume, 'primary_color', '#4f46e5') or '#4f46e5'
    if primary == '#4f46e5':
        primary = '#0d9488'
    secondary = getattr(resume, 'secondary_color', '#6b7280') or '#6b7280'
    if secondary == '#6b7280':
        secondary = '#64748b'
    pc = HexColor(primary)

    styles, _, sc = _build_styles(primary, secondary, 'creative')

    # ── Resolve data ──
    if context:
        skills = context.get('technical_skills', [])
        work_experience = context.get('work_experience', [])
        internships = context.get('internships', [])
        projects = context.get('projects', [])
        certifications = context.get('certifications', [])
        achievements_list = context.get('achievements_list', [])
        extracurricular = context.get('extracurricular_html', '')
        user_profile = context.get('user_profile', user)
    else:
        skills = user.get_skills_list() if hasattr(user, 'get_skills_list') else []
        work_experience = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
        internships = user.get_internships() if hasattr(user, 'get_internships') else []
        projects = user.get_projects() if hasattr(user, 'get_projects') else []
        certifications = user.get_certifications() if hasattr(user, 'get_certifications') else []
        achievements_list = []
        if hasattr(user, 'achievements') and user.achievements:
            achievements_list = [a.strip() for a in user.achievements.split('\n') if a.strip()]
        extracurricular = getattr(user, 'extracurricular_activities', '') or ''
        user_profile = user

    def _show(field, default=True):
        if resume is None:
            return default
        return getattr(resume, field, default)

    # ── Page geometry ──
    page_w, page_h = A4
    sidebar_frac = 0.34
    sidebar_w = page_w * sidebar_frac
    main_w = page_w * (1 - sidebar_frac)
    sidebar_inner = sidebar_w - 24  # 12px padding each side

    # ── Sidebar content ──
    sidebar = _build_creative_sidebar(
        user_profile, skills if _show('show_skills') else [],
        certifications if _show('show_certifications') else [],
        resume, pc, sidebar_inner,
    )

    # ── Main content (reuse existing section builders) ──
    main = []
    main.append(Spacer(1, 4))
    if _show('show_objective'):
        _build_objective(main, user_profile, styles, pc, 'creative')
    if _show('show_experience'):
        _build_experience(main, work_experience, styles, pc,
                          label='Experience', template_style='creative')
        if internships:
            _build_experience(main, internships, styles, pc,
                              label='Internships', template_style='creative')
    if _show('show_projects'):
        _build_projects(main, projects, styles, pc, 'creative')
    if _show('show_education'):
        _build_education(main, user_profile, styles, pc, 'creative')
    if _show('show_achievements'):
        _build_achievements(main, achievements_list, styles, pc, 'creative')
    if _show('show_extracurricular'):
        _build_extracurricular(main, extracurricular, styles, pc, 'creative')

    # ── Assemble two-column Table ──
    layout_data = [[sidebar, main]]
    layout_table = Table(layout_data, colWidths=[sidebar_w, main_w])
    layout_table.setStyle(TableStyle([
        # Sidebar — coloured background
        ('BACKGROUND', (0, 0), (0, -1), pc),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Sidebar padding
        ('LEFTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (0, 0), (0, -1), 12),
        ('TOPPADDING', (0, 0), (0, -1), 16),
        ('BOTTOMPADDING', (0, 0), (0, -1), 16),
        # Main column padding
        ('LEFTPADDING', (1, 0), (1, -1), 16),
        ('RIGHTPADDING', (1, 0), (1, -1), 14),
        ('TOPPADDING', (1, 0), (1, -1), 16),
        ('BOTTOMPADDING', (1, 0), (1, -1), 16),
    ]))

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=0, bottomMargin=0, leftMargin=0, rightMargin=0,
        title=f"{user_profile.full_name} – Resume",
        author=user_profile.full_name,
    )
    doc.build([layout_table])
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_resume_pdf(user, resume=None, context=None):
    """
    Generate a professional PDF resume and return bytes.

    Parameters
    ----------
    user : accounts.models.User  (or proxy with same attributes)
    resume : Resume model instance (optional – used for colours & section toggles)
    context : dict (optional – pre-built context from _build_tailored_context)

    Returns
    -------
    bytes – The PDF file content.
    """
    # Detect template style
    template_style = _detect_template(resume)

    # Creative template uses a completely different two-column layout
    if template_style == 'creative':
        return _generate_creative_resume_pdf(user, resume, context)

    # Resolve colours from resume customisation
    primary = getattr(resume, 'primary_color', '#4f46e5') or '#4f46e5'
    secondary = getattr(resume, 'secondary_color', '#6b7280') or '#6b7280'

    # Professional template: override to classic dark blue
    if template_style == 'professional' and primary == '#4f46e5':
        primary = '#1a1a2e'
        secondary = '#555555'
    # Creative template: override to vibrant teal if using default
    elif template_style == 'creative' and primary == '#4f46e5':
        primary = '#0d9488'
        secondary = '#64748b'

    styles, pc, sc = _build_styles(primary, secondary, template_style)

    # Resolve data sources
    if context:
        skills = context.get('technical_skills', [])
        work_experience = context.get('work_experience', [])
        internships = context.get('internships', [])
        projects = context.get('projects', [])
        certifications = context.get('certifications', [])
        achievements_list = context.get('achievements_list', [])
        extracurricular = context.get('extracurricular_html', '')
        user_profile = context.get('user_profile', user)
    else:
        skills = user.get_skills_list() if hasattr(user, 'get_skills_list') else []
        work_experience = user.get_work_experience() if hasattr(user, 'get_work_experience') else []
        internships = user.get_internships() if hasattr(user, 'get_internships') else []
        projects = user.get_projects() if hasattr(user, 'get_projects') else []
        certifications = user.get_certifications() if hasattr(user, 'get_certifications') else []
        achievements_list = []
        if hasattr(user, 'achievements') and user.achievements:
            achievements_list = [a.strip() for a in user.achievements.split('\n') if a.strip()]
        extracurricular = getattr(user, 'extracurricular_activities', '') or ''
        user_profile = user

    # Section visibility
    def _show(field, default=True):
        if resume is None:
            return default
        return getattr(resume, field, default)

    # Margin / page setup per template
    if template_style == 'professional':
        left_margin, right_margin = 0.75 * inch, 0.75 * inch
        top_margin, bottom_margin = 0.6 * inch, 0.6 * inch
    elif template_style == 'creative':
        left_margin, right_margin = 0.5 * inch, 0.5 * inch
        top_margin, bottom_margin = 0.45 * inch, 0.45 * inch
    else:
        left_margin, right_margin = 0.6 * inch, 0.6 * inch
        top_margin, bottom_margin = 0.5 * inch, 0.5 * inch

    # Build the PDF
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=left_margin,
        rightMargin=right_margin,
        title=f"{user_profile.full_name} – Resume",
        author=user_profile.full_name,
    )

    story = []

    # Header (always shown)
    _build_header(story, user_profile, styles, resume, template_style, pc)

    # Divider under header — varies by template
    if template_style == 'professional':
        # Professional: thin double line
        story.append(ColoredLine(doc.width, height=0.8, color=pc))
        story.append(Spacer(1, 2))
        story.append(ColoredLine(doc.width, height=0.3, color=pc))
        story.append(Spacer(1, 8))
    elif template_style == 'creative':
        # Creative: thick coloured bar
        story.append(ColoredLine(doc.width, height=3, color=pc))
        story.append(Spacer(1, 8))
    else:
        # Modern: standard coloured line
        story.append(ColoredLine(doc.width, height=1.5, color=pc))
        story.append(Spacer(1, 6))

    # Section ordering varies by template
    if template_style == 'professional':
        # Professional order: Summary → Experience → Education → Skills → Projects → Certs → etc.
        if _show('show_objective'):
            _build_objective(story, user_profile, styles, pc, template_style)
        if _show('show_experience'):
            _build_experience(story, work_experience, styles, pc,
                              label='Professional Experience', template_style=template_style)
            if internships:
                _build_experience(story, internships, styles, pc,
                                  label='Internships', template_style=template_style)
        if _show('show_education'):
            _build_education(story, user_profile, styles, pc, template_style)
        if _show('show_skills'):
            _build_skills(story, skills, styles, pc, template_style)
        if _show('show_projects'):
            _build_projects(story, projects, styles, pc, template_style)
        if _show('show_certifications'):
            _build_certifications(story, certifications, styles, pc, template_style)
        if _show('show_achievements'):
            _build_achievements(story, achievements_list, styles, pc, template_style)
        if _show('show_extracurricular'):
            _build_extracurricular(story, extracurricular, styles, pc, template_style)
    elif template_style == 'creative':
        # Creative order: Skills → Summary → Projects → Experience → Education → etc.
        if _show('show_skills'):
            _build_skills(story, skills, styles, pc, template_style)
        if _show('show_objective'):
            _build_objective(story, user_profile, styles, pc, template_style)
        if _show('show_projects'):
            _build_projects(story, projects, styles, pc, template_style)
        if _show('show_experience'):
            _build_experience(story, work_experience, styles, pc,
                              label='Work Experience', template_style=template_style)
            if internships:
                _build_experience(story, internships, styles, pc,
                                  label='Internships', template_style=template_style)
        if _show('show_education'):
            _build_education(story, user_profile, styles, pc, template_style)
        if _show('show_certifications'):
            _build_certifications(story, certifications, styles, pc, template_style)
        if _show('show_achievements'):
            _build_achievements(story, achievements_list, styles, pc, template_style)
        if _show('show_extracurricular'):
            _build_extracurricular(story, extracurricular, styles, pc, template_style)
    else:
        # Modern: default order
        if _show('show_objective'):
            _build_objective(story, user_profile, styles, pc, template_style)
        if _show('show_education'):
            _build_education(story, user_profile, styles, pc, template_style)
        if _show('show_skills'):
            _build_skills(story, skills, styles, pc, template_style)
        if _show('show_experience'):
            _build_experience(story, work_experience, styles, pc,
                              label='Work Experience', template_style=template_style)
            if internships:
                _build_experience(story, internships, styles, pc,
                                  label='Internships', template_style=template_style)
        if _show('show_projects'):
            _build_projects(story, projects, styles, pc, template_style)
        if _show('show_certifications'):
            _build_certifications(story, certifications, styles, pc, template_style)
        if _show('show_achievements'):
            _build_achievements(story, achievements_list, styles, pc, template_style)
        if _show('show_extracurricular'):
            _build_extracurricular(story, extracurricular, styles, pc, template_style)

    # Build
    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
