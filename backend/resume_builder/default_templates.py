"""
Template definitions for the resume builder app.
This file contains predefined templates that can be loaded into the database.
"""

DEFAULT_TEMPLATES = [
    {
        "name": "Modern",
        "description": "Clean and minimal design with a touch of color, perfect for tech professionals.",
        "html_structure": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user_profile.full_name }} - Resume</title>
</head>
<body class="modern-resume">
    <div class="resume-container">
        <!-- Header Section -->
        <header class="resume-header">
            <div class="name-title">
                <h1>{{ user_profile.full_name }}</h1>
                <h2>{{ user_profile.job_title }}</h2>
            </div>
            
            {% if resume.show_contact %}
            <div class="contact-info">
                {% if user_profile.email %}
                <div class="contact-item">
                    <i class="icon email-icon"></i>
                    <span>{{ user_profile.email }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.phone_number %}
                <div class="contact-item">
                    <i class="icon phone-icon"></i>
                    <span>{{ user_profile.phone_number }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.linkedin_profile and resume.show_links %}
                <div class="contact-item">
                    <i class="icon linkedin-icon"></i>
                    <span>{{ user_profile.linkedin_profile }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.github_profile and resume.show_links %}
                <div class="contact-item">
                    <i class="icon github-icon"></i>
                    <span>{{ user_profile.github_profile }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.portfolio_website and resume.show_links %}
                <div class="contact-item">
                    <i class="icon web-icon"></i>
                    <span>{{ user_profile.portfolio_website }}</span>
                </div>
                {% endif %}
            </div>
            {% endif %}
        </header>
        
        <!-- Main Content -->
        <main class="resume-content">
            <!-- Objective Section -->
            {% if resume.show_objective and user_profile.objective %}
            <section class="resume-section">
                <h3 class="section-title">Professional Summary</h3>
                <div class="section-content">
                    <p>{{ user_profile.objective }}</p>
                </div>
            </section>
            {% endif %}
            
            <!-- Education Section -->
            {% if resume.show_education and user_profile.university %}
            <section class="resume-section">
                <h3 class="section-title">Education</h3>
                <div class="section-content">
                    <div class="education-item">
                        <div class="edu-header">
                            <h4>{{ user_profile.degree }}</h4>
                            <span class="edu-date">{{ user_profile.graduation_year }}</span>
                        </div>
                        <div class="edu-details">
                            <p class="edu-institution">{{ user_profile.university }}</p>
                            {% if user_profile.cgpa %}
                            <p class="edu-gpa">CGPA: {{ user_profile.cgpa }}</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </section>
            {% endif %}
            
            <!-- Work Experience Section -->
            {% if resume.show_experience and work_experience %}
            <section class="resume-section">
                <h3 class="section-title">Work Experience</h3>
                <div class="section-content">
                    {% for job in work_experience %}
                    <div class="experience-item">
                        <div class="exp-header">
                            <h4>{{ job.title }}</h4>
                            <span class="exp-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
                        </div>
                        <p class="exp-company">{{ job.company }}</p>
                        <div class="exp-description">
                            {{ job.description|linebreaks }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Internships Section -->
            {% if user_profile.user_type == 'student' and resume.show_experience and internships %}
            <section class="resume-section">
                <h3 class="section-title">Internships</h3>
                <div class="section-content">
                    {% for internship in internships %}
                    <div class="experience-item">
                        <div class="exp-header">
                            <h4>{{ internship.title }}</h4>
                            <span class="exp-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
                        </div>
                        <p class="exp-company">{{ internship.company }}</p>
                        <div class="exp-description">
                            {{ internship.description|linebreaks }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Projects Section -->
            {% if resume.show_projects and projects %}
            <section class="resume-section">
                <h3 class="section-title">Projects</h3>
                <div class="section-content">
                    {% for project in projects %}
                    <div class="project-item">
                        <div class="project-header">
                            <h4>{{ project.title }}</h4>
                            {% if project.url %}
                            <a href="{{ project.url }}" class="project-link" target="_blank">View Project</a>
                            {% endif %}
                        </div>
                        <div class="project-description">
                            {{ project.description|linebreaks }}
                        </div>
                        {% if project.skills %}
                        <div class="project-tech">
                            <strong>Technologies:</strong> {{ project.skills }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Skills Section -->
            {% if resume.show_skills and technical_skills %}
            <section class="resume-section">
                <h3 class="section-title">Technical Skills</h3>
                <div class="section-content skills-grid">
                    {% for skill in technical_skills %}
                    <div class="skill-item">{{ skill }}</div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            {% if resume.show_certifications and certifications %}
            <section class="resume-section">
                <h3 class="section-title">Certifications</h3>
                <div class="section-content">
                    {% for cert in certifications %}
                    <div class="cert-item">
                        <h4>{{ cert.name }}</h4>
                        {% if cert.organization %}
                        <p class="cert-org">{{ cert.organization }}</p>
                        {% endif %}
                        {% if cert.issue_date %}
                        <p class="cert-date">{{ cert.issue_date }}</p>
                        {% endif %}
                        {% if cert.skills %}
                        <p class="cert-description">{{ cert.skills }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Achievements Section -->
            {% if resume.show_achievements and achievements_list %}
            <section class="resume-section">
                <h3 class="section-title">Achievements</h3>
                <div class="section-content">
                    <ul class="achievements-list">
                        {% for achievement in achievements_list %}
                        <li>{{ achievement }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </section>
            {% endif %}
            
            <!-- Extracurricular Activities -->
            {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
            <section class="resume-section">
                <h3 class="section-title">Extracurricular Activities</h3>
                <div class="section-content">
                    <p>{{ user_profile.extracurricular_activities|linebreaks }}</p>
                </div>
            </section>
            {% endif %}
        </main>
        
        <!-- Footer with page number when printing -->
        <footer class="resume-footer">
            <div class="page-number">Page <span class="page"></span></div>
            <div class="last-updated">Last updated: {{ resume.updated_at|date:"F d, Y" }}</div>
        </footer>
    </div>
</body>
</html>
""",
        "css_structure": """
/* Modern Resume Template CSS */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

:root {
    --primary-color: {{ resume.primary_color }};
    --secondary-color: {{ resume.secondary_color }};
    --text-color: #333;
    --light-text: #666;
    --border-color: #ddd;
    --background-color: #fff;
    --section-spacing: 1.5rem;
}

/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: {{ resume.font_family|default:"'Roboto', sans-serif" }};
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

/* Container */
.resume-container {
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.75in 0.5in;
    background-color: var(--background-color);
}

/* Header Section */
.resume-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--section-spacing);
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 1rem;
}

.name-title h1 {
    font-size: 28px;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.25rem;
}

.name-title h2 {
    font-size: 18px;
    font-weight: 500;
    color: var(--light-text);
}

.contact-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 12px;
}

.contact-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Main Content */
.resume-content {
    display: flex;
    flex-direction: column;
    gap: var(--section-spacing);
}

/* Sections */
.resume-section {
    margin-bottom: var(--section-spacing);
}

.section-title {
    font-size: 18px;
    font-weight: 500;
    color: var(--primary-color);
    margin-bottom: 0.75rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid var(--border-color);
}

/* Education */
.education-item {
    margin-bottom: 1rem;
}

.edu-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.edu-header h4 {
    font-weight: 500;
}

.edu-date {
    color: var(--light-text);
}

.edu-institution {
    font-weight: 500;
}

/* Experience */
.experience-item {
    margin-bottom: 1rem;
}

.exp-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.exp-header h4 {
    font-weight: 500;
}

.exp-date {
    color: var(--light-text);
}

.exp-company {
    font-weight: 500;
    margin-bottom: 0.25rem;
}

/* Projects */
.project-item {
    margin-bottom: 1rem;
}

.project-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.project-header h4 {
    font-weight: 500;
}

.project-link {
    color: var(--secondary-color);
    text-decoration: none;
}

.project-tech {
    margin-top: 0.5rem;
    font-size: 12px;
}

/* Skills */
.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.skill-item {
    background-color: #f5f5f5;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    font-size: 12px;
}

/* Certifications */
.cert-item {
    margin-bottom: 0.75rem;
}

.cert-item h4 {
    margin-bottom: 0.25rem;
}

.cert-org, .cert-date {
    font-size: 12px;
    color: var(--light-text);
}

/* Achievements */
.achievements-list {
    padding-left: 1.5rem;
}

.achievements-list li {
    margin-bottom: 0.5rem;
}

/* Footer */
.resume-footer {
    margin-top: 1rem;
    font-size: 10px;
    color: var(--light-text);
    display: flex;
    justify-content: space-between;
}

/* Print styles */
@media print {
    body {
        background-color: white;
    }
    
    .resume-container {
        padding: 0;
        max-width: 100%;
    }
    
    .page-number:after {
        content: counter(page);
    }
    
    .resume-container {
        page-break-after: always;
    }
    
    .resume-section {
        page-break-inside: avoid;
    }
}
"""
    },
    {
        "name": "Professional",
        "description": "Traditional and elegant layout for corporate roles and experienced professionals.",
        "html_structure": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user_profile.full_name }} - Professional Resume</title>
</head>
<body class="professional-resume">
    <div class="resume-container">
        <!-- Header Section -->
        <header class="resume-header">
            <h1 class="name">{{ user_profile.full_name }}</h1>
            {% if user_profile.job_title %}
            <h2 class="title">{{ user_profile.job_title }}</h2>
            {% endif %}
            
            {% if resume.show_contact %}
            <div class="contact-bar">
                {% if user_profile.email %}
                <div class="contact-item">
                    <span class="contact-label">Email:</span>
                    <span class="contact-value">{{ user_profile.email }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.phone_number %}
                <div class="contact-item">
                    <span class="contact-label">Phone:</span>
                    <span class="contact-value">{{ user_profile.phone_number }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.linkedin_profile and resume.show_links %}
                <div class="contact-item">
                    <span class="contact-label">LinkedIn:</span>
                    <span class="contact-value">{{ user_profile.linkedin_profile }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.github_profile and resume.show_links %}
                <div class="contact-item">
                    <span class="contact-label">GitHub:</span>
                    <span class="contact-value">{{ user_profile.github_profile }}</span>
                </div>
                {% endif %}
                
                {% if user_profile.portfolio_website and resume.show_links %}
                <div class="contact-item">
                    <span class="contact-label">Website:</span>
                    <span class="contact-value">{{ user_profile.portfolio_website }}</span>
                </div>
                {% endif %}
            </div>
            {% endif %}
        </header>
        
        <!-- Main Content -->
        <main class="resume-content">
            <!-- Objective Section -->
            {% if resume.show_objective and user_profile.objective %}
            <section class="resume-section">
                <h3 class="section-title">Professional Summary</h3>
                <div class="section-content">
                    <p>{{ user_profile.objective }}</p>
                </div>
            </section>
            {% endif %}
            
            <!-- Work Experience Section -->
            {% if resume.show_experience and work_experience %}
            <section class="resume-section">
                <h3 class="section-title">Professional Experience</h3>
                <div class="section-content">
                    {% for job in work_experience %}
                    <div class="experience-item">
                        <div class="exp-header">
                            <div class="exp-title-company">
                                <h4>{{ job.title }}</h4>
                                <p class="exp-company">{{ job.company }}</p>
                            </div>
                            <span class="exp-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
                        </div>
                        <div class="exp-description">
                            {{ job.description|linebreaks }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Internships Section -->
            {% if user_profile.user_type == 'student' and resume.show_experience and internships %}
            <section class="resume-section">
                <h3 class="section-title">Internship Experience</h3>
                <div class="section-content">
                    {% for internship in internships %}
                    <div class="experience-item">
                        <div class="exp-header">
                            <div class="exp-title-company">
                                <h4>{{ internship.title }}</h4>
                                <p class="exp-company">{{ internship.company }}</p>
                            </div>
                            <span class="exp-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
                        </div>
                        <div class="exp-description">
                            {{ internship.description|linebreaks }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Education Section -->
            {% if resume.show_education and user_profile.university %}
            <section class="resume-section">
                <h3 class="section-title">Education</h3>
                <div class="section-content">
                    <div class="education-item">
                        <div class="edu-header">
                            <div class="edu-degree-institution">
                                <h4>{{ user_profile.degree }}</h4>
                                <p class="edu-institution">{{ user_profile.university }}</p>
                            </div>
                            <span class="edu-date">{{ user_profile.graduation_year }}</span>
                        </div>
                        {% if user_profile.cgpa %}
                        <p class="edu-gpa">CGPA: {{ user_profile.cgpa }}</p>
                        {% endif %}
                    </div>
                </div>
            </section>
            {% endif %}
            
            <!-- Skills Section -->
            {% if resume.show_skills and technical_skills %}
            <section class="resume-section">
                <h3 class="section-title">Technical Skills</h3>
                <div class="section-content">
                    <div class="skills-list">
                        {% for skill in technical_skills %}
                        <span class="skill-item">{{ skill }}</span>{% if not forloop.last %}, {% endif %}
                        {% endfor %}
                    </div>
                </div>
            </section>
            {% endif %}
            
            <!-- Projects Section -->
            {% if resume.show_projects and projects %}
            <section class="resume-section">
                <h3 class="section-title">Projects</h3>
                <div class="section-content">
                    {% for project in projects %}
                    <div class="project-item">
                        <h4>{{ project.title }} {% if project.url %}<a href="{{ project.url }}" class="project-link">(View Project)</a>{% endif %}</h4>
                        <div class="project-description">
                            {{ project.description|linebreaks }}
                        </div>
                        {% if project.skills %}
                        <div class="project-tech">
                            <span class="tech-label">Technologies:</span> {{ project.skills }}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Certifications Section -->
            {% if resume.show_certifications and certifications %}
            <section class="resume-section">
                <h3 class="section-title">Certifications</h3>
                <div class="section-content">
                    <ul class="cert-list">
                        {% for cert in certifications %}
                        <li class="cert-item">
                            <strong>{{ cert.name }}</strong>
                            {% if cert.organization %} - {{ cert.organization }}{% endif %}
                            {% if cert.issue_date %} ({{ cert.issue_date }}){% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </section>
            {% endif %}
            
            <!-- Achievements Section -->
            {% if resume.show_achievements and achievements_list %}
            <section class="resume-section">
                <h3 class="section-title">Achievements</h3>
                <div class="section-content">
                    <ul class="achievements-list">
                        {% for achievement in achievements_list %}
                        <li>{{ achievement }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </section>
            {% endif %}
            
            <!-- Extracurricular Activities -->
            {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
            <section class="resume-section">
                <h3 class="section-title">Extracurricular Activities</h3>
                <div class="section-content">
                    <p>{{ user_profile.extracurricular_activities|linebreaks }}</p>
                </div>
            </section>
            {% endif %}
        </main>
        
        <!-- Footer with page number when printing -->
        <footer class="resume-footer">
            <div class="footer-content">
                {{ user_profile.full_name }} | Resume | Page <span class="page"></span>
            </div>
        </footer>
    </div>
</body>
</html>
""",
        "css_structure": """
/* Professional Resume Template CSS */
@import url('https://fonts.googleapis.com/css2?family=Times+New+Roman:wght@400;700&display=swap');

:root {
    --primary-color: {{ resume.primary_color }};
    --secondary-color: {{ resume.secondary_color }};
    --text-color: #333;
    --light-text: #666;
    --border-color: #ddd;
    --background-color: #fff;
    --section-spacing: 1.5rem;
}

/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: {{ resume.font_family|default:"'Times New Roman', serif" }};
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}

/* Container */
.resume-container {
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.75in 0.5in;
    background-color: var(--background-color);
}

/* Header Section */
.resume-header {
    text-align: center;
    margin-bottom: var(--section-spacing);
}

.name {
    font-size: 24px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.25rem;
}

.title {
    font-size: 16px;
    font-weight: normal;
    color: var(--primary-color);
    margin-bottom: 0.75rem;
}

.contact-bar {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 11px;
}

.contact-item {
    display: flex;
    gap: 0.25rem;
}

.contact-label {
    font-weight: bold;
}

/* Main Content */
.resume-content {
    display: flex;
    flex-direction: column;
    gap: var(--section-spacing);
}

/* Sections */
.resume-section {
    margin-bottom: var(--section-spacing);
}

.section-title {
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--primary-color);
    border-bottom: 1px solid var(--primary-color);
    padding-bottom: 0.25rem;
    margin-bottom: 0.75rem;
}

/* Experience */
.experience-item {
    margin-bottom: 1rem;
}

.exp-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}

.exp-title-company h4 {
    font-weight: 700;
    font-size: 13px;
}

.exp-company {
    font-style: italic;
}

.exp-date {
    font-weight: normal;
    font-style: italic;
}

/* Education */
.education-item {
    margin-bottom: 1rem;
}

.edu-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
}

.edu-degree-institution h4 {
    font-weight: 700;
    font-size: 13px;
}

.edu-institution {
    font-style: italic;
}

.edu-date {
    font-weight: normal;
    font-style: italic;
}

.edu-gpa {
    font-size: 11px;
}

/* Skills */
.skills-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

/* Projects */
.project-item {
    margin-bottom: 1rem;
}

.project-item h4 {
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 0.25rem;
}

.project-link {
    font-weight: normal;
    font-size: 11px;
    color: var(--primary-color);
    text-decoration: none;
}

.project-tech {
    font-size: 11px;
    margin-top: 0.25rem;
}

.tech-label {
    font-weight: bold;
}

/* Certifications */
.cert-list {
    list-style-type: none;
}

.cert-item {
    margin-bottom: 0.5rem;
}

/* Achievements */
.achievements-list {
    padding-left: 1.25rem;
}

.achievements-list li {
    margin-bottom: 0.5rem;
}

/* Footer */
.resume-footer {
    margin-top: var(--section-spacing);
    text-align: center;
    font-size: 9px;
    color: var(--light-text);
}

/* Print styles */
@media print {
    body {
        background-color: white;
    }
    
    .resume-container {
        padding: 0;
        max-width: 100%;
    }
    
    .page:after {
        content: counter(page);
    }
    
    .resume-container {
        page-break-after: always;
    }
    
    .resume-section {
        page-break-inside: avoid;
    }
}
"""
    },
    {
        "name": "Creative",
        "description": "Bold and distinctive design to showcase your creativity and personality.",
        "html_structure": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ user_profile.full_name }} - Creative Resume</title>
    <style>
        /* Creative Resume Template CSS */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        :root {
            --primary-color: {{ resume.primary_color }};
            --secondary-color: {{ resume.secondary_color }};
            --text-color: #333;
            --light-text: #666;
            --sidebar-bg: #f5f5f5;
            --main-bg: #ffffff;
            --accent-color: {{ resume.primary_color }};
            --border-radius: 8px;
        }

        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: {{ resume.font_family|default:"'Poppins', sans-serif" }};
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-color);
            background-color: #f9f9f9;
        }

        /* Container */
        .resume-container {
            max-width: 8.5in;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 2fr;
            background-color: var(--main-bg);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }

        /* Sidebar */
        .resume-sidebar {
            background-color: var(--sidebar-bg);
            padding: 2rem 1.5rem;
            color: var(--text-color);
        }

        .profile-container {
            text-align: center;
            margin-bottom: 2rem;
        }

        .profile-image-placeholder {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background-color: var(--primary-color);
            margin: 0 auto 1rem;
        }

        .name {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .title {
            font-size: 16px;
            font-weight: 500;
            color: var(--primary-color);
            margin-bottom: 1rem;
        }

        .sidebar-section {
            margin-bottom: 2rem;
        }

        .sidebar-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 1rem;
            position: relative;
            padding-bottom: 0.5rem;
        }

        .sidebar-title:after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 50px;
            height: 3px;
            background-color: var(--primary-color);
        }

        /* Contact styles */
        .contact-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .contact-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .contact-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 30px;
            height: 30px;
            background-color: var(--primary-color);
            color: white;
            border-radius: 50%;
            font-size: 14px;
        }

        /* Skills styles */
        .skills-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .skill-badge {
            background-color: var(--primary-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        /* Education styles */
        .education-item {
            margin-bottom: 1rem;
        }

        .degree {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .university {
            font-weight: 500;
            margin-bottom: 0.25rem;
        }

        .graduation, .gpa {
            font-size: 12px;
            color: var(--light-text);
        }

        /* Certifications styles */
        .cert-list {
            list-style: none;
        }

        .cert-item {
            margin-bottom: 1rem;
        }

        .cert-name {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .cert-org, .cert-date {
            font-size: 12px;
            color: var(--light-text);
        }

        /* Main Content */
        .resume-main {
            padding: 2rem;
            background-color: var(--main-bg);
        }

        .main-section {
            margin-bottom: 2rem;
        }

        .main-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 1.5rem;
            position: relative;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary-color);
        }

        /* Timeline styles */
        .timeline {
            position: relative;
        }

        .timeline:before {
            content: '';
            position: absolute;
            top: 0;
            bottom: 0;
            left: 16px;
            width: 2px;
            background-color: var(--primary-color);
        }

        .timeline-item {
            display: flex;
            margin-bottom: 1.5rem;
            position: relative;
        }

        .timeline-marker {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: var(--primary-color);
            flex-shrink: 0;
            margin-right: 1.5rem;
            margin-top: 6px;
            z-index: 1;
        }

        .timeline-content {
            flex-grow: 1;
        }

        .job-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }

        .job-title {
            font-weight: 600;
            font-size: 16px;
        }

        .job-date {
            font-size: 12px;
            color: var(--light-text);
        }

        .job-company {
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--primary-color);
        }

        /* Projects styles */
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
        }

        .project-card {
            border-radius: var(--border-radius);
            border: 1px solid #eee;
            padding: 1rem;
            background-color: white;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .project-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .project-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--primary-color);
        }

        .project-link {
            display: inline-block;
            color: var(--primary-color);
            text-decoration: none;
            font-size: 12px;
            margin-bottom: 0.5rem;
        }

        .tech-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-top: 0.5rem;
        }

        .tech-chip {
            font-size: 10px;
            background-color: #f0f0f0;
            padding: 0.1rem 0.5rem;
            border-radius: 12px;
        }

        /* Achievements styles */
        .achievements-list {
            padding-left: 1.5rem;
        }

        .achievement-item {
            margin-bottom: 0.75rem;
        }

        /* Print styles */
        @media print {
            body {
                background-color: white;
            }
            
            .resume-container {
                max-width: 100%;
                box-shadow: none;
            }
            
            .resume-container {
                page-break-after: always;
            }
            
            .main-section, .sidebar-section {
                page-break-inside: avoid;
            }
        }

        /* Media queries for responsiveness */
        @media (max-width: 768px) {
            .resume-container {
                grid-template-columns: 1fr;
            }
            
            .timeline:before {
                left: 12px;
            }
            
            .timeline-marker {
                width: 12px;
                height: 12px;
                margin-right: 1rem;
            }
            
            .projects-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body class="creative-resume">
    <div class="resume-container">
        <!-- Sidebar -->
        <aside class="resume-sidebar">
            <div class="profile-container">
                <div class="profile-image-placeholder"></div>
                <h1 class="name">{{ user_profile.full_name }}</h1>
                <h2 class="title">{{ user_profile.job_title }}</h2>
            </div>
            
            {% if resume.show_contact %}
            <section class="sidebar-section contact-section">
                <h3 class="sidebar-title">Contact</h3>
                <div class="contact-list">
                    {% if user_profile.email %}
                    <div class="contact-item">
                        <span class="contact-icon">✉</span>
                        <span class="contact-text">{{ user_profile.email }}</span>
                    </div>
                    {% endif %}
                    
                    {% if user_profile.phone_number %}
                    <div class="contact-item">
                        <span class="contact-icon">☏</span>
                        <span class="contact-text">{{ user_profile.phone_number }}</span>
                    </div>
                    {% endif %}
                    
                    {% if user_profile.linkedin_profile and resume.show_links %}
                    <div class="contact-item">
                        <span class="contact-icon">in</span>
                        <span class="contact-text">{{ user_profile.linkedin_profile }}</span>
                    </div>
                    {% endif %}
                    
                    {% if user_profile.github_profile and resume.show_links %}
                    <div class="contact-item">
                        <span class="contact-icon">gh</span>
                        <span class="contact-text">{{ user_profile.github_profile }}</span>
                    </div>
                    {% endif %}
                    
                    {% if user_profile.portfolio_website and resume.show_links %}
                    <div class="contact-item">
                        <span class="contact-icon">🌐</span>
                        <span class="contact-text">{{ user_profile.portfolio_website }}</span>
                    </div>
                    {% endif %}
                </div>
            </section>
            {% endif %}
            
            {% if resume.show_skills and technical_skills %}
            <section class="sidebar-section skills-section">
                <h3 class="sidebar-title">Skills</h3>
                <div class="skills-container">
                    {% for skill in technical_skills %}
                    <div class="skill-badge">{{ skill }}</div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            {% if resume.show_education and user_profile.university %}
            <section class="sidebar-section education-section">
                <h3 class="sidebar-title">Education</h3>
                <div class="education-item">
                    <h4 class="degree">{{ user_profile.degree }}</h4>
                    <p class="university">{{ user_profile.university }}</p>
                    <p class="graduation">Class of {{ user_profile.graduation_year }}</p>
                    {% if user_profile.cgpa %}
                    <p class="gpa">CGPA: {{ user_profile.cgpa }}</p>
                    {% endif %}
                </div>
            </section>
            {% endif %}
            
            {% if resume.show_certifications and certifications %}
            <section class="sidebar-section certifications-section">
                <h3 class="sidebar-title">Certifications</h3>
                <ul class="cert-list">
                    {% for cert in certifications %}
                    <li class="cert-item">
                        <div class="cert-name">{{ cert.name }}</div>
                        {% if cert.organization %}
                        <div class="cert-org">{{ cert.organization }}</div>
                        {% endif %}
                        {% if cert.issue_date %}
                        <div class="cert-date">{{ cert.issue_date }}</div>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            </section>
            {% endif %}
        </aside>
        
        <!-- Main Content -->
        <main class="resume-main">
            <!-- Objective Section -->
            {% if resume.show_objective and user_profile.objective %}
            <section class="main-section intro-section">
                <h3 class="main-title">About Me</h3>
                <div class="intro-content">
                    <p>{{ user_profile.objective }}</p>
                </div>
            </section>
            {% endif %}
            
            <!-- Work Experience Section -->
            {% if resume.show_experience and work_experience %}
            <section class="main-section experience-section">
                <h3 class="main-title">Professional Experience</h3>
                <div class="timeline">
                    {% for job in work_experience %}
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="job-header">
                                <h4 class="job-title">{{ job.title }}</h4>
                                <span class="job-date">{{ job.start_date }} - {{ job.end_date|default:"Present" }}</span>
                            </div>
                            <p class="job-company">{{ job.company }}</p>
                            <div class="job-description">
                                {{ job.description|linebreaks }}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Internships Section -->
            {% if user_profile.user_type == 'student' and resume.show_experience and internships %}
            <section class="main-section internship-section">
                <h3 class="main-title">Internships</h3>
                <div class="timeline">
                    {% for internship in internships %}
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="job-header">
                                <h4 class="job-title">{{ internship.title }}</h4>
                                <span class="job-date">{{ internship.start_date }} - {{ internship.end_date|default:"Present" }}</span>
                            </div>
                            <p class="job-company">{{ internship.company }}</p>
                            <div class="job-description">
                                {{ internship.description|linebreaks }}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Projects Section -->
            {% if resume.show_projects and projects %}
            <section class="main-section projects-section">
                <h3 class="main-title">Projects</h3>
                <div class="projects-grid">
                    {% for project in projects %}
                    <div class="project-card">
                        <h4 class="project-title">{{ project.title }}</h4>
                        {% if project.url %}
                        <a href="{{ project.url }}" class="project-link" target="_blank">View Project</a>
                        {% endif %}
                        <div class="project-description">
                            {{ project.description|linebreaks }}
                        </div>
                        {% if project.skills %}
                        <div class="project-tech">
                            <div class="tech-chips">
                                <span class="tech-chip">{{ project.skills }}</span>
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </section>
            {% endif %}
            
            <!-- Achievements Section -->
            {% if resume.show_achievements and achievements_list %}
            <section class="main-section achievements-section">
                <h3 class="main-title">Achievements</h3>
                <ul class="achievements-list">
                    {% for achievement in achievements_list %}
                    <li class="achievement-item">{{ achievement }}</li>
                    {% endfor %}
                </ul>
            </section>
            {% endif %}
            
            <!-- Extracurricular Activities -->
            {% if resume.show_extracurricular and user_profile.extracurricular_activities %}
            <section class="main-section extracurricular-section">
                <h3 class="main-title">Extracurricular Activities</h3>
                <div class="extracurricular-content">
                    {{ user_profile.extracurricular_activities|linebreaks }}
                </div>
            </section>
            {% endif %}
        </main>
    </div>
</body>
</html>
"""
    }
]