import os
import shutil
import subprocess
import sys
import datetime
import logging
import re
from llama_cpp import Llama
import time

max_tokens = 16384
file_extensions = ('.py', '.java', '.cpp', '.cs', '.cshtml', '.js')

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
    log_filename = f"script_log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_code_revision(original_code, output_directory,):
    # Check if original_code is more than 40% of max_tokens
    if len(original_code) > 0.5 * max_tokens:
        return generate_file_revisions(original_code, output_directory)

    logging.info("Generating code revision.")
    
    try:
        messages = [{"role": "system", "content": "Revise and enhance the provided code, addressing issues, optimizing, and expanding features; implement pseudocode, comments, and placeholders; suggest additional features or improvements in comments or pseudocode for iterative development in subsequent rounds. YOU MUST ALWAYS generate a properly-commented summary of the overall intent of the code that mentions every intended feature. Use the same programming language as the provided code. Here is the provided code: " + original_code}]
        response = llama.create_chat_completion(messages=messages, temperature=1.0)

        logging.info(f"Question: {messages[0]['content']}")
        logging.info(f"Response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error generating code revision: {str(e)}")
        return original_code  # Return original code in case of an error

def generate_file_revisions(original_code, output_directory):
    # Generate code revisions for individual files
    logging.info("Generating file revisions.")

    try:
        messages = [{"role": "system", "content": "Refactor the provided code to enable separation into individual files. Each refactored part should be enclosed in markdown, representing an individual file. YOU MUST ALWAYS generate a properly-commented summary of the overall intent of the code that mentions every intended feature, as well as how the refactored individual file contributes to that goal. Use the same programming language as the provided code. Here is the provided code: " + original_code}]
        response = llama.create_chat_completion(messages=messages, temperature=1.0)

        logging.info(f"Question: {messages[0]['content']}")
        logging.info(f"Response: {response}")

        # Extract file names and contents from the response
        file_revisions = extract_file_revisions(response)
        logging.info("Here are the file revisions:")
        logging.info(file_revisions)
        
        return file_revisions

    except Exception as e:
        logging.error(f"Error generating file revisions: {str(e)}")
        return [{"filename": "error_file.txt", "content": original_code}]

def extract_file_revisions(response):
    # Extract file contents from the response using backticks
    file_revisions = []
    pattern = re.compile(r'```.*?```', re.DOTALL)

    matches = pattern.finditer(response['choices'][0]['message']['content'])

    for index, match in enumerate(matches, start=1):
        content = match.group(0)[3:-3].strip()  # Remove triple backticks and strip whitespaces
        # Remove the first line, which would include the language name
        content = content.split('\n', 1)
        file_revisions.append({"filename": f"file_{index}", "content": content})

    return file_revisions

def save_file_revisions(file_revisions, output_directory, round_number, original_filename):
    # Save the contents as files in the current round directory
    round_output_directory = os.path.join(output_directory, f"round_{round_number}")

    for index, revision in enumerate(file_revisions, start=1):
        original_extension = os.path.splitext(original_filename)[1]
        new_filename = f"{original_filename}_{index}{original_extension}"
        new_filepath = os.path.join(round_output_directory, new_filename)

        # Check if the content is a list (in case it's a code block with language info)
        if isinstance(revision["content"], list):
            # Join the list elements into a string
            content_str = '\n'.join(revision["content"])
        else:
            content_str = revision["content"]

        with open(new_filepath, 'w') as file:
            file.write(content_str)

        logging.info(f"File revision saved: {new_filepath}")

def process_file(input_path, output_path, output_directory, round_number):
    logging.info(f"Processing file: {input_path}")

    try:
        with open(input_path, 'r') as file:
            original_code = file.read()

        # Convert original_code to a string
        original_code = str(original_code)

        response = generate_code_revision(original_code, output_directory)

        if type(response) == list:
            # File revisions generated, save them
            save_file_revisions(response, output_directory, round_number, os.path.basename(input_path))
            # Remove the input file after processing
            os.remove(input_path)
            logging.info(f"Input file {input_path} removed after processing.")
            return

        # Extract the revised code from the response inside the Markdown code block using regular expression
        pattern = re.compile(r'```.*?```', re.DOTALL)
        match = pattern.search(response['choices'][0]['message']['content'])

        if match:
            revised_code = match.group(0)[3:-3].strip()  # Remove the triple backticks and strip leading/trailing whitespaces

            # Remove the first line from the revised_code
            revised_code_lines = revised_code.split('\n', 1)
            if len(revised_code_lines) > 1:
                revised_code = revised_code_lines[1]

        else:
            # If no match is found, use the entire content
            revised_code = response['choices'][0]['message']['content'].strip()

        # Write the revised code to the output file
        with open(output_path, 'w') as file:
            file.write(revised_code)

    except Exception as e:
        logging.error(f"Error processing file {input_path}: {str(e)}")
        shutil.copy2(input_path, output_path)

def main(target_directory, output_directory, rounds):

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

        for root, dirs, files in os.walk(round_output_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(file_extensions):
                    process_file(file_path, file_path, output_directory, round_number)

    logging.info("Script execution completed.")

if __name__ == "__main__":

    start_time = time.time()

    file_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q5_K_S.gguf"
    file_name = "mistral-7b-instruct-v0.2.Q5_K_S.gguf"

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
    rounds = 100
    model_name = file_name
    
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
        "tfs": 0.68,
        "max_tokens": max_tokens
    }
    
    llama = Llama(model_name, **llama_params)

    main(source_directory, output_directory, rounds + 1)
        
    end_time = time.time()
    total_execution_time = end_time - start_time
    logging.info(f"Total execution time: {total_execution_time} seconds.")
