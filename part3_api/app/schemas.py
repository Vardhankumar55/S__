from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator
from typing import Optional

class DetectRequest(BaseModel):
    # Accept both "audioBase64" (camelCase) and "audio_base_64" (snake_case)
    model_config = ConfigDict(populate_by_name=True)
    # This ensures we can use either the field name OR the alias for validation
    

    audioBase64: str = Field(
        ..., 
        validation_alias=AliasChoices("audioBase64", "audio_base_64"),
        description="The base64 encoded audio data.",
        example="SUQzBAAAAAAAI1..."
    )
    # Strict validation for Supported Languages
    language: str = Field(
        ..., 
        pattern="^(Tamil|English|Hindi|Malayalam|Telugu)$",
        description="The language of the audio (Tamil, English, Hindi, Malayalam, Telugu).Case-sensitive.",
        example="Tamil"
    )
    # Strict validation for Audio Format
    audioFormat: str = Field(
        "mp3",
        pattern="^mp3$",
        validation_alias=AliasChoices("audioFormat", "audio_format"),
        description="The format of the audio (Always 'mp3').",
        example="mp3"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ["Tamil", "English", "Hindi", "Malayalam", "Telugu"]:
             raise ValueError("Language must be one of: Tamil, English, Hindi, Malayalam, Telugu")
        return v

    @field_validator('audioFormat')
    @classmethod
    def validate_audio_format(cls, v: str) -> str:
        if v.lower() != "mp3":
            raise ValueError("audioFormat must be 'mp3'")
        return "mp3"

class DetectResponse(BaseModel):
    status: str = Field("success", description="Status of the request (success/error)")
    language: str = Field(..., description="Language of the analyzed audio")
    classification: str = Field(..., description="Prediction: 'Human' or 'AI_GENERATED'")
    confidenceScore: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    explanation: str = Field(..., description="Human-readable explanation (max 3 lines)")
