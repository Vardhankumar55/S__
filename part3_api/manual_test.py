
import sys
import os
import base64
import json
import io
import argparse
from unittest.mock import MagicMock

# 1. Mock critical dependencies BEFORE importing app modules
sys.modules["structlog"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["librosa"] = MagicMock()

# Mock part1 and part2
part1_mock = MagicMock()
part1_mock.extract_features.return_value = MagicMock()

part2_mock = MagicMock()
# Default mock result
part2_mock.infer.return_value = {
    "classification": "Fake",
    "confidence": 0.98,
    "explanation": "High frequency anomalies detected.\nRobotic phrasing observed.\n(Mocked for testing)"
}

sys.modules["part1"] = part1_mock
sys.modules["part2"] = part2_mock

# Adjust paths
sys.path.append(r"d:\spectra\Spectral_Lie\part3_api")

try:
    from app import orchestrator
    orchestrator.part1 = part1_mock
    orchestrator.part2 = part2_mock
except ImportError as e:
    print(json.dumps({"status": "error", "message": f"Import Error: {e}"}))
    sys.exit(1)

import random
import hashlib

def run_test(input_base64, label_hint="Input Test", language="Tamil"):
    try:
        # Check for smart input (JSON)
        final_base64 = input_base64
        final_language = language
        
        if input_base64.strip().startswith('{') and input_base64.strip().endswith('}'):
            try:
                parsed = json.loads(input_base64)
                if "audioBase64" in parsed: final_base64 = parsed["audioBase64"]
                if "language" in parsed: final_language = parsed["language"]
                # Format ignored for now as mock handles it
            except:
                pass # Parse error, assume raw base64

        # Generate a semi-random confidence based on input content digest
        # This ensures "random" but deterministic results for the same input
        input_hash = hashlib.md5(final_base64.encode('utf-8', errors='ignore')).hexdigest()
        seed = int(input_hash[:8], 16)
        random.seed(seed)
        
        # Mock Logic:
        # If input has "lang:..." that wasn't stripped, or just random
        # Let's say inputs ending in specific char are Real vs Fake to give variety
        # Or just random
        is_fake = random.choice([True, True, False]) # Bias towards Fake as per typical test data
        
        base_conf = 0.90 + (random.random() * 0.09) # 0.90 to 0.99
        
        if not is_fake:
             part2_mock.infer.return_value = {
                "classification": "Real",
                "confidence": base_conf,
                "explanation": "Natural prosody detected.\nNo artifacts observed in high frequencies.\nConsistent background noise profile."
            }
        else:
             part2_mock.infer.return_value = {
                "classification": "Fake",
                "confidence": base_conf,
                "explanation": f"Unnatural pitch consistency in {final_language} speech.\nRobotic vocal patterns detected.\nDigital artifacts present in spectral analysis."
            }

        result = orchestrator.detect_voice(
            audio_base64=final_base64,
            language_hint=final_language,
            request_id=f"test-{label_hint}"
        )
        
        # Apply Routes Logic
        classification = "AI_GENERATED" if result["classification"].lower() == "fake" else "HUMAN"
        explanation_lines = result["explanation"].split('\n')
        final_explanation = '\n'.join(explanation_lines[:3])
        
        response_data = {
            "status": "success",
            "language": final_language,
            "classification": classification,
            "confidenceScore": round(result["confidence"], 4),
            "explanation": final_explanation
        }
        
        print(json.dumps(response_data, indent=2))
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manual API Test")
    parser.add_argument("--base64", type=str, help="Base64 string directly")
    parser.add_argument("--file", type=str, help="Path to text file containing Base64")
    parser.add_argument("--language", type=str, default="Tamil", help="Language hint")
    
    args = parser.parse_args()
    
    input_data = "DUMMY_DEFAUL_BASE64"
    if args.base64:
        input_data = args.base64.strip("'\"")
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                input_data = f.read().strip()
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Could not read file: {e}"}))
            sys.exit(1)
            
    run_test(input_data, language=args.language)
