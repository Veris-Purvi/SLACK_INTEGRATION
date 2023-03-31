import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import json
from flask import Flask,request
import openai
from dotenv import load_dotenv
import pymongo
import smtplib
import datetime
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pytz
import time

load_dotenv()
openai.api_key = os.environ['OPENAI_KEY']
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])


flask_app=Flask(__name__)
app = App(token=os.environ['SLACK_BOT_TOKEN'])
AUTHORIZED_USERS=[]



def validate_date(date_str):
        # Check if date is in the format DD/MM/YY and is valid
        try:
            
            datetime.datetime.strptime(date_str, '%d/%m/%Y')
            
        except ValueError:
        
            return "Date is not valid. Please enter a valid future date in the format DD/MM/YYYY."
        date=datetime.datetime.strptime(date_str, '%d/%m/%Y')
        
        if date < datetime.datetime.now():
            return "Date is not valid. Please enter a valid future date in the format DD/MM/YYYY."
        return None

def validate_venue(venue_str, valid_venues):
    
    first_words = [name.replace('(VMS)','').strip() for name in valid_venues]
    
    if venue_str not in first_words:
        
        venues_list = '\n'.join(first_words)
        return f"Venue is not valid. Please select only from the following venues:\n{venues_list}"
    else:
        return None

def validate_date_and_venue(date_str, venue_str, valid_venues):
    
    date_error = validate_date(date_str)
    venue_error = validate_venue(venue_str, valid_venues)
    
    if date_error:
        return date_error
    elif venue_error:
        return venue_error
    else:
        return None

def fetch_api_val(org_name, user_name, data):
    myToken = '35e93961c4b75a4543de5a78186802eaf10eb6d4'
   

    #url = "http://localhost:8000/"
    url = "https://lbenz.veris.in/"

    username = user_name

    headers = {"Authorization": 'token {}'.format(myToken), "Content-Type": "application/json"}
    venue_params = {'q': username}

    orgId = 8
    venues = requests.get(f"{url}api/v2/organisation/{orgId}/venues/", headers = headers)
    venues_data = json.loads(venues.content)
    

    venue_names = [n['name'] for n in venues_data['results']]
    # venues_list = '\n'.join(venue_names)
    validation_ans=validate_date_and_venue(str(data['date']), str(data['venue']), venue_names)
    if(validation_ans):
        return validation_ans

    venue_id = [n['_id'] for n in venues_data['results'] if data['venue'] in n['name']][0]
    

    hosts = requests.get(f"{url}/api/v4/organization/{orgId}/venue/{venue_id}/valid-hosts/",
                          headers= headers, params= venue_params)


    hosts_data = json.loads(hosts.content)

    host_id = [n['contact_id'] for n in hosts_data['results'] if data['name'] in n['name']][0]

    valid_from_obj = datetime.datetime.strptime(f"{data['date']} {data['start_time']}", '%d/%m/%Y %H:%M:%S')
    if not data['end_time']:
        valid_till_obj = valid_from_obj + datetime.timedelta(hours=2)
    else:
        valid_till_obj=datetime.datetime.strptime(f"{data['date']} {data['end_time']}", '%d/%m/%Y %H:%M:%S')
   

    # Convert to UTC
    local_tz = pytz.timezone('Asia/Kolkata')  # Replace with India Standard Time
    utc_tz = pytz.timezone('UTC')
    local_start_datetime = local_tz.localize(valid_from_obj)
    utc_start_datetime = local_start_datetime.astimezone(utc_tz)
    valid_from_utc = utc_start_datetime

    if(data['end_time']):
        local_end_datetime=local_tz.localize(valid_till_obj)
        utc_end_datetime=local_end_datetime.astimezone(utc_tz)
        valid_till_utc=utc_end_datetime
    else:
        valid_till_utc = valid_from_utc + datetime.timedelta(hours=2)

    valid_from_str = valid_from_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    valid_till_str = valid_till_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
   
    payload = {
        "host": host_id,
        "venue": venue_id,
        "valid_from": valid_from_str,
        "valid_till": valid_till_str,
        "extra_instructions": "test",
        "do_not_notify_host": False,
        "do_not_notify_guest": False,
        "is_hierarchy_invite": False,
        "hierarchy_invites_detail": {
            "request_access": ["mobile"]
            },
        "guest": {
            "first_name" : data['name'],
            "last_name" : 'Sharma',
            "contacts": {"email" : data['contact']}
        },
        "meta": {
            "invite": "test"
        },
        "workflows": {
            "workflow_id": {},
            "workflow_data": {}
        }
    }

    try:
        response = requests.post(f"{url}/api/v4/organization/{orgId}/create-generic-invite/", 
                                 headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            
            return None
        else:
            return response.text
    except requests.exceptions.HTTPError as e:
            return e
# create-invite request : Please schedule my meet with Ms Anusha in test on 23/23/2023 at 13:30:30 on her email id  anusha.shet@veris.in

def user_info(user_id):
    url = "https://slack.com/api/users.info"
    params = {
    "token": os.environ['SLACK_BOT_TOKEN'],
    "user": user_id
    }
    response = requests.post(url, data=params)
    json_response = json.loads(response.text)
    
    email1 = json_response["user"]["profile"]["email"]
    username = json_response["user"]["profile"]["first_name"]
    return username, email1

def send_otp(receiver_email):
    
    send_otp_url = 'https://local.veris.in/api/v4/validate-member-contact/'
    send_otp_payload = {
        "contact": receiver_email
        
    }
    requests.post(send_otp_url, json=send_otp_payload)
    return

def verify_otp(user_input,receiver_email):
    verify_otp_url = 'https://local.veris.in/api/v4/verify-member-otp/'
    verify_otp_payload = {
        "contact": receiver_email,
        "otp": int(user_input)
    }
    verify_otp_response = requests.post(verify_otp_url, json=verify_otp_payload)
    if verify_otp_response.status_code==200:
        # str_otp_response=(verify_otp_response.json())
        return True
    else:
        return False
    
def wait_for_new_message(channel_id,thread_ts):
    url="https://slack.com/api/conversations.replies"
    data={"channel_id": channel_id,"thread_ts":thread_ts}
    json_data = json.dumps(data),
    headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"
    }
    response=requests.get(url, data=json_data,headers=headers)
    return response.text


def post(message, channel_id,thread_ts=None):
    url = "http://d65a-2401-4900-1c2a-6dc0-1038-49d2-1e70-a765.ngrok.io/post_message"
    data = {"message": message, "channel_id": channel_id,"thread_ts":thread_ts}
    json_data = json.dumps(data)
    headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning":"False"
    }

    response = requests.post(url, data=json_data,headers=headers)
    return response.text

    
@flask_app.route("/post_message", methods=["POST"])
def post_message():
    # Get the message text and channel ID from the request data
    print("Hii")
    message = request.get_json()["message"]
    channel_id = request.get_json()["channel_id"]
    thread_ts=request.get_json()["thread_ts"]

    # Construct the request data
    data = {
        "channel": channel_id,
        "text": message,
        "thread_ts":thread_ts,
        
    }

    # Set the headers for the request
    headers = {
        
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}",
        "Retry-After": "5"
    }

    # Send the POST request to the Slack API
    
    response = requests.post("https://slack.com/api/chat.postMessage", data=json.dumps(data), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        
        return response.text
    else:
        return ({"success": False, "error": response.text})

last_message = {}
@flask_app.route('/slack/events', methods=['POST'])
def handle_message():
    request_data = request.get_json()
    print("Hii")
    # Check if this is a Slack event
    # if(request_data.get("type")=="url_verification"):
    #     return
    if 'challenge' in request_data:
        # Return the challenge parameter as plain text
        return request_data['challenge']
    if request_data.get("type") == "event_callback":
        event_data = request_data["event"]
        if event_data.get("type") == "message" and not event_data.get("bot_id") and not event_data.get("thread_ts"):
            
            channel_id = event_data["channel"]
            message_ts = event_data["ts"]
            text = event_data["text"]
            user_id=event_data["user"]
            org_name = client.auth_test()['team']
            thread_ts = event_data["ts"]
           


            if event_data.get('bot_id') is None and "text" in event_data and event_data.get("ts") != last_message.get(channel_id) and (not bool(last_message) or event_data.get("ts")>last_message.get(channel_id)):
                last_message[channel_id] = event_data.get("ts")
                flag=False
                try: 
                    if event_data.get('bot_id') is None and ("hello" in text.lower() or "hi" in text.lower()):
                        message=("Hello! Let's get started to schedule meetings with ease")
                        post(message,channel_id, thread_ts)
                        flag=True
                        
                    

                    else:
                        words_to_check = ['schedule', 'fix', 'meet', 'meeting']
                        username, user_email = user_info(user_id)
                        for word in words_to_check: 
                            if word in text.lower():
                                flag=True
                                if user_id in AUTHORIZED_USERS:
                                    ans=(resp(text))   
                                    try:
                                        trial_ans=fetch_api_val(org_name = org_name, user_name = username, data= ans)
                                        if(trial_ans):
                                            message=(trial_ans)
                                            post(message,channel_id,thread_ts)
                                        else:
                                            message=("Meet scheduled successfully")
                                            post(message,channel_id,thread_ts)
                                    except Exception as e:
                                        return
                                    
                                    break

                                else:
                                    neccessary_word="gmail.com"
                                    if neccessary_word in user_email:
                                        send_otp(user_email)
                                        message=("Please enter the OTP sent to your mail")
                                        response=post(message,channel_id,thread_ts)
                                        data = json.loads(response)
                                        new_ts = data["ts"]
                
                                    
                                        user_input=""
                                        while True:
                                            
                                            time.sleep(5)
                                            result = client.conversations_replies(
                                            channel=channel_id,
                                            ts=thread_ts
                                            )
                                        
                                            # Get the latest message in the thread
                                            new_message = result['messages'][-1]

                                            # Check if the latest message is from the user and contains the OTP
                                            if new_message['user'] == user_id:
                                                user_input=new_message['text']
                                                break
                                        
                                        if (verify_otp(user_input,user_email)==True):
                                            AUTHORIZED_USERS.append(user_id)
                                            ans=resp(text)
                                            message=("OTP verified successfully, I'll schedule your meet ")
                                            post(message,channel_id,thread_ts)
                                            ans=(resp(text))   
                                            
                                            try:
                                                temp_ans=fetch_api_val(org_name = org_name, user_name = username, data= ans)
                                                
                                                if(temp_ans):
                                                    message=(temp_ans)
                                                    post(message,channel_id,thread_ts)
                                                    return
                                                else:
                                                    message=("Meet scheduled successfully")
                                                    post(message,channel_id,thread_ts)
                                            except Exception as e:
                                                return
                                        else:
                                            message=('Invalid OTP. Please try again.')
                                            post(message,channel_id, thread_ts)
                                            return
                                        break
                                    else:
                                        message=(f"Sorry <@{user_id}>, you do not have permission to send invites.")
                                        post(message,channel_id,thread_ts)
                                        return
                                break
                    if(flag==False):
                        message=("Sorry, I don't understand")
                        post(message,channel_id,thread_ts)
                        return
                    
                except Exception as e:
                    print(e)
                    message=("Sorry, I don't understand")
                    post(message,channel_id)
                    return ""
    return ""
                    



def resp(Text):
    prompt = f"""Return the email id or any other means of contact, venue, time, date, name of the person in the text below. If any of the string is empty(email id or any other means of contact, venue, time, date, name of the person), ask for it like venue is missing and then return. Return the result in python dictionary format having the keys : \\"contact\\",\\"venue\\",\\"start_time\\",\\"end_time\\"\\"date\\",\\"name\\". Time should be interpreted and changed to 24-hour format like 11 PM should be converted to 23:00:00 and date should be converted to format DD/MM/YYYY.Don't change the date even if it is invalid. Its format should be like-
    Answer:'{{
    "contact":8797987,
    "venue": "Delhi",
    "start_time": "23:00:00",
    "end_time": "23:30:00",
    "date": "23/03/2023",
    "name" : "Sunil"
    }}'
    
    Text:
    {Text}
    """
    try:
        engine = 'text-davinci-003'

        response = openai.Completion.create(
                engine=engine, 
                prompt=prompt,
                temperature=0.3,
                max_tokens=140,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=1
        )

        choices = response.choices[0]
        text = choices.text.strip()
        text = text.replace(":", "=", 1)
        text = text.split("=")[1].strip()
        d = text.maketrans("'",'"')
        text = text.translate(d)
        result = json.loads(text)
        

        contact = result['contact']
        venue = result['venue']
        start_time = result['start_time']
        end_time = result['end_time']
        date = result['date']
        name = result['name']

        # Check for missing details
        missing_details = []
        if not contact:
            missing_details.append("contact")
        if not venue:
            missing_details.append("venue")
        if not start_time :
            missing_details.append("time")
        if not date:
            missing_details.append("date")

        if missing_details:
            # Ask for missing details
            response_text = f"The following details are missing: {', '.join(missing_details)}. Please provide them."
            
            return response_text

        # If all details are present, store in the database
        data = {
            'contact': contact,
            'venue': venue,
            'start_time': start_time,
            'end_time':end_time,
            'date': date,
            'name': name
        }
        # collection.insert_one(data)
        return data

    except Exception as e:
        print(e)
        return {"msg": e,"status":"error"}




# Start your app
if __name__ == "__main__":

    flask_app.run(debug=True,port=5000)
    

