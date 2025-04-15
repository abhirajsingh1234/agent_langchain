from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import urllib.parse
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser


load_dotenv()

def send_whatsapp_message( phone_number, message,country_code="91", headless=True):
    driver = None
    try:
        profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        os.makedirs(profile_dir, exist_ok=True)
        if len(phone_number) != 10:
            return 'context: tell user to provide a valid phone number'
        full_phone = f"{country_code}{phone_number}"
        encoded_message = urllib.parse.quote(message)
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Common options to make Chrome more stable
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")
        
        # Path to store user data to maintain login sessions
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Service object to configure the driver
        service = Service()
        
        print("Starting Chrome browser...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Use direct WhatsApp API URL to open chat
        wa_url = f"https://web.whatsapp.com/send?phone={full_phone}&text={encoded_message}"
        print(f"Opening WhatsApp Web for {full_phone}...")
        driver.get(wa_url)
        
        # First check if we need to scan QR code
        try:
            # Check if QR code is present (session expired)
            qr_code_wait = WebDriverWait(driver, 5)
            qr_code = qr_code_wait.until(
                EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
            )
            
            if headless:
                print("\n*** SESSION EXPIRED - QR CODE NEEDS SCANNING ***")
                print("Please run the script again with headless=False to scan the QR code.")
                print("Example: send_whatsapp_message(country_code, phone_number, message, headless=False)")
                driver.quit()
                return False
            else:
                print("\nPlease scan the QR code with your WhatsApp app.")
                print("Waiting for scan...")
                # Wait longer for user to scan QR code
                WebDriverWait(driver, 120).until(
                    EC.invisibility_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
                )
                print("QR code scanned successfully!")
        except TimeoutException:
            # QR code not found, session is likely active
            pass
        
        # Now wait for the send button to appear
        print("Waiting for WhatsApp Web to load...")
        send_button_xpath = '//span[@data-icon="send"]'
        wait = WebDriverWait(driver, 60)
        send_button = wait.until(EC.element_to_be_clickable((By.XPATH, send_button_xpath)))
        
        # Click send button
        time.sleep(2)  # Small delay to ensure everything is ready
        send_button.click()
        print("Message sent successfully!")
        
        # Wait a bit before closing to ensure message is sent
        time.sleep(3)
        driver.quit()
        return True

        
    except TimeoutException:
        if headless:
            print("\n*** SESSION MAY HAVE EXPIRED ***")
            print("Failed to load WhatsApp Web or send button not found.")
            print("Please run the script again with headless=False to check if you need to scan the QR code.")
            print("Example: send_whatsapp_message(country_code, phone_number, message, headless=False)")
        else:
            print("\nFailed to load WhatsApp Web or send button not found.")
            print("Please check your internet connection and try again.")
        
        if driver:
            driver.quit()
        return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        return False


def send_whatsapp_message_tool(query):
    available_numbers = {'8450995752':'Abhiraj singh rajpurohit',
                        '8828296303':'karan shelar',
                        '7620967264':'dimple rajpurohit',
                        '8094935507':'ishwar singh rajpurohit'}
    chat_history=[]
    parser = JsonOutputParser()
    model = ChatGoogleGenerativeAI(model='gemini-1.5-pro', api_key=os.getenv('GEMINI_API_KEY'),temperature=0,max_output_tokens=40)
    template = PromptTemplate(
        input_variables=["question","available_numbers","chat_history"],
        template="""
                               Analyze the input {question} to determine if the user is requesting to send a WhatsApp message.

                                Guidelines:
                                1. First check if a phone number is explicitly provided in the query
                                2. If no phone number is found:
                                   - Extract any person/contact name mentioned in the query
                                   - Search the {available_numbers}  for matching names
                                   - Use the corresponding number if a name match is found

                                3. Extracting Message Content:
                                    - Identify the message content from the user query.
                                    - If message is missing, search the {chat_history} for relevant details.
                                    - The message must accurately resolve the user’s query.

                                4. If either phone_number (direct or via name lookup) or message is not found:
                                   - Set send_whatsapp_message to false
                                   - Set the missing parameter(s) to null
                                5. Always use "send_whatsapp_message" as the tool value
                                6. if no message is found, set message to '..'

                                Return JSON response in this format:
                                {{
                                    "phone_number": string,  // extracted phone number, number from name lookup, or null if not found
                                    "message": string        // extracted message content or null if not found
                                }}
                                """
    )


    chain = template | model | parser
    response=chain.invoke({
        "question": query,
        "available_numbers": available_numbers,
        "chat_history": chat_history
    })
    print(response)
    try:
        response = send_whatsapp_message(response['phone_number'], response['message'])
        if response:
            return f"whatsapp message was sent successfully!"
        else:
            return {"error": f"ERROR OCCURED WHILE SENDING WHATSAPP MESSAGE, TRY AGAIN"}
    except Exception as e:
        return {"error": f"ERROR OCCURED WHILE SENDING WHATSAPP MESSAGE, TRY AGAIN"}
    



# # Example usage
# if __name__ == "__main__":
#     print("WhatsApp Message Sender")
#     print("=======================")
    
#     result = send_whatsapp_message(
#         country_code="91",     
#         phone_number="8450995752",
#         message="Hello! This is a test message sent using Python.",
#         headless=True
#     )
    
#     if not result:
#         print("\nMessage sending failed. Please check the error messages above.")
#     else:
#         print("\nOperation completed successfully."