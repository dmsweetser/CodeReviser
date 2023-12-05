import os
import shutil
import re
import requests
import subprocess

def generate_code_revision(original_code, model_name):
    llama_path = os.path.join("llamacpp", "llama")  # Adjust based on the actual path
    
    # Define llama.cpp parameters
    llama_params = [
        "--loader", "llama.cpp",
        "--cpu", "false",
        "--threads", "0",
        "--threads_batch", "0",
        "--n_batch", "512",
        "--no_mmap", "false",
        "--mlock", "true",
        "--no_mul_mat_q", "false",
        "--n_gpu_layers", "0",
        "--tensor_split", "",
        "--n_ctx", "16384",
        "--compress_pos_emb", "1",
        "--alpha_value", "1",
        "--rope_freq_base", "0",
        "--numa", "false",
        "--model", model_name,
        "--temperature", "0.87",               # Add temperature parameter
        "--top_p", "0.99",                     # Add top_p parameter
        "--top_k", "85",                       # Add top_k parameter
        "--repetition_penalty", "1.01",        # Add repetition_penalty parameter
        "--typical_p", "0.68",                 # Add typical_p parameter
        "--tfs", "0.68"                        # Add tfs parameter
    ]

    subprocess.run([llama_path, "generate", "--input", original_code, "--output", "revised_code.cpp"] + llama_params)

    # Read the generated code from the file
    with open("revised_code.cpp", 'r') as file:
        revised_code = file.read()

    return revised_code

def process_file(input_path, output_path):
    with open(input_path, 'r') as file:
        original_code = file.read()

    revised_code = generate_code_revision(original_code, model_name)

    # Extract code from markdown
    code_matches = re.findall("```(.+?)```", revised_code, flags=re.DOTALL)
    revised_code = "\n".join(code_matches)

    with open(output_path, 'w') as file:
        file.write(revised_code)

def main(target_directory, output_directory, rounds):
    for round_number in range(1, rounds + 1):
        round_output_directory = os.path.join(output_directory, f"round_{round_number}")

        # Replicate folder structure
        shutil.copytree(target_directory, round_output_directory, symlinks=False, ignore=None)

        for root, dirs, files in os.walk(round_output_directory):
            for file in files:
                file_path = os.path.join(root, file)

                # Check if the file has an authorized file type
                if file.lower().endswith(('.py', '.java', '.cpp', '.cs')):
                    output_file_path = os.path.join(output_directory, f"round_{round_number}", file)
                    process_file(file_path, output_file_path)

        target_directory = round_output_directory

    # Merge final output with target directory
    final_output_directory = os.path.join(output_directory, f"round_{rounds}")
    shutil.copytree(target_directory, final_output_directory, symlinks=False, ignore=None)

    # Merge contents into target directory
    for root, dirs, files in os.walk(final_output_directory):
        for file in files:
            file_path = os.path.join(root, file)
            target_path = os.path.join(target_directory, os.path.relpath(file_path, final_output_directory))
            shutil.copy(file_path, target_path)

    # Run "dotnet test"
    # Add your code for running tests here

if __name__ == "__main__":
    target_directory = "Target"
    output_directory = "Output"
    rounds = 3  # Specify the number of rounds
    model_name = "openhermes-2.5-mistral-7b-16k.Q8_0.gguf"  # Specify the model name

    main(target_directory, output_directory, rounds)
