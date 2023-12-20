import os
import shutil
import datetime
import logging
from llama_cpp import Llama
import time

max_tokens = 32768
file_extensions = ('.py', '.java', '.cpp', '.cs', '.cshtml', '.js', '.html')

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

def generate_code_revision(original_code):

    logging.info("Generating code revision.")
    
    try:

        # Define llama.cpp parameters
        llama_params = {
            "loader": "llama.cpp",
            "cpu": False,
            "threads": 0,
            "threads_batch": 0,
            "n_batch": 512,
            "no_mmap": False,
            "mlock": False,
            "no_mul_mat_q": False,
            "n_gpu_layers": 0,
            "tensor_split": "",
            "n_ctx": max_tokens,
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

        response = llama(
            "Enhance the provided code by replacing placeholders or pseudocode with actual implementations. Utilize the same programming language as the original. Generate as many properly-escaped comments as you can, including adding at least five TODO items for potential new features. Your revised code should always be longer than the provided code. Present the revised code solely in markdown format. Here is the provided code: " + original_code)

        logging.info(f"Response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error generating code revision: {str(e)}")
        return original_code  # Return original code in case of an error

def process_file(input_path, output_path):
    logging.info(f"Processing file: {input_path}")

    try:

        with open(input_path, 'r') as file:
            original_code = file.read()

        response = generate_code_revision(str(original_code))

        revised_code = response['choices'][0]['text'].strip()

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
                    process_file(file_path, file_path)

    logging.info("Script execution completed.")

if __name__ == "__main__":

    start_time = time.time()

    file_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_S.gguf"
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
        
    main(source_directory, output_directory, rounds + 1)
        
    end_time = time.time()
    total_execution_time = end_time - start_time
    logging.info(f"Total execution time: {total_execution_time} seconds.")
