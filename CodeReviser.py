import os
import shutil
import subprocess
import sys
import datetime
import logging
import re
from llama_cpp import Llama
import time

def archive_prior_results(output_directory, current_round):
    # Archive prior results before starting a new round
    for round_number in range(1, current_round):
        prior_round_directory = os.path.join(output_directory, f"round_{round_number}")
        archive_directory(prior_round_directory, f"{prior_round_directory}_archive")

def archive_directory(source, destination):
    # Check if the source directory exists
    if not os.path.exists(source):
        logging.warning(f"Source directory '{source}' does not exist. Skipping archiving.")
        return

    try:
        # Archive the source directory as a zip file
        shutil.make_archive(destination, 'zip', source)
        # Remove the original source directory
        shutil.rmtree(source)
    except Exception as e:
        logging.error(f"Error archiving directory {source}: {str(e)}")

def setup_logging():
    # Configure logging to log to a timestamped file
    log_filename = f"script_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_code_revision(original_code, temperature):
    # Generate code revision using llama_cpp library
    logging.info("Generating code revision.")
    
    try:

        messages = [{"role": "system", "content": "Can you make this code better? If you see placeholders or pseudocode, please replace them with actual implementations. Please generate revisions in the same code language as the original. Please only respond with the revised code in markdown: " + original_code}]
        response = llama.create_chat_completion(messages=messages, temperature=temperature)

        # Log the question and response
        logging.info(f"Question: {messages[0]['content']}")
        logging.info(f"Response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error generating code revision: {str(e)}")
        return original_code  # Return original code in case of an error

def process_file(input_path, output_path, temperature):
    # Process a file by generating a code revision and extracting code blocks
    logging.info(f"Processing file: {input_path}")

    try:
        with open(input_path, 'r') as file:
            original_code = file.read()

        # Convert original_code to a string
        original_code = str(original_code)

        revised_response = generate_code_revision(original_code, temperature)

        # Extract the revised code from the response inside the Markdown code block using regular expression
        pattern = re.compile(r'```.*?```', re.DOTALL)
        match = pattern.search(revised_response['choices'][0]['message']['content'])

        if match:
            revised_code = match.group(0)[3:-3].strip()  # Remove the triple backticks and strip leading/trailing whitespaces

            # Remove the first line from the revised_code
            revised_code_lines = revised_code.split('\n', 1)
            if len(revised_code_lines) > 1:
                revised_code = revised_code_lines[1]

        else:
            # If no match is found, use the entire content
            revised_code = revised_response['choices'][0]['message']['content'].strip()

        # Write the revised code to the output file
        with open(output_path, 'w') as file:
            file.write(revised_code)

    except Exception as e:
        logging.error(f"Error processing file {input_path}: {str(e)}")
        shutil.copyfile(input_path, output_path)  # Copy the original file in case of an error

def main(target_directory, output_directory, rounds, temperatures):

    # Main function to process files in multiple rounds
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    logging.info("Script execution started.")

    # Create 'Output' directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for round_number in range(1, rounds):
        round_output_directory = os.path.join(output_directory, f"round_{round_number}")
        logging.info(f"Round {round_number}: Creating directory {round_output_directory}")

        if round_number == 1:
            # For the first round, use the original target directory
            shutil.copytree(target_directory, round_output_directory, symlinks=False, ignore=None)
        else:
            # For subsequent rounds, copy the results from the previous round
            prior_round_directory = os.path.join(output_directory, f"round_{round_number - 1}")
            shutil.copytree(prior_round_directory, round_output_directory, symlinks=False, ignore=None)

        # Archive prior results
        archive_prior_results(output_directory, round_number)

        # Use the specified temperature for this round
        temperature = temperatures[round_number - 1]

        for root, dirs, files in os.walk(round_output_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(('.py', '.java', '.cpp', '.cs', '.cshtml', '.js')):
                    process_file(file_path, file_path, temperature)

    logging.info("Script execution completed.")

if __name__ == "__main__":

    start_time = time.time()

    file_url = "https://huggingface.co/TheBloke/Yarn-Mistral-7B-128k-GGUF/blob/main/yarn-mistral-7b-128k.Q2_K.gguf"
    file_name = "yarn-mistral-7b-128k.Q2_K.gguf"

    # Check if the file already exists
    if not os.path.exists(file_name):
        # If not, download the file
        response = requests.get(file_url)
        with open(file_name, "wb") as file:
            file.write(response.content)
        print(f"{file_name} downloaded successfully.")
    else:
        print(f"{file_name} already exists in the current directory.")

    setup_logging()
    source_directory = "Source"
    output_directory = "Output"
    rounds = 5
    model_name = file_name
    temperatures = [1.0, 1.0, 1.0, 0.87, 0.87]  # Specify temperatures for each round
    
    # Define llama.cpp parameters
    llama_params = {
        "loader": "llama.cpp",
        "cpu": False,
        "threads": 0,
        "threads_batch": 0,
        "n_batch": 512,
        "no_mmap": False,
        "mlock": True,
        "no_mul_mat_q": False,
        "n_gpu_layers": 0,
        "tensor_split": "",
        "n_ctx": 16384,
        "compress_pos_emb": 1,
        "alpha_value": 1,
        "rope_freq_base": 0,
        "numa": False,
        "model": model_name,
        "temperature": 1.0,
        "top_p": 0.99,
        "top_k": 85,
        "repetition_penalty": 1.01,
        "typical_p": 0.68,
        "tfs": 0.68
    }
    
    llama = Llama(model_name, **llama_params)
    
    main(source_directory, output_directory, rounds + 1, temperatures)
        
    end_time = time.time()
    total_execution_time = end_time - start_time
    logging.info(f"Total execution time: {total_execution_time} seconds.")
