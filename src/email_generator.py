import json
import re
import openai


class EmailGenerator:
    """This class is responsible for handling operations related to personalised emails based on job parser output and candidate matching output

        args:
            job_parser: json output of job parser api
            candidate_matching: json output of candidate matching api
    """

    def __init__(self, job_parser:json, candidate_matching:json) -> None:

        self.job_parser = job_parser
        self.candidate_matching = candidate_matching

        # openai credentials
        openai.api_type = 'azure'
        openai.api_base = "https://test-chatgpt-sproutsai-nlp-team.openai.azure.com/"
        openai.api_version = "2023-03-15-preview"
        openai.api_key = 'b72034179b3c45468bf9c7389d51e403'

    def generate_email(self) -> json:
        """This method is responsible for fetching job parser details and candidate matching details and merging the whole schema of the composed email.
        
            return:
                email_text: json having two keys subject and body of the email
        """
        try:
            # Loading json output
            job_parser = json.loads(self.job_parser)
            candidate_matching = json.loads(self.candidate_matching)

            # Extract job details
            company_name = job_parser.get('Extracted', {}).get('company_name') or job_parser.get('rawData', {}).get('company_name')
            job_position = job_parser.get('Extracted', {}).get('job_position') or job_parser.get('rawData', {}).get('job_position')
            job_type = job_parser.get('Extracted', {}).get('job_type') or job_parser.get('rawData', {}).get('job_type')
            workplace_type = job_parser.get('Extracted', {}).get('workplace_type') or job_parser.get('rawData', {}).get('workplace_type')
            job_location = job_parser.get('Extracted', {}).get('job_location') or job_parser.get('rawData', {}).get('job_location')

            # Extract candidate matching details
            candidate_name = candidate_matching.get('full_name') or candidate_matching.get('full name')
            candidate_matching_comment = candidate_matching.get('matching_result', {}).get('comparison_comment') or candidate_matching.get('matching_result', {}).get('comparison comment')
            candidate_matching_comment = extract_word(remove_text_between_parentheses(candidate_matching_comment))

            # Subject
            subject = f"You're invited: Job Interview for {job_position} at {company_name}"

            # Components of body
            salutations = f"Dear {candidate_name}\n\n"
            opening_line = f"We are pleased to extend an interview invitation for the {job_position} at {company_name}. "

            # Generate candidate matching line using OpenAI
            candidate_match_line = self.generate_candidate_match_line(candidate_matching_comment)

            # Handle N/A values
            job_type = "" if job_type == 'N/A' else job_type
            workplace_type = "" if workplace_type == 'N/A' else workplace_type
            job_location = "" if job_location == 'N/A' else job_location

            company_para = f"We offer an exciting {job_type} {workplace_type} opportunity with competitive compensation and ample career growth prospects. Join us in achieving success together."

            action_para = "If you find this opportunity appealing, please revert with your updated resume, and we will be glad to schedule an interview at your convenience. We are eager to learn more about your experience and how your expertise can contribute to our team.\n\n"

            closing_para = "With your skills, you can make a significant impact here. Feel free to reach out with any questions. We look forward to your response. Good luck!\n\n"

            closing_titles = f"Regards\n{company_name}"

            # Email body
            body = salutations + opening_line + candidate_match_line + '\n\n' + company_para + '\n\n' + action_para + closing_para + closing_titles
            
            body = self.email_corrector(body)

            data = {'subject': subject, 'body': body}
            email_text = json.dumps(data)

            return email_text
        except Exception as e:
            # Log the error
            print(f"Error: {e}")
            return None

    @staticmethod
    def generate_candidate_match_line(candidate_matching_comment:str) -> str:
        """This method is responsible for getting the personalized candidate unique for each candidate

            args:
                candidate_matching_comment: One of the output of candidate matching json

            return:
                candidate_matching_line: Personalised content
        """
        try:
            response = openai.ChatCompletion.create(
                engine='gpt35june', 
                messages=[
                    {'role':'system', 'content':'You are an assistant tasked with composing a follow-up message based on a matching comparison comment for a specific job candidate.'},
                    {'role':'system', 'content':'Address the candidate directly, using the second person.'},
                    {'role':'system', 'content':"Avoid mentioning the candidate's LinkedIn profile."},
                    {'role':'system', 'content':'Maintain a confident and professional tone throughout the message.'},
                    {'role':'system', 'content':'Keep the message concise and impactful.'},
                    {'role':'system', 'content':'Refrain from asking any questions in your response.'},
                    {'role':'system', 'content':'Begin your response with a phrase like "Your impressive"'},
                    {'role':'system', 'content':'If the candidate has multiple previous roles, mention only the most relevant one.'},
                    {'role':'system', 'content':'Ensure that your response does not exceed 50 words in total.'},
                    {'role':'system', 'content':'Highlight only the two most relevant skills in your response.'},
                    {'role':'system', 'content':'Keep the message strictly within two lines.'},
                    {'role':'user', 'content':f"{candidate_matching_comment}"}
                ],
                temperature=0
            )
            candidate_match_line = response['choices'][0]['message']['content']
            return remove_text_after_first_newline(remove_text_before_first_newline(candidate_match_line))
        except Exception as e:
            print(f"Error generating candidate match line: {e}")
            return ""
        
    @staticmethod
    def email_corrector(body:str) -> str:
        """This method is responsible for checking the consistency of the email
        
            args:
                body: body of the email

            return:
                corrected body of the email
        """
        response = openai.ChatCompletion.create(
            engine='gpt35june', 
            messages=[
                {'role':'system', 'content':'You are an assistant who checks the body of the email and check if there is any inconsistency in language or not. If inconsistency is there then you improve it without making much changes to the template.'},
                {'role':'system', 'content':'Do not write subject in the mail'},
                {'role':'user', 'content':f"{body}"}
            ]
        )
        return response['choices'][0]['message']['content']
    
def remove_text_between_parentheses(text:str) -> str:
    """Function to remove text between the parenthesis
    
        args:
            text: Any text from which parenthesis text to be removed

        return:
            cleaned_text: Text with parenthesis data removed along with parenthesis
    """
    cleaned_text = re.sub(r'\([^)]*\)', '', text)
    return cleaned_text

def extract_word(text:str) -> str:
    """Function to remove '/' from the text and to select one word randomly from slashed words
    
        args:
            text: Text from which '/' to be removed
        
        return:
            cleaned_text: Text with no '/'
    """
    match = re.search(r'(\w+)\/(\w+)', text)
    
    if match:
        extracted_word = match.group(1)
        cleaned_text = text.replace(match.group(0), extracted_word)
        return cleaned_text
    
    else:
        return text

def remove_text_before_first_newline(text:str) -> str:
    """Function to remove new line character before any new line character
    
        args:
            text: Text from which characters before new line is to be removed

        return:
            cleaned_text: cleaned text after removing text before new line character
    """
    newline_index = text.find('\n')
    
    if newline_index != -1:
        # Remove everything before the first newline character
        cleaned_text = text[newline_index + 1:].strip()
    else:
        # If no newline character is found, return the original text
        cleaned_text = text
    
    return cleaned_text

def remove_text_after_first_newline(text:str) -> str:
    """Function to remove new line character after any new line character
    
        args:
            text: Text from which characters after new line is to be removed

        return:
            cleaned_text: cleaned text after removing text after new line character
    """
    newline_index = text.find('\n')
    
    if newline_index != -1:
        # Remove everything after the first newline character
        cleaned_text = text[:newline_index].strip()
    else:
        # If no newline character is found, return the original text
        cleaned_text = text
    
    return cleaned_text