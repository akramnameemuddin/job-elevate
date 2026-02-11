"""
Template definitions for the resume builder app.
This file contains predefined templates that can be loaded into the database.
Each template uses Django template tags for dynamic rendering.
CSS uses direct colour values via template tags - no CSS variables needed.
"""

DEFAULT_TEMPLATES = [
    # =========================================================================
    # MODERN TEMPLATE - clean, minimal, with accent colour
    # =========================================================================
    {
        "name": "Modern",
        "description": "Clean and minimal design with a touch of color, perfect for tech professionals.",
        "html_structure": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ user_profile.full_name }} - Resume</title>
</head>
<body class="modern-resume">
<div class="resume-container">

  <header class="resume-header">
    <h1 class="header-name">{{ user_profile.full_name }}</h1>
    {% if user_profile.job_title %}<p class="header-title">{{ user_profile.job_title }}</p>{% endif %}
    {% if resume.show_contact %}
    <div class="contact-row">
      {% if user_profile.email %}<span class="contact-item">{{ user_profile.email }}</span>{% endif %}
      {% if user_profile.phone_number %}<span class="contact-item">{{ user_profile.phone_number }}</span>{% endif %}
      {% if user_profile.linkedin_profile and resume.show_links %}<span class="contact-item">{{ user_profile.linkedin_profile }}</span>{% endif %}
      {% if user_profile.github_profile and resume.show_links %}<span class="contact-item">{{ user_profile.github_profile }}</span>{% endif %}
      {% if user_profile.portfolio_website and resume.show_links %}<span class="contact-item">{{ user_profile.portfolio_website }}</span>{% endif %}
    </div>
    {% endif %}
  </header>

  <main class="resume-body">

    {% if resume.show_objective and user_profile.objective %}
    <section class="section">
      <h2 class="section-heading">Professional Summary</h2>
      <p class="summary-text">{{ user_profile.objective }}</p>
    </section>
    {% endif %}

    {% if resume.show_education and user_profile.university %}
    <section class="section">
      <h2 class="section-heading">Education</h2>
      <div class="entry">
        <div class="entry-row">
          <span class="entry-title">{{ user_profile.degree }}</span>
          <span class="entry-date">{{ user_profile.graduation_year }}</span>
        </div>
        <p class="entry-subtitle">{{ user_profile.university }}</p>
        {% if user_profile.cgpa %}<p class="entry-meta">CGPA: {{ user_profile.cgpa }}</p>{% endif %}
      </div>
    </section>
    {% endif %}

    {% if resume.show_skills and technical_skills %}
    <section class="section">
      <h2 class="section-heading">Technical Skills</h2>
      <div class="skills-wrap">
        {% for skill in technical_skills %}<span class="skill-tag">{{ skill }}</span>{% endfor %}
      </div>
    </section>
    {% endif %}

    {% if resume.show_experience and work_experience %}
    <section class="section">
      <h2 class="section-heading">Work Experience</h2>
      {% for job in work_experience %}
      <div class="entry">
        <div class="entry-row">
          <span class="entry-title">{{ job.title }}</span>
          <span class="entry-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
        </div>
        <p class="entry-subtitle">{{ job.company }}</p>
        {% if job.description %}<div class="entry-body">{{ job.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_experience and internships %}
    <section class="section">
      <h2 class="section-heading">Internships</h2>
      {% for internship in internships %}
      <div class="entry">
        <div class="entry-row">
          <span class="entry-title">{{ internship.title }}</span>
          <span class="entry-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
        </div>
        <p class="entry-subtitle">{{ internship.company }}</p>
        {% if internship.description %}<div class="entry-body">{{ internship.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_projects and projects %}
    <section class="section">
      <h2 class="section-heading">Projects</h2>
      {% for project in projects %}
      <div class="entry">
        <div class="entry-row">
          <span class="entry-title">{{ project.title }}</span>
          {% if project.technologies %}<span class="entry-date">{{ project.technologies }}</span>{% endif %}
        </div>
        {% if project.url %}<p class="entry-link">{{ project.url }}</p>{% endif %}
        {% if project.description %}<div class="entry-body">{{ project.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_certifications and certifications %}
    <section class="section">
      <h2 class="section-heading">Certifications</h2>
      {% for cert in certifications %}
      <div class="cert-row">
        <strong>{{ cert.name }}</strong>
        {% if cert.issuing_organization %}<span class="cert-org"> - {{ cert.issuing_organization }}</span>{% endif %}
        {% if cert.date %}<span class="cert-date">({{ cert.date }})</span>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_achievements and achievements_list %}
    <section class="section">
      <h2 class="section-heading">Achievements</h2>
      <ul class="bullet-list">
        {% for achievement in achievements_list %}<li>{{ achievement }}</li>{% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
    <section class="section">
      <h2 class="section-heading">Extracurricular Activities</h2>
      <div class="entry-body">{{ user_profile.extracurricular_activities|linebreaks }}</div>
    </section>
    {% endif %}

  </main>
</div>
</body>
</html>""",

        "css_structure": """/* Modern Resume Template */
*{margin:0;padding:0;box-sizing:border-box}
body.modern-resume{
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size:13px; line-height:1.55; color:#333; background:#fff;
}
.resume-container{max-width:8.5in;margin:0 auto;padding:.65in .6in}

.resume-header{text-align:center;padding-bottom:.7rem;margin-bottom:.5rem;
  border-bottom:2.5px solid """ + "{{ resume.primary_color|default:'#4f46e5' }}" + """}
.header-name{font-size:26px;font-weight:700;color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;letter-spacing:.5px;margin-bottom:2px}
.header-title{font-size:14px;color:#666;margin-bottom:6px}
.contact-row{display:flex;justify-content:center;flex-wrap:wrap;gap:.3rem .9rem;font-size:11.5px;color:#555}
.contact-item{white-space:nowrap}
.contact-item + .contact-item::before{content:'|';margin-right:.9rem;color:#ccc}

.section{margin-bottom:.75rem}
.section-heading{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  border-bottom:1.5px solid """ + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  padding-bottom:3px;margin-bottom:8px}

.entry{margin-bottom:10px}
.entry-row{display:flex;justify-content:space-between;align-items:baseline}
.entry-title{font-weight:600;font-size:13px;color:#222}
.entry-date{font-size:11.5px;color:#888;white-space:nowrap}
.entry-subtitle{font-size:12px;color:#555;margin-bottom:2px}
.entry-meta{font-size:11px;color:#888}
.entry-link{font-size:11px;color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;margin-bottom:2px}
.entry-body{font-size:12.5px;color:#444}
.entry-body p{margin-bottom:3px}

.summary-text{font-size:12.5px;color:#444;text-align:justify}

.skills-wrap{display:flex;flex-wrap:wrap;gap:6px}
.skill-tag{background:#f0f0ff;border:1px solid #e0e0ef;border-radius:3px;
  padding:2px 10px;font-size:11.5px;color:#444}

.cert-row{margin-bottom:4px;font-size:12.5px}
.cert-org{color:#555} .cert-date{color:#888;font-size:11px}

.bullet-list{padding-left:1.3rem;font-size:12.5px;color:#444}
.bullet-list li{margin-bottom:3px}

@media print{
  body{background:#fff}
  .resume-container{padding:0;max-width:100%}
  .section{page-break-inside:avoid}
}
@page{size:A4;margin:.6in}
"""
    },

    # =========================================================================
    # PROFESSIONAL TEMPLATE - traditional, serif-based, corporate
    # =========================================================================
    {
        "name": "Professional",
        "description": "Traditional and elegant layout for corporate roles and experienced professionals.",
        "html_structure": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ user_profile.full_name }} - Professional Resume</title>
</head>
<body class="professional-resume">
<div class="resume-container">

  <header class="resume-header">
    <h1 class="name">{{ user_profile.full_name }}</h1>
    {% if user_profile.job_title %}<p class="jobtitle">{{ user_profile.job_title }}</p>{% endif %}
    <div class="header-rule"></div>
    {% if resume.show_contact %}
    <div class="contact-bar">
      {% if user_profile.email %}<span>{{ user_profile.email }}</span>{% endif %}
      {% if user_profile.phone_number %}<span>{{ user_profile.phone_number }}</span>{% endif %}
      {% if user_profile.linkedin_profile and resume.show_links %}<span>{{ user_profile.linkedin_profile }}</span>{% endif %}
      {% if user_profile.github_profile and resume.show_links %}<span>{{ user_profile.github_profile }}</span>{% endif %}
      {% if user_profile.portfolio_website and resume.show_links %}<span>{{ user_profile.portfolio_website }}</span>{% endif %}
    </div>
    {% endif %}
  </header>

  <main class="resume-body">

    {% if resume.show_objective and user_profile.objective %}
    <section class="section">
      <h2 class="section-heading">Professional Summary</h2>
      <p class="body-text">{{ user_profile.objective }}</p>
    </section>
    {% endif %}

    {% if resume.show_experience and work_experience %}
    <section class="section">
      <h2 class="section-heading">Professional Experience</h2>
      {% for job in work_experience %}
      <div class="entry">
        <div class="entry-top">
          <div class="entry-left">
            <span class="entry-title">{{ job.title }}</span>
            <span class="entry-org">{{ job.company }}</span>
          </div>
          <span class="entry-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
        </div>
        {% if job.description %}<div class="entry-body">{{ job.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_experience and internships %}
    <section class="section">
      <h2 class="section-heading">Internship Experience</h2>
      {% for internship in internships %}
      <div class="entry">
        <div class="entry-top">
          <div class="entry-left">
            <span class="entry-title">{{ internship.title }}</span>
            <span class="entry-org">{{ internship.company }}</span>
          </div>
          <span class="entry-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
        </div>
        {% if internship.description %}<div class="entry-body">{{ internship.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_education and user_profile.university %}
    <section class="section">
      <h2 class="section-heading">Education</h2>
      <div class="entry">
        <div class="entry-top">
          <div class="entry-left">
            <span class="entry-title">{{ user_profile.degree }}</span>
            <span class="entry-org">{{ user_profile.university }}</span>
          </div>
          <span class="entry-date">{{ user_profile.graduation_year }}</span>
        </div>
        {% if user_profile.cgpa %}<p class="entry-meta">CGPA: {{ user_profile.cgpa }}</p>{% endif %}
      </div>
    </section>
    {% endif %}

    {% if resume.show_skills and technical_skills %}
    <section class="section">
      <h2 class="section-heading">Technical Skills</h2>
      <p class="body-text">{{ technical_skills|join:", " }}</p>
    </section>
    {% endif %}

    {% if resume.show_projects and projects %}
    <section class="section">
      <h2 class="section-heading">Projects</h2>
      {% for project in projects %}
      <div class="entry">
        <span class="entry-title">{{ project.title }}</span>
        {% if project.technologies %}<span class="entry-tech">{{ project.technologies }}</span>{% endif %}
        {% if project.description %}<div class="entry-body">{{ project.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_certifications and certifications %}
    <section class="section">
      <h2 class="section-heading">Certifications</h2>
      <ul class="plain-list">
        {% for cert in certifications %}
        <li><strong>{{ cert.name }}</strong>{% if cert.issuing_organization %} - {{ cert.issuing_organization }}{% endif %}{% if cert.date %} ({{ cert.date }}){% endif %}</li>
        {% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if resume.show_achievements and achievements_list %}
    <section class="section">
      <h2 class="section-heading">Achievements</h2>
      <ul class="bullet-list">
        {% for achievement in achievements_list %}<li>{{ achievement }}</li>{% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
    <section class="section">
      <h2 class="section-heading">Extracurricular Activities</h2>
      <div class="entry-body">{{ user_profile.extracurricular_activities|linebreaks }}</div>
    </section>
    {% endif %}

  </main>
</div>
</body>
</html>""",

        "css_structure": """/* Professional Resume Template */
*{margin:0;padding:0;box-sizing:border-box}
body.professional-resume{
  font-family: Georgia, 'Times New Roman', serif;
  font-size:13px; line-height:1.5; color:#333; background:#fff;
}
.resume-container{max-width:8.5in;margin:0 auto;padding:.65in .6in}

.resume-header{text-align:center;margin-bottom:.6rem}
.name{font-size:28px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#222;margin-bottom:2px}
.jobtitle{font-size:14px;color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;margin-bottom:6px}
.header-rule{height:2px;background:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;margin:6px auto 8px;width:100%}
.contact-bar{display:flex;justify-content:center;flex-wrap:wrap;gap:.25rem .8rem;font-size:11.5px;color:#555}
.contact-bar span + span::before{content:'\\2022';margin-right:.8rem;color:#bbb}

.section{margin-bottom:.7rem}
.section-heading{font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;
  color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  border-bottom:1px solid """ + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  padding-bottom:3px;margin-bottom:8px}

.entry{margin-bottom:10px}
.entry-top{display:flex;justify-content:space-between;align-items:baseline}
.entry-left{display:flex;flex-direction:column}
.entry-title{font-weight:700;font-size:13px;color:#222}
.entry-org{font-style:italic;font-size:12px;color:#555}
.entry-date{font-size:11.5px;color:#888;white-space:nowrap;font-style:italic}
.entry-meta{font-size:11px;color:#888;margin-top:1px}
.entry-tech{font-size:11px;color:#888;margin-left:6px}
.entry-body{font-size:12.5px;color:#444;margin-top:2px}
.entry-body p{margin-bottom:3px}

.body-text{font-size:12.5px;color:#444;text-align:justify}

.bullet-list{padding-left:1.3rem;font-size:12.5px;color:#444}
.bullet-list li{margin-bottom:3px}
.plain-list{list-style:none;font-size:12.5px;color:#444}
.plain-list li{margin-bottom:4px}

@media print{
  body{background:#fff}
  .resume-container{padding:0;max-width:100%}
  .section{page-break-inside:avoid}
}
@page{size:A4;margin:.6in}
"""
    },

    # =========================================================================
    # CREATIVE TEMPLATE - sidebar layout, colourful, modern
    # =========================================================================
    {
        "name": "Creative",
        "description": "Bold and distinctive two-column design to showcase your creativity and personality.",
        "html_structure": """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ user_profile.full_name }} - Creative Resume</title>
</head>
<body class="creative-resume">
<div class="resume-container">

  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="avatar">{{ user_profile.full_name|truncatechars:1 }}</div>
      <h1 class="sidebar-name">{{ user_profile.full_name }}</h1>
      {% if user_profile.job_title %}<p class="sidebar-title">{{ user_profile.job_title }}</p>{% endif %}
    </div>

    {% if resume.show_contact %}
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Contact</h3>
      <ul class="sidebar-list">
        {% if user_profile.email %}<li>{{ user_profile.email }}</li>{% endif %}
        {% if user_profile.phone_number %}<li>{{ user_profile.phone_number }}</li>{% endif %}
        {% if user_profile.linkedin_profile and resume.show_links %}<li>{{ user_profile.linkedin_profile }}</li>{% endif %}
        {% if user_profile.github_profile and resume.show_links %}<li>{{ user_profile.github_profile }}</li>{% endif %}
        {% if user_profile.portfolio_website and resume.show_links %}<li>{{ user_profile.portfolio_website }}</li>{% endif %}
      </ul>
    </div>
    {% endif %}

    {% if resume.show_skills and technical_skills %}
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Skills</h3>
      <div class="sidebar-tags">
        {% for skill in technical_skills %}<span class="sidebar-tag">{{ skill }}</span>{% endfor %}
      </div>
    </div>
    {% endif %}

    {% if resume.show_education and user_profile.university %}
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Education</h3>
      <p class="sb-bold">{{ user_profile.degree }}</p>
      <p class="sb-text">{{ user_profile.university }}</p>
      <p class="sb-light">{{ user_profile.graduation_year }}</p>
      {% if user_profile.cgpa %}<p class="sb-light">CGPA: {{ user_profile.cgpa }}</p>{% endif %}
    </div>
    {% endif %}

    {% if resume.show_certifications and certifications %}
    <div class="sidebar-section">
      <h3 class="sidebar-heading">Certifications</h3>
      {% for cert in certifications %}
      <div class="sb-cert">
        <p class="sb-bold">{{ cert.name }}</p>
        {% if cert.issuing_organization %}<p class="sb-light">{{ cert.issuing_organization }}</p>{% endif %}
        {% if cert.date %}<p class="sb-light">{{ cert.date }}</p>{% endif %}
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </aside>

  <main class="main-col">

    {% if resume.show_objective and user_profile.objective %}
    <section class="main-section">
      <h2 class="main-heading">About Me</h2>
      <p class="main-text">{{ user_profile.objective }}</p>
    </section>
    {% endif %}

    {% if resume.show_experience and work_experience %}
    <section class="main-section">
      <h2 class="main-heading">Experience</h2>
      {% for job in work_experience %}
      <div class="main-entry">
        <div class="me-top">
          <span class="me-title">{{ job.title }}</span>
          <span class="me-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
        </div>
        <p class="me-org">{{ job.company }}</p>
        {% if job.description %}<div class="me-body">{{ job.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_experience and internships %}
    <section class="main-section">
      <h2 class="main-heading">Internships</h2>
      {% for internship in internships %}
      <div class="main-entry">
        <div class="me-top">
          <span class="me-title">{{ internship.title }}</span>
          <span class="me-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
        </div>
        <p class="me-org">{{ internship.company }}</p>
        {% if internship.description %}<div class="me-body">{{ internship.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_projects and projects %}
    <section class="main-section">
      <h2 class="main-heading">Projects</h2>
      {% for project in projects %}
      <div class="main-entry">
        <span class="me-title">{{ project.title }}</span>
        {% if project.technologies %}<span class="me-tech">{{ project.technologies }}</span>{% endif %}
        {% if project.description %}<div class="me-body">{{ project.description|linebreaks }}</div>{% endif %}
      </div>
      {% endfor %}
    </section>
    {% endif %}

    {% if resume.show_achievements and achievements_list %}
    <section class="main-section">
      <h2 class="main-heading">Achievements</h2>
      <ul class="main-bullets">
        {% for achievement in achievements_list %}<li>{{ achievement }}</li>{% endfor %}
      </ul>
    </section>
    {% endif %}

    {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
    <section class="main-section">
      <h2 class="main-heading">Activities</h2>
      <div class="me-body">{{ user_profile.extracurricular_activities|linebreaks }}</div>
    </section>
    {% endif %}

  </main>
</div>
</body>
</html>""",

        "css_structure": """/* Creative Resume Template - two-column sidebar */
*{margin:0;padding:0;box-sizing:border-box}
body.creative-resume{
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size:13px; line-height:1.5; color:#333; background:#f5f5f5;
}
.resume-container{max-width:8.5in;margin:0 auto;display:flex;background:#fff;
  box-shadow:0 2px 20px rgba(0,0,0,.08);min-height:11in}

.sidebar{width:34%;background:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;color:#fff;padding:1.4rem 1.1rem;
  display:flex;flex-direction:column;gap:.1rem}
.sidebar-header{text-align:center;margin-bottom:.8rem}
.avatar{width:64px;height:64px;border-radius:50%;background:rgba(255,255,255,.2);
  margin:0 auto .6rem;display:flex;align-items:center;justify-content:center;
  font-size:26px;font-weight:700;color:#fff}
.sidebar-name{font-size:20px;font-weight:700;margin-bottom:2px}
.sidebar-title{font-size:12px;opacity:.85}

.sidebar-section{margin-bottom:.75rem}
.sidebar-heading{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;opacity:.8;
  margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid rgba(255,255,255,.25)}

.sidebar-list{list-style:none;font-size:11.5px}
.sidebar-list li{margin-bottom:5px;word-break:break-all;opacity:.92}

.sidebar-tags{display:flex;flex-wrap:wrap;gap:5px}
.sidebar-tag{background:rgba(255,255,255,.18);border-radius:3px;padding:2px 8px;font-size:11px}

.sb-bold{font-weight:600;font-size:12px;margin-bottom:1px}
.sb-text{font-size:11.5px;opacity:.9}
.sb-light{font-size:11px;opacity:.75}
.sb-cert{margin-bottom:8px}

.main-col{flex:1;padding:1.4rem 1.3rem}

.main-section{margin-bottom:.85rem}
.main-heading{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  border-bottom:2px solid """ + "{{ resume.primary_color|default:'#4f46e5' }}" + """;
  padding-bottom:3px;margin-bottom:8px}
.main-text{font-size:12.5px;color:#444;text-align:justify}

.main-entry{margin-bottom:10px}
.me-top{display:flex;justify-content:space-between;align-items:baseline}
.me-title{font-weight:600;font-size:13px;color:#222}
.me-date{font-size:11px;color:#888;white-space:nowrap}
.me-org{font-size:12px;color:""" + "{{ resume.primary_color|default:'#4f46e5' }}" + """;margin-bottom:2px}
.me-tech{font-size:11px;color:#888;margin-left:6px}
.me-body{font-size:12.5px;color:#444}
.me-body p{margin-bottom:3px}

.main-bullets{padding-left:1.2rem;font-size:12.5px;color:#444}
.main-bullets li{margin-bottom:3px}

@media print{
  body{background:#fff}
  .resume-container{box-shadow:none;max-width:100%}
  .sidebar{print-color-adjust:exact;-webkit-print-color-adjust:exact}
  .main-section{page-break-inside:avoid}
}
@page{size:A4;margin:0}

@media(max-width:600px){
  .resume-container{flex-direction:column}
  .sidebar{width:100%}
}
"""
    },
]
