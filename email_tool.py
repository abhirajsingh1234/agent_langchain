import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from email.mime.text import MIMEText
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import dotenv

emails = {'rajpurohitabhirajsinghvyasch@gmail.com':'owner of this email id is Abhiraj singh rajpurohit',
    'karanshelar8775@gmail.com':'owner of this email id is Karan Shelar',
    'siddhantparulekar5@gmail.com':'owner of this email id is Siddhant Parulekar',
    'dimplerajpurohit203040@gmail.com':'owner of this email id is Dimple Rajpurohit'}

def send_emails(recipient, subject, body):
    
    dotenv.load_dotenv()
    smtp_server = "smtp.gmail.com"
    port = 587  # TLS port
    sender_email = "rajpurohitabhirajsingh@gmail.com"         # Replace with your email
    password = os.getenv("MAIL_ID_PASSWORD")                  # Replace with your app password (if using Gmail, set up 2FA and generate an app password)
    receiver_email = recipient
    subject = subject
    body = body
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()           
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

    return f"email was sent by {sender_email} to {receiver_email} and  subject was {subject}, body was {body}"



def send_email_tool(query):
    emails = {'rajpurohitabhirajsinghvyasch@gmail.com':'owner of this email id is Abhiraj singh rajpurohit',
    'karanshelar8775@gmail.com':'owner of this email id is Karan Shelar',
    'siddhantparulekar5@gmail.com':'owner of this email id is Siddhant Parulekar',
    'dimplerajpurohit203040@gmail.com':'owner of this email id is Dimple Rajpurohit'}


    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=os.getenv('GEMINI_API_KEY'),temperature=0,max_output_tokens=300)
    parser = JsonOutputParser()

    template = PromptTemplate(
        input_variables=["query","emails"],
        template="""
                    Given the input {query} and available emails, construct an appropriate email.
                                1 Email Data Handling:
                                - The available {emails} are provided in dictionary format:
                                "email_id": "owner's name"
                                - If the recipient's email is missing in the query, search for a matching name in available emails and retrieve the corresponding email ID.
                                - If recipient's email is not found in available emails too, find the relevant email id from chat history.

                                2 Extracting Email Content:
                                - Identify the email subject and body from the user query.
                                - The email subject and body must accurately resolve the user’s query.
                                -if body is present but subject is missing, generate a subject on basis of body.

                                3 Formatting the Email Body:
                                - Always end the email body with:
                                "Written by Jarvis on command of (user’s actual name)."
                                - Extract the user’s actual name from chat history.(if not found then bydefault use 'abhiraj's custom-MCP')

                                4 Expected JSON Output Format:
                                {{
                                    "email_id": "recipient's email or null",
                                    "subject": "Generated subject ",
                                    "body": "Generated body ending with 'Written by private Agent"
                                }}
                                5 Handling Missing Data:
                                - If any required parameters (email_id or body) are missing, return null for those values instead of generating incorrect data.
                                """
    )
    prompt = template | llm | parser 

    result = prompt.invoke({"query": query, "emails": emails})
    print("\nresult:\n", result)
    print("\nresult type:\n", type(result))
    result = send_emails(result['email_id'], result['subject'], result['body'])
    return result
    
       
    