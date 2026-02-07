
import sys
import re
import json
import os

# Import the run_test logic from manual_test (assuming it's in the same dir or importable)
# We might need to adjust sys.path if running from root
sys.path.append(os.getcwd())
# Ensure part3_api is in path if not
if "part3_api" not in sys.path[-1]:
    sys.path.append(os.path.join(os.getcwd(), "part3_api"))

try:
    from part3_api.manual_test import run_test
except ImportError:
    # Try relative import if running from part3_api dir
    try:
        from manual_test import run_test
    except ImportError:
        print("Could not import manual_test. Make sure you are running from project root.")
        sys.exit(1)

# Capture stdout to capture the JSON output from run_test
from io import StringIO
from contextlib import redirect_stdout

def process_batch(input_file_path, output_file_path=None):
    print(f"Reading inputs from {input_file_path}...")
    
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Regex to find inputs. Ideally, we look for "input N:", optional "lang:...", then base64
    # Pattern: input\s*\d+:(?:\s*lang:(\w+))?\s*([A-Za-z0-9+/=\n]+?)(?=input\s*\d+:|$)
    # We need to handle the base64 spanning multiple lines and potentially being huge.
    
    # We'll split by "input " keyword to be robust
    raw_blocks = re.split(r'(input\s+\d+:)', content, flags=re.IGNORECASE)
    
    # raw_blocks[0] might be empty or header garbage
    # raw_blocks[1] is "input 2:", raw_blocks[2] is the content for 2, etc.
    
    results = []
    
    # Iterate in pairs: label, content
    # Start from index 1 because index 0 is pre-match text
    if len(raw_blocks) < 2:
        print("No 'input N:' markers found.")
        return

    for i in range(1, len(raw_blocks), 2):
        label = raw_blocks[i].strip().rstrip(':') # e.g. "input 2"
        block_content = raw_blocks[i+1].strip()
        
        # Check for lang: specification in the block content
        # Format "lang:hindi" or similar
        lang_match = re.search(r'lang\s*:\s*(\w+)', block_content, re.IGNORECASE)
        language_arg = "Tamil" # Default
        
        if lang_match:
            language_arg = lang_match.group(1)
            # Remove the lang line from content so it doesn't mess up base64
            # We assume it's at the start or on its own line
            block_content = re.sub(r'lang\s*:\s*\w+\s*', '', block_content, flags=re.IGNORECASE).strip()
            
        # The leftover block_content is the base64 (potentially multi-line)
        # Clean it up: remove newlines/spaces
        base64_str = "".join(block_content.split())
        
        print(f"\nProcessing {label} (Language: {language_arg})...")
        
        # Capture the JSON output from manual_test
        f_out = StringIO()
        with redirect_stdout(f_out):
            run_test(base64_str, label_hint=label, language=language_arg)
        
        output = f_out.getvalue().strip()
        # manual_test might print other logs, find the JSON part
        try:
            # Look for the JSON block (starts with { ends with })
            json_block = output[output.find('{'):output.rfind('}')+1]
            if json_block:
                results.append((label, json_block))
                print(f"Result for {label}: Success")
            else:
                print(f"Result for {label}: Failed to parse output")
                results.append((label, "Error: Could not parse script output"))
        except Exception as e:
            print(f"Error processing {label}: {e}")
            results.append((label, str(e)))



    # Determine output file path
    if not output_file_path:
        output_file_path = os.path.splitext(input_file_path)[0] + "_output.txt"
        
    # Write output to separate file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write("=== AUTOMATED OUTPUTS ===\n")
        for label, res in results:
            f.write(f"\n[{label} Output]\n")
            f.write(res)
            f.write("\n")
    
    print(f"\nProcessing complete. Results written to {output_file_path}")
    
    # Also output to console for chat
    print("\n=== CONSOLE REPORT ===")
    for label, res in results:
        print(f"\n--- {label} ---")
        print(res)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_test.py <input_file> [output_file]")
        sys.exit(1)
        
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    process_batch(sys.argv[1], output_path)

