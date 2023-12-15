# Code Reviser
_Built in collaboration with generative AI_

This repository contains Python code for performing code revision using the Llama.cpp tool. The process involves multiple rounds of revision, and the final output is stored in the "Output" directory.

## Prerequisites

Make sure you have the following prerequisites installed before running the code:

- Llama.cpp: Follow the installation instructions [here](llamacpp/llama/INSTALL.md) to install Llama.cpp.
- Python: Ensure you have Python 3.12 installed on your system.
- Microsoft C++ Build Tools: Ensure you have the proper build tools available for C/C++ (see discussion here: https://github.com/imartinez/privateGPT/issues/18). It may involve the following:
  
- ![image](https://github.com/dmsweetser/CodeReviser/assets/37463869/4679e46d-640b-4e7e-93b6-d4d5aec7dc80)


## Usage

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/dmsweetser/CodeReviser.git
   cd CodeReviser
   ```

2. Set up the target directory with the initial code you want to revise. Place the code files in the "Target" directory.

3. Adjust the parameters in the `main()` function of the `revision.py` file according to your requirements. Set the `rounds` variable to the desired number of revision rounds and specify the Llama.cpp model name.

4. Run the code:

   ```bash
   python CodeReviser.py
   ```

   This will perform multiple rounds of code revision using Llama.cpp, and the final revised code will be stored in the "Output" directory.

## Parameters

You can customize the revision process by modifying the parameters in the `llama_params` list in the `generate_code_revision()` function within the `revision.py` file. These parameters include temperature, top_p, top_k, repetition_penalty, typical_p, and tfs.

## Additional Notes

- The code supports files with the extensions `.py`, `.java`, `.cpp`, and `.cs`. Make sure your target code files have one of these extensions.

- The generated code from Llama.cpp is extracted from markdown code blocks within the revised code. The `process_file()` function handles this extraction.

Feel free to explore and experiment with the code revision process to suit your needs.
