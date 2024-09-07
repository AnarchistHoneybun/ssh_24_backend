import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("API"))

model = genai.GenerativeModel(
    'gemini-1.5-flash-latest',
    generation_config={"response_mime_type": "application/json"},
    system_instruction="""
        You will respond with a JSON object that provides a detailed, step-by-step roadmap tailored to the user's profile, focusing on
        achieving their desired role at the specified company. The output should strictly follow the JSON structure provided. The steps 
        in the roadmap should be logical and distinct with minimal overlap. Try to make the roadmap digestible, and easy to follow as it
        will be integrated into the frontend and allow users to check each step off as they're done with it.
    """
)

def generate_roadmap_prompt(skills, education, experience, role, company, timeline, learning_style):
    prompt = f"""
    Create a detailed, personalized roadmap for a candidate with the following profile:
    - Skills: {", ".join(skills)}
    - Education: {education}
    - Experience: {experience}
    - Preferred learning style: {learning_style}
    Their goal is to become a {role} at {company} within {timeline}.

    Please create a tailored roadmap that focuses on the skills and experiences relevant for a {role} at {company}. Ignore skills not directly applicable to this goal.
    The roadmap should be provided as a JSON object with the following structure for each step:

    {{
        "Step_number": {{Number of the step}},
        "Step_name": {{Step_name}},
        "Time_frame": {{Estimated time to complete this step}},
        "Description": {{Concise description of the step}},
        "Difficulty": {{Beginner, Intermediate, Advanced}},
        "Prerequisites": [{{Any prerequisites for this step}}],
        "Sub_steps": [
            {{
                "Sub_step_number": {{Number of the sub-step}},
                "Sub_step_name": {{Name of the sub-step}},
                "Sub_step_description": {{Brief description of the sub-step}},
                "Difficulty": {{Beginner, Intermediate, Advanced}},
                "Status" : Incomplete,
                "Substep_roadmap" : None
            }}
        ],
        "Resources": [{{List of recommended resources for this step}}],
        "Status" : Incomplete,
        "roadmap_type" : {{"Choose ONE out of the following categories:
                "Software Development",
                "Electronics Engineering",
                "Creative Arts",
                "Data Science and Analytics",
                "Machine Learning and AI",
                "Web Development",
                "Digital Marketing",
                "Product Management",
                "Business and Finance",
                "Healthcare and Medicine",
                "Education and Training",
                "Human Resources",
                "Sales and Business Development",
                "Legal and Compliance",
                "Public Relations and Communications",
                "Cybersecurity",
                "Operations and Supply Chain Management",
                "Project Management",
                "Social Impact and Non-Profit Work",
                "Media and Entertainment"]
                If it doesnt fit any of them, create a category
            }}
    }}

    The substeps should be distinct, with minimal overlap.

    Ensure the roadmap covers these key areas:
    1. Skill Enhancement: Improve existing skills and add new ones relevant to {role} at {company}.
    2. Key Milestones: Define concrete achievements related to the goal.
    3. Real-World Activities: Projects, internships, competitions, contributions, and certifications.
    4. Company-Specific Focus: Highlight expectations and practices specific to {company} for {role}.
    5. Networking and Professional Growth: Suggest networking opportunities and events.

    Consider these guidelines:
    - Tailor the difficulty and content to the user's current skill level and the requirements of {role} at {company}.
    - Ensure a logical progression of steps, with advanced topics introduced only after necessary foundations are built.
    - Include specific technologies, frameworks, and practices commonly used at {company} for {role}.
    - Align recommendations with the user's preferred learning style ({learning_style}).
    - Provide specific, actionable sub-steps for each main step.

    Provide only the JSON object as the response, with no additional text or explanation.
    """
    return prompt


def generate_substep_roadmap_prompt(sub_step_name, sub_step_description, prerequisites, learning_style, role, company):
    prompt = f"""
    
    The following information is about a step in the roadmap to get {role} at {company}. Create a mini roadmap to help the user achieve the following sub-step:
    
    Sub-step Name: {sub_step_name}
    Sub-step Description: {sub_step_description}
    Prerequisites: {prerequisites}
    Preferred Learning Style: {learning_style}
    
    This mini roadmap should consist of at most 3-5 steps, depending on the step's complexity and be provided as a JSON object with the following structure:

    {{
        "Sub_step_number": {{Number of the sub-step}},
        "Step_number": {{Number of the step within the mini roadmap}},
        "Step_name": {{Name of the step}},
        "Time_frame": {{Estimated time to complete this step}},
        "Description": {{Concise description of the step}},
        "Difficulty": {{Beginner, Intermediate, Advanced}},
        "Resources": [{{List of recommended resources for this step}}],
        "Substep_roadmap" : None, 
        "Status" : Incomplete

    }}

    Ensure the mini roadmap:
    1. Breaks down the sub-step into manageable actions.
    2. Follows a logical progression, considering the prerequisites and the user's current skill level.
    3. Aligns with the user's preferred learning style ({learning_style}).
    4. Focuses on practical, actionable steps with specific resources to aid in learning.

    Provide only the JSON object as the response, with no additional text or explanation.
    """
    return prompt

def extract_json_steps(response_stream):
    accumulated_json = ""
    step_count = 1
    extracted_steps = {}

    for chunk in response_stream:
        if chunk.text:
            accumulated_json += chunk.text
        
        while True:
            step_start = accumulated_json.find(f'"{step_count}":')
            
            if step_start == -1:
                break  # No more steps to extract in the current accumulated JSON
            
            step_end = accumulated_json.find(f'"{step_count + 1}":', step_start)
            if step_end == -1:
                step_end = accumulated_json.rfind('}')  # Find the last closing brace
            
            step_json = accumulated_json[step_start:step_end].strip().rstrip(',')
            step_json = "{" + step_json + "}"
            
            try:
                parsed_step = json.loads(step_json)
                step = parsed_step[str(step_count)]
                extracted_steps[str(step_count)] = step
                
                yield {str(step_count): step}
                
                step_count += 1
                accumulated_json = accumulated_json[step_end:].strip()
                
                if accumulated_json.startswith('}'):
                    break
            except json.JSONDecodeError:
                break


def generate_content(skills, education, experience, role, company, timeline, learning_style):
    prompt = generate_roadmap_prompt(skills, education, experience, role, company, timeline, learning_style)
    return model.generate_content(prompt, stream=True)

def generate_substep(sub_step_name, sub_step_description, prerequisites, learning_style, role, company):
    prompt = generate_substep_roadmap_prompt(sub_step_name, sub_step_description, prerequisites, learning_style, role, company)
    return model.generate_content(prompt, stream=True)
