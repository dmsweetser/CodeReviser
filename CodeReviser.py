import os
import shutil
import datetime
import logging
import re
from llama_cpp import Llama

def split_methods(file_path, output_directory, max_method_size):
    try:
        with open(file_path, 'r') as file:
            original_code = file.read()

        # Check if the file is a C# file
        if file_path.lower().endswith('.cs'):
            # Split methods based on an arbitrary maximum size
            methods = re.split(r'\b(?:public|private|protected|internal|static|void)\b', original_code)
            method_files = []

            for i, method in enumerate(methods):
                if len(method) > max_method_size:
                    # Create a new file for the large method with an index in the filename
                    method_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_method_{i + 1}.cs"
                    method_filepath = os.path.join(output_directory, method_filename)

                    with open(method_filepath, 'w') as method_file:
                        method_file.write(method)

                    method_files.append(method_filepath)

            return method_files

        else:
            # If not a C# file, return the original file
            return [file_path]

    except Exception as e:
        logging.error(f"Error splitting methods in file {file_path}: {str(e)}")
        return [file_path]

def combine_files(output_directory, combined_filename, method_files):
    try:
        # Sort the method files based on the index in the filename
        method_files.sort(key=lambda x: int(re.search(r'_method_(\d+)\.cs', x).group(1)))

        # Combine the split method files into a single file
        combined_filepath = os.path.join(output_directory, combined_filename)

        with open(combined_filepath, 'w') as combined_file:
            for method_file in method_files:
                with open(method_file, 'r') as method_content:
                    combined_file.write(method_content.read())
                # Remove the individual method file after combining
                os.remove(method_file)

        return combined_filepath

    except Exception as e:
        logging.error(f"Error combining method files: {str(e)}")
        return None

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

        messages = [{"role": "system", "content": "Please revise the following code and respond with only the revised code in markdown. If pseudocode is provided, generate valid code based on requested programming language to complete the necessary task. For any changes made, please include an inline comment explaining the rationale. Focus on performance, usability, and general code quality, and please only respond with the revised code in markdown: " + original_code}]
        response = llama.create_chat_completion(messages=messages)

        # Log the question and response
        logging.info(f"Question: {messages[0]['content']}")
        logging.info(f"Response: {response}")

        return response

    except Exception as e:
        logging.error(f"Error generating code revision: {str(e)}")
        return original_code  # Return original code in case of an error

def process_file(input_path, output_path, output_directory, model_name, max_method_size):
    # Process a file by splitting methods, generating a code revision, and then combining methods
    logging.info(f"Processing file: {input_path}")

    try:
        # Split and revise methods if the file is a C# file
        method_files = split_methods(input_path, output_directory, max_method_size)

        # Combine the split method files into a single file
        combined_filename = f"{os.path.splitext(os.path.basename(output_path))[0]}_combined.cs"
        combined_filepath = combine_files(output_directory, combined_filename, method_files)

        # Read the combined file for generating code revision
        with open(combined_filepath, 'r') as file:
            original_code = file.read()

        # Convert original_code to a string
        original_code = str(original_code)

        revised_response = generate_code_revision(original_code, model_name)

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

        return combined_filepath

    except Exception as e:
        logging.error(f"Error processing file {input_path}: {str(e)}")
        shutil.copyfile(input_path, output_path)  # Copy the original file in case of an error
        return None

# Modify the main function

def main(target_directory, output_directory, rounds, model_name, max_method_size):
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
                if file.lower().endswith(('.py', '.java', '.cpp', '.cs', '.js', '.cshtml')):
                    process_file(file_path, file_path, round_output_directory, model_name, max_method_size)

    logging.info("Script execution completed.")

if __name__ == "__main__":
    setup_logging()
    target_directory = "Target"
    output_directory = "Output"
    rounds = 5
    model_name = "openhermes-2.5-mistral-7b-16k.Q2_K.gguf"
    max_method_size = 4096
    main(target_directory, output_directory, rounds + 1, model_name, max_method_size)
