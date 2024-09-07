from fastapi import FastAPI, Form, HTTPException, Query, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from mongo import *
from roadmap import extract_json_steps

"""
To do:
Linkedin suggestions
Daily points
Badges?
Add reminder to do x, returns a daily popup

"""

origins = [
    "*",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Account creation
@app.post("/create_account_from_email")
def create_account_from_email_endpoint(email: str = Form(...)):
    success = create_account_from_email(email)
    if success == -1:
        return {"message": "Account already exists or failed to create"}
    roadmap = get_user_roadmap(email)
    return {"message": "Account created successfully", "roadmap": roadmap}

# Linkedin
@app.get("/linkedin/recommend")
def get_recommendations(username: str):
    recommendations = get_linkedin_recommendations(username)
    if recommendations is None:
        raise HTTPException(status_code=404, detail=f"User {username} not found or no roadmap types found.")
    return recommendations

@app.delete("/linkedin/remove")
def remove_linkedin_endpoint(username: str):
    if not delete_linkedin_profile(username):
        raise HTTPException(status_code=404, detail=f"User {username} not found.")
    return {"message": f"LinkedIn profile removed for user {username}."}

@app.post("/linkedin/add")
def add_linkedin_endpoint(username: str, linkedin_url: str):
    if not add_linkedin_profile(username, linkedin_url):
        raise HTTPException(status_code=404, detail=f"User {username} not found.")
    return {"message": f"LinkedIn profile added for user {username}."}


# Friends
@app.post("/friends/add")
async def add_friend_endpoint(username: str, friend_username: str):
    result = add_friend(username, friend_username)
    if result == -1:
        raise HTTPException(status_code=404, detail="User or friend not found")
    elif result == 0:
        raise HTTPException(status_code=400, detail="Friend already added")
    return {"message": f"{friend_username} added as a friend to {username}"}

@app.get("/friends/get")
async def get_friends_endpoint(username: str):
    friends = get_friends(username)
    if friends == -1:
        raise HTTPException(status_code=404, detail="User not found")
    return {"friends": friends}

@app.post("/friends/remove")
async def remove_friend_endpoint(username: str, friend_username: str):
    result = remove_friend(username, friend_username)
    if result == -1:
        raise HTTPException(status_code=404, detail="User not found")
    elif result == 0:
        raise HTTPException(status_code=400, detail=f"{friend_username} is not a friend of {username}")
    return {"message": f"{friend_username} removed as a friend of {username}"}


# Leaderboard and points
@app.get("/stats/{username}")
async def get_stats_endpoint(username: str):
    stats = get_stats(username)
    if stats == -1:
        raise HTTPException(status_code=404, detail="User not found")
    return stats

@app.get("/leaderboard/global")
def get_leaderboard_endpoint(username: str):
    try:
        position, sorted_users = get_users_sorted(username)
        if position is None:
            raise HTTPException(status_code=404, detail=f"Username '{username}' not found in the leaderboard.")

        return {
            "position": position,
            "leaderboard": sorted_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/leaderboard/friends")
async def get_friend_leaderboard_endpoint(username: str):
    result = get_friends_sorted(username)
    
    if result is None:
        raise HTTPException(status_code=404, detail="User not found or an error occurred.")
    
    return result

# Skills
@app.get("/get_skills")
def get_skills_endpoint(username: str):
    return get_skills(username)


@app.post("/add_skills")
def add_skills_endpoint(username: str = Form(...), skills: str = Form(...)):
    skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
    if not skills_list:
        raise HTTPException(status_code=400, detail="No valid skills provided")
    success = add_skills(username, skills_list)
    if success != -1:
        updated_skills = get_skills(username)
        return {"message": "Skills added successfully", "skills": updated_skills}
    else:
        raise HTTPException(status_code=400, detail="Failed to add skills")

@app.post("/delete_skills")
def delete_skills_endpoint(username: str = Form(...), skills: str = Form(...)):
    skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
    if not skills_list:
        raise HTTPException(status_code=400, detail="No valid skills provided")
    success = delete_skills(username, skills_list)
    if success != -1:
        updated_skills = get_skills(username)
        return {"message": "Skills deleted successfully", "skills": updated_skills}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete skills")

# Experience
@app.get("/get_experience")
def get_experience_endpoint(username: str):
    return get_experience(username)


@app.post("/add_experience")
def add_experience_endpoint(username: str = Form(...), experience: str = Form(...)):
    experience_list = [exp.strip() for exp in experience.split(",") if exp.strip()]
    if not experience_list:
        raise HTTPException(status_code=400, detail="No valid experience provided")
    success = add_experience(username, experience_list)
    if success != -1:
        updated_experience = get_experience(username)
        return {"message": "Experience added successfully", "experience": updated_experience}
    else:
        raise HTTPException(status_code=400, detail="Failed to add experience")


@app.post("/delete_experience")
def delete_experience_endpoint(username: str = Form(...), experience: str = Form(...)):
    experience_list = [exp.strip() for exp in experience.split(",") if exp.strip()]
    if not experience_list:
        raise HTTPException(status_code=400, detail="No valid experience provided")
    success = delete_experience(username, experience_list)
    if success != -1:
        updated_experience = get_experience(username)
        return {"message": "Experience deleted successfully", "experience": updated_experience}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete experience")
    
# Education
@app.get("/get_education")
def get_education_endpoint(username: str):
    return get_education(username)


@app.post("/add_education")
def add_education_endpoint(username: str = Form(...), education: str = Form(...)):
    education_list = [edu.strip() for edu in education.split(",") if edu.strip()]
    if not education_list:
        raise HTTPException(status_code=400, detail="No valid education provided")
    success = add_education(username, education_list)
    if success != -1:
        updated_education = get_education(username)
        return {"message": "Education added successfully", "education": updated_education}
    else:
        raise HTTPException(status_code=400, detail="Failed to add education")


@app.post("/delete_education")
def delete_education_endpoint(username: str = Form(...), education: str = Form(...)):
    education_list = [edu.strip() for edu in education.split(",") if edu.strip()]
    if not education_list:
        raise HTTPException(status_code=400, detail="No valid education provided")
    success = delete_education(username, education_list)
    if success != -1:
        updated_education = get_education(username)
        return {"message": "Education deleted successfully", "education": updated_education}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete education")


# Learning style
@app.get("/get_learning_styles")
def get_learning_styles_endpoint(username: str):
    styles = get_learning_styles(username)
    if styles is not None:
        return {"learning_styles": styles}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/add_learning_styles")
def add_learning_styles_endpoint(username: str = Form(...), learning_styles: str = Form(...)):
    style_list = [style.strip() for style in learning_styles.split(",") if style.strip()]
    if not style_list:
        raise HTTPException(status_code=400, detail="No valid learning styles provided")
    success = add_learning_style(username, style_list)
    if success != -1:
        updated_styles = get_learning_styles(username)
        return {"message": "Learning styles added successfully", "learning_styles": updated_styles}
    else:
        raise HTTPException(status_code=400, detail="Failed to add learning styles")

@app.post("/delete_learning_styles")
def delete_learning_styles_endpoint(username: str = Form(...), learning_styles: str = Form(...)):
    style_list = [style.strip() for style in learning_styles.split(",") if style.strip()]
    if not style_list:
        raise HTTPException(status_code=400, detail="No valid learning styles provided")
    success = delete_learning_style(username, style_list)
    if success != -1:
        updated_styles = get_learning_styles(username)
        return {"message": "Learning styles deleted successfully", "learning_styles": updated_styles}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete learning styles")


# Roadmap

@app.websocket("/generate_roadmap")
async def generate_roadmap_endpoint(websocket: WebSocket):
    roadmap = {}
    await websocket.accept()
    try:
        username = await websocket.receive_text()
        role = await websocket.receive_text()
        company = await websocket.receive_text()

        chunk_stream = generate_user_roadmap(username, role, company)
        
        for step in extract_json_steps(chunk_stream):
            roadmap.update(step)
            await websocket.send_json(step)
        
        await websocket.send_json({"status": "completed"})
    
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    
    finally:
        await websocket.close()

    if roadmap:
        add_user_roadmap(username, role, company, roadmap)


@app.websocket("/generate_submap")
async def generate_roadmap_endpoint(websocket: WebSocket):
    submap = {}
    await websocket.accept()
    try:
        username = await websocket.receive_text()
        substep_name = await websocket.receive_text()
        substep_description = await websocket.receive_text()
        prerequisites = await websocket.receive_text()
        role = await websocket.receive_text()
        company = await websocket.receive_text()
        coordinates = json.loads(await websocket.receive_text())

        chunk_stream = generate_substep_branch(username, substep_name, substep_description, prerequisites, role, company)
        
        for step in extract_json_steps(chunk_stream):
            submap.update(step)
            await websocket.send_json(step)
        
        
        await websocket.send_json({"status": "completed"})
    
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    
    finally:
        await websocket.close()

    if submap:
        merge_substep_to_main(username, f"{role}+{company}", submap, coordinates)
    
    
@app.get("/roadmap")
def roadmap_endpoint(username: str, role: str, company: str):
    roadmap = get_user_roadmap(username, role, company)
    if roadmap:
        return {"username": username, "role": role, "company": company, "roadmap": roadmap}
    else:
        raise HTTPException(status_code=404, detail="User or roadmap not found")

@app.post("/update_roadmap")
def update_roadmap_endpoint(username: str = Form(...), role: str = Form(...), company: str = Form(...)):
    status = update_user_roadmap(username, role, company)
    if status:
        return {"message": "Roadmap updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="User or roadmap not found")

@app.post("/delete_roadmap")
def delete_roadmap_endpoint(username: str = Form(...), role: str = Form(...), company: str = Form(...)):
    delete_user_roadmap(username, role, company)
    return {"message": "Roadmap deleted successfully"}

@app.get("/list_roadmaps")
def list_roadmaps_endpoint(username: str):
    user_roadmaps = list_user_roadmaps(username)
    if user_roadmaps is not None:
        return {"roadmaps": user_roadmaps}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/test")
def mudit_test():
    roadmap = get_user_roadmap("mudit.7.gupta+github@gmail.com", "Intern", "Google")
    if roadmap:
        return {"roadmap": roadmap["roadmap"]}
    else:
        raise HTTPException(status_code=404, detail="User or roadmap not found")


# Deprecated
@app.get("/search")
def search_endpoint(q: str = ""):
    return skill_search(q)
