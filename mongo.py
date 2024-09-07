from pymongo import MongoClient
import os
from bson import json_util
import json
from roadmap import generate_content, generate_substep


client = MongoClient("mongodb+srv://admin:xN5eoW33cQFjFnid@roadmap.ykhw9zp.mongodb.net/?retryWrites=true&w=majority&appName=roadmap")
database = client["automap"]
users = database["Users"]
skills = database["Skills"]
roadmaps = database["Roadmaps"]

try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB")
except Exception as e:
    print(f"Couldn't connect to MongoDB: {e}")


def create_account_from_email(email):
    if users.find_one({"username": email}):
        print("Account already exists")
        return -1

    result = users.insert_one(
        {
            "username": email,
            "skills": [],
            "education" : [],
            "experience" : [],
            "learning_styles" : [],
            "roadmap": {},
            "points" : 0,
            "friends" : [],
            "linkedin" : ""
        }
    )

    if result.acknowledged:
        print(f"Account created successfully for {email}")
        return 1
    else:
        print("Failed to create account")
        return -1



# Leaderboard

def get_users_sorted(username):
    try:
        sorted_users = list(users.find().sort("points", -1))
        user_position = next((index for index, user in enumerate(sorted_users) if user["username"] == username), None)
        user_data = []
        for user in sorted_users:
            user_info = {
                "username": user["username"],
                "points": user["points"]
            }
            user_data.append(user_info)
        if user_position is not None:
            return user_position + 1, user_data
        else:
            print(f"Username '{username}' not found in the leaderboard.")
            return None, user_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, []
    

def get_friends_sorted(username):
    try:
        sorted_users = list(users.find().sort("points", -1))
        user_position = next((index for index, user in enumerate(sorted_users) if user["username"] == username), None)
        
        if user_position is None:
            print(f"Username '{username}' not found in the leaderboard.")
            return None
        
        user_stats = get_stats(username)
        if user_stats == -1:
            return None
        
        friends = get_friends(username)
        if friends == -1:
            return None
        
        result = {
            "user": {
                "username": username,
                "position": user_position + 1,
                "points": sorted_users[user_position]["points"],
                "stats": user_stats
            },
            "friends": []
        }
        
        for friend_username in friends:
            friend_position = next((index for index, user in enumerate(sorted_users) if user["username"] == friend_username), None)
            friend_stats = get_stats(friend_username)
            
            if friend_position is not None and friend_stats != -1:
                result["friends"].append({
                    "username": friend_username,
                    "position": friend_position + 1,
                    "points": sorted_users[friend_position]["points"],
                    "stats": friend_stats
                })
        
        return result
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def get_stats(username):
    user = users.find_one({"username": username})
    
    if not user:
        print(f"User {username} not found")
        return -1

    total_beginner = 0
    total_intermediate = 0
    total_advanced = 0
    
    for roadmap_key, roadmap_data in user.get("roadmap", {}).items():
        metrics = roadmap_data.get("metrics", {})
        total_beginner += metrics.get("Beginner", 0)
        total_intermediate += metrics.get("Intermediate", 0)
        total_advanced += metrics.get("Advanced", 0)

    result = {
        "Beginner": total_beginner,
        "Intermediate": total_intermediate,
        "Advanced": total_advanced
    }

    return result
    
# Linkedin
def get_linkedin_recommendations(username: str):
    user = users.find_one({"username": username})
    if not user:
        return None

    user_roadmap_types = set()
    for roadmap_data in user.get("roadmap", {}).values():
        user_roadmap_types.add(roadmap_data.get("roadmap_type"))

    recommendations = []
    
    for other_user in users.find():
        other_user_roadmap_types = set()
        for roadmap_data in other_user.get("roadmap", {}).values():
            other_user_roadmap_types.add(roadmap_data.get("roadmap_type"))
        
        if user_roadmap_types.intersection(other_user_roadmap_types):
            recommendations.append({
                "user": other_user.get("username"),
                "linkedin": other_user.get("linkedin")
            })

    return recommendations

def delete_linkedin_profile(username: str):
    result = users.update_one(
        {"username": username},
        {"$unset": {"linkedin": ""}}
    )
    return result.matched_count > 0

def add_linkedin_profile(username: str, linkedin_url: str):
    result = users.update_one(
        {"username": username},
        {"$set": {"linkedin": linkedin_url}}
    )
    return result.matched_count > 0

# Friends
def add_friend(username, friend_username):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    friend = users.find_one({"username": friend_username})
    if not friend:
        print(f"Friend {friend_username} not found")
        return -1

    if friend_username in user.get("friends", []):
        print(f"{friend_username} is already a friend of {username}")
        return 0

    result = users.update_one(
        {"username": username},
        {"$push": {"friends": friend_username}}
    )

    if result.modified_count == 1:
        print(f"{friend_username} added as a friend to {username}")
        return 1
    else:
        print(f"Failed to add {friend_username} as a friend to {username}")
        return -1

def get_friends(username):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    friends = user.get("friends", [])
    return friends
    
def remove_friend(username, friend_username):
    user = users.find_one({"username": username})
    
    if not user:
        print(f"User {username} not found")
        return -1

    if friend_username not in user.get("friends", []):
        print(f"{friend_username} is not a friend of {username}")
        return 0

    result = users.update_one(
        {"username": username},
        {"$pull": {"friends": friend_username}}
    )

    if result.modified_count == 1:
        print(f"{friend_username} removed as a friend of {username}")
        return 1
    else:
        print(f"Failed to remove {friend_username} as a friend of {username}")
        return -1



# skills
def delete_skills(username, skills_list):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_skills = [skill for skill in user.get("skills", []) if skill not in skills_list]
    users.update_one(
        {"username": username},
        {"$set": {"skills": updated_skills}}
    )

    print(f"Skills deleted for {username}")
    return 1

def add_skills(username, new_skills):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_skills = list(set(user.get("skills", []) + new_skills))
    users.update_one(
        {"username": username},
        {"$set": {"skills": updated_skills}}
    )

    print(f"Skills updated for {username}")
    return 1

def get_skills(username: str):
    user = users.find_one({"username": username})
    if user:
        return user.get("skills", [])
    return []

# Education 
def delete_education(username, education_list):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_education = [edu for edu in user.get("education", []) if edu not in education_list]
    users.update_one(
        {"username": username},
        {"$set": {"education": updated_education}}
    )

    print(f"Education deleted for {username}")
    return 1

def add_education(username, new_education):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_education = list(set(user.get("education", []) + new_education))
    users.update_one(
        {"username": username},
        {"$set": {"education": updated_education}}
    )

    print(f"Education updated for {username}")
    return 1

def get_education(username: str):
    user = users.find_one({"username": username})
    if user:
        return user.get("education", [])
    return []

# Experience
def delete_experience(username, experience_list):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_experience = [exp for exp in user.get("experience", []) if exp not in experience_list]
    users.update_one(
        {"username": username},
        {"$set": {"experience": updated_experience}}
    )

    print(f"Experience deleted for {username}")
    return 1

def add_experience(username, new_experience):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_experience = list(set(user.get("experience", []) + new_experience))
    users.update_one(
        {"username": username},
        {"$set": {"experience": updated_experience}}
    )

    print(f"Experience updated for {username}")
    return 1

def get_experience(username: str):
    user = users.find_one({"username": username})
    if user:
        return user.get("experience", [])
    return []

# Learning style

def delete_learning_style(username, learning_style_list):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_learning_styles = [style for style in user.get("learning_styles", []) if style not in learning_style_list]
    users.update_one(
        {"username": username},
        {"$set": {"learning_styles": updated_learning_styles}}
    )

    print(f"Learning styles deleted for {username}")
    return 1


def add_learning_style(username, new_learning_styles):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return -1

    updated_learning_styles = list(set(user.get("learning_styles", []) + new_learning_styles))
    users.update_one(
        {"username": username},
        {"$set": {"learning_styles": updated_learning_styles}}
    )

    print(f"Learning styles updated for {username}")
    return 1

def get_learning_styles(username: str):
    user = users.find_one({"username": username})
    if user:
        return user.get("learning_styles", [])
    return []
    
# Roadmap

def generate_user_roadmap(username, role, company):
    user = users.find_one({"username": username})
    if not user:
        return None

    skills = user.get("skills", [])
    education = user.get("education", "Not Provided")
    experience = user.get("experience", "NA")
    timeline = user.get("timeline", "As needed")
    learning_style = user.get("learning_style", "self-paced") 

    return(generate_content(skills, education, experience, role, company, timeline, learning_style))


def generate_substep_branch(username, substep_name, substep_description, prerequisites, role, company):
    user = users.find_one({"username": username})
    if not user:
        return None
    learning_style = user.get("learning_style", "self-paced") 

    return(generate_substep(substep_name, substep_description, prerequisites, learning_style, role, company))

def merge_substep_to_main(username, roadmap_key, substep_map, coordinates):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return
    roadmap = user.get("roadmap", {}).get(roadmap_key, {})
    if not roadmap:
        print(f"Roadmap {roadmap_key} not found for user {username}")
        return

    current_step = roadmap["roadmap"]
    for i, coord in enumerate(coordinates):
        if isinstance(current_step, dict):
            if str(coord) not in current_step:
                print(f"Step {coord} not found in roadmap")
                return
            
            if i < 2:
                if i == 0:
                    current_step = current_step[str(coord)]["Sub_steps"]
                else:
                    last_step = current_step[str(coord)]
                    current_step = current_step[str(coord)]["Substep_roadmap"]
            else:
                last_step = current_step[str(coord)]
                current_step = current_step[str(coord)]["Substep_roadmap"]

        elif isinstance(current_step, list):
            if coord < 1 or coord > len(current_step):
                print(f"Step {coord} is out of range")
                return
            last_step = current_step[coord - 1]
            current_step = current_step[coord - 1]["Substep_roadmap"]
        else:
            print(f"Unexpected data structure at coordinate {i}")
            return

    last_step["Substep_roadmap"] = substep_map

    metrics = roadmap.get("metrics", {"Problems": {}, "Completed": {}})
    for step in substep_map:
        difficulty = substep_map[step]["Difficulty"]
        if difficulty not in metrics["Problems"]:
            metrics["Problems"][difficulty] = 0
            metrics["Completed"][difficulty] = 0
        metrics["Problems"][difficulty] += 1

    roadmap_data = {
        f"roadmap.{roadmap_key}": {
            "roadmap": roadmap["roadmap"],
            "metrics": metrics
        }
    }
    users.update_one({"username": username}, {"$set": roadmap_data})
    return 1

def add_user_roadmap(username, role, company, roadmap):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return

    roadmap_key = f"{role}+{company}"
    metrics = {"Problems": {}, "Completed": {}}

    for step in roadmap:
        roadmap_type = roadmap[step]["roadmap_type"]
        difficulty = roadmap[step]["Difficulty"]
        if difficulty not in metrics["Problems"]:
            metrics["Problems"][difficulty] = 0
            metrics["Completed"][difficulty] = 0
        metrics["Problems"][difficulty] += 1


    roadmap_data = {
        f"roadmap.{roadmap_key}": {
            "roadmap": roadmap,
            "metrics": metrics,
            "roadmap_type" : roadmap_type
        }
    }

    users.update_one({"username": username}, {"$set": roadmap_data})

def update_user_roadmap(username, roadmap_key, coordinates):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return
    roadmap = user.get("roadmap", {}).get(roadmap_key, {})
    if not roadmap:
        print(f"Roadmap {roadmap_key} not found for user {username}")
        return

    current_step = roadmap["roadmap"]
    for i, coord in enumerate(coordinates):
        if isinstance(current_step, dict):
            if str(coord) not in current_step:
                print(f"Step {coord} not found in roadmap")
                return

            if i < 2:
                if i == 0:
                    current_step = current_step[str(coord)]["Sub_steps"]
                else:
                    last_step = current_step[str(coord)]
                    current_step = current_step[str(coord)]["Substep_roadmap"]
            else:
                last_step = current_step[str(coord)]
                current_step = current_step[str(coord)]["Substep_roadmap"]

        elif isinstance(current_step, list):
            if coord < 1 or coord > len(current_step):
                print(f"Step {coord} is out of range")
                return
            last_step = current_step[coord - 1]
            current_step = current_step[coord - 1]["Substep_roadmap"]
        else:
            print(f"Unexpected data structure at coordinate {i}")
            return

    difficulty = last_step.get("Difficulty")
    metrics = roadmap.get("metrics", {"Problems": {}, "Completed": {}})
    last_step["status"] = "Complete"
    metrics["Completed"][difficulty] = metrics["Completed"].get(difficulty, 0) + 1

    if difficulty == "Beginner":
        users.update_one({"username": username}, {"$inc": {"points": 10}})
    elif difficulty == "Intermediate":
        users.update_one({"username": username}, {"$inc": {"points": 30}})
    elif difficulty == "Advanced":
        users.update_one({"username": username}, {"$inc": {"points": 50}})

    roadmap_data = {
        f"roadmap.{roadmap_key}": {
            "roadmap": roadmap["roadmap"],
            "metrics": metrics
        }
    }
    users.update_one({"username": username}, {"$set": roadmap_data})
    return 1

def get_user_roadmap(username, role, company):
    user = users.find_one({"username": username})
    if user:
        roadmap_key = f"{role}+{company}"
        if roadmap_key in user.get("roadmap", {}):
            return user["roadmap"][roadmap_key]
    return None

def delete_user_roadmap(username, role, company):
    user = users.find_one({"username": username})
    if not user:
        print(f"User {username} not found")
        return

    roadmap_key = f"{role}+{company}"

    if roadmap_key in user.get("roadmap", {}):
        users.update_one({"username": username}, {"$unset": {f"roadmap.{roadmap_key}": ""}})
        print(f"Roadmap {roadmap_key} deleted successfully")
    else:
        print(f"Roadmap {roadmap_key} not found in user data")

def list_user_roadmaps(username: str):
    user = users.find_one({"username": username})
    if user:
        roadmaps = {}
        for roadmap_key in user.get("roadmap", {}):
            roadmap_data = user["roadmap"][roadmap_key]
            roadmaps[roadmap_key] = {
                "roadmap": roadmap_key,
                "metrics": roadmap_data["metrics"]
            }
        return roadmaps
    else:
        return None
    
# Deprecated
def skill_search(q: str):
    res = skills.aggregate(
        [
            {
                "$search": {
                    "index": "Skill-search",
                    "text": {
                        "path": "Name",
                        "query": f"{q}",
                        "fuzzy": {
                            "maxEdits": 2,
                            "maxExpansions": 100,
                        },
                    },
                }
            }
        ]
    )
    
    return json.loads(json_util.dumps(res))
