import os
import shutil
import subprocess
import sys
import datetime
import logging
from llama_cpp import Llama

def archive_prior_results(output_directory, rounds):
    # Archive prior results before starting a new round
    for round_number in range(1, rounds):
        prior_round_directory = os.path.join(output_directory, f"round_{round_number}")
        archive_directory(prior_round_directory, f"{prior_round_directory}_archive")

def archive_directory(source, destination):
    # Archive the source directory as a zip file
    shutil.make_archive(destination, 'zip', source)
    # Remove the original source directory
    shutil.rmtree(source)

def setup_logging():
    # Configure logging to log to a timestamped file
    log_filename = f"script_log_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_code_revision(original_code, model_name):
    # Generate code revision using llama_cpp library
    logging.info("Generating code revision.")

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
        "temperature": 0.87,
        "top_p": 0.99,
        "top_k": 85,
        "repetition_penalty": 1.01,
        "typical_p": 0.68,
        "tfs": 0.68
    }
    
    try:
        llama = Llama(model_name, **llama_params)

        messages = [{"role": "system", "content": "Please revise the following code and respond with only the revised code in markdown. If pseudocode is provided, generate valid code based on requested programming language to complete the necessary task. Focus on performance, usability, and general code quality, and please only respond with the revised code in markdown: " + original_code}]
        response = llama.create_chat_completion(messages=messages)

        # Log the question and response
        logging.info(f"Question: {messages[0]['content']}")
        logging.info(f"Response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error generating code revision: {str(e)}")
        return original_code  # Return original code in case of an error

def process_file(input_path, output_path, model_name):
    # Process a file by generating a code revision and extracting code blocks
    logging.info(f"Processing file: {input_path}")
    
    try:
        with open(input_path, 'r') as file:
            original_code = file.read()

        # Convert original_code to a string
        original_code = str(original_code)

        revised_code = generate_code_revision(original_code, model_name)

        # Write the revised code to the output file
        with open(output_path, 'w') as file:
            file.write(revised_code)

    except Exception as e:
        logging.error(f"Error processing file {input_path}: {str(e)}")
        shutil.copyfile(input_path, output_path)  # Copy the original file in case of an error

def main(target_directory, output_directory, rounds, model_name):
    # Main function to process files in multiple rounds
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    logging.info("Script execution started.")

    # Create 'Output' directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for round_number in range(1, rounds + 1):
        round_output_directory = os.path.join(output_directory, f"round_{round_number}")
        logging.info(f"Round {round_number}: Creating directory {round_output_directory}")
        
        # Archive prior results
        archive_prior_results(output_directory, round_number)

        # Copy the original target directory to the round's output directory
        shutil.copytree(target_directory, round_output_directory, symlinks=False, ignore=None)

        for root, dirs, files in os.walk(round_output_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(('.py', '.java', '.cpp', '.cs')):
                    process_file(file_path, file_path, model_name)

    logging.info("Script execution completed.")

if __name__ == "__main__":
    setup_logging()
    target_directory = "Target"
    output_directory = "Output"
    rounds = 3
    model_name = "openhermes-2.5-mistral-7b-16k.Q2_K.gguf"
    main(target_directory, output_directory, rounds, model_name)
