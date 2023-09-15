from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from email_generator import EmailGenerator
import json

app = FastAPI()

# Define a Pydantic model to handle input data
class EmailGeneratorInput(BaseModel):
    job_parser: dict
    candidate_matching: dict


# Create an instance of the EmailGenerator class
email_generator = EmailGenerator(job_parser={}, candidate_matching={})

# Define the endpoint to generate emails
@app.post("/generate_email/")
async def generate_email(input_data: EmailGeneratorInput):
    try:
        # Pass the input data to the EmailGenerator instance
        email_generator.job_parser = json.dumps(input_data.job_parser)
        email_generator.candidate_matching = json.dumps(input_data.candidate_matching)

        # Generate the email
        email_text = email_generator.generate_email()
        
        if email_text is not None:
            return {"email": json.loads(email_text)}
        else:
            raise HTTPException(status_code=500, detail="Error generating email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
